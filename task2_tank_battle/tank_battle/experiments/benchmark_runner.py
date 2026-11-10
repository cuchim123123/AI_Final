"""Benchmark & tournament runners for Requirement 2 experimental comparison."""
from __future__ import annotations

import os
import time
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from ..core.maps import MAPS
from ..core.rules import TransitionEngine
from ..factory import FOUR_REQUIRED_CONFIGS, build_agent, build_search_engine
from .scenarios import BENCHMARK_SCENARIOS


class SearchBenchmark:
    """Runs controlled, reproducible search benchmarks across the 4 configurations."""

    def __init__(
        self,
        scenarios: Sequence[str] = ("endgame", "dodge", "skirmish", "standard"),
        depths: Sequence[int] = (1, 2, 3, 4),
        trials: int = 3,
    ) -> None:
        self.scenarios = list(scenarios)
        self.depths = list(depths)
        self.trials = max(1, int(trials))

    def run(self, output_csv: Optional[str] = None) -> pd.DataFrame:
        """Execute the 4-configuration search benchmark across scenarios and depths."""
        rows: List[Dict[str, object]] = []

        for scen_key in self.scenarios:
            if scen_key not in BENCHMARK_SCENARIOS:
                continue
            scenario = BENCHMARK_SCENARIOS[scen_key]

            for depth in self.depths:
                # Store unpruned baseline node counts at this (scenario, depth)
                baseline_nodes: Dict[bool, int] = {}

                for cfg_key, cfg in FOUR_REQUIRED_CONFIGS.items():
                    times: List[float] = []
                    last_metrics = None

                    for _ in range(self.trials):
                        state = scenario.builder()
                        engine = build_search_engine(cfg_key, depth=depth)
                        last_metrics = engine.search(state)
                        times.append(last_metrics.elapsed_s)

                    assert last_metrics is not None
                    if not cfg.use_alpha_beta:
                        baseline_nodes[cfg.use_heuristic] = last_metrics.nodes_explored

                    unpruned = baseline_nodes.get(cfg.use_heuristic, last_metrics.nodes_explored)
                    reduction_ratio = (
                        max(0.0, 1.0 - (last_metrics.nodes_explored / unpruned))
                        if unpruned > 0 and cfg.use_alpha_beta
                        else 0.0
                    )

                    rows.append(
                        {
                            "scenario": scen_key,
                            "scenario_title": scenario.title,
                            "config_key": cfg_key,
                            "config_name": cfg.display_name,
                            "use_alpha_beta": cfg.use_alpha_beta,
                            "use_heuristic": cfg.use_heuristic,
                            "depth": depth,
                            "trials": self.trials,
                            "time_mean_s": float(np.mean(times)),
                            "time_std_s": float(np.std(times)),
                            "time_mean_ms": float(np.mean(times) * 1000.0),
                            "nodes_explored": last_metrics.nodes_explored,
                            "nodes_pruned": last_metrics.nodes_pruned,
                            "pruning_ratio": last_metrics.pruning_ratio,
                            "state_reduction_vs_minimax": reduction_ratio,
                            "tt_hits": last_metrics.tt_hits,
                            "chosen_action": last_metrics.chosen_action.value,
                            "score": last_metrics.score,
                        }
                    )

        df = pd.DataFrame(rows)
        if output_csv:
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            df.to_csv(output_csv, index=False)
        return df


class TournamentRunner:
    """Runs head-to-head matches between Tank Battle agents with side-swapping."""

    def __init__(
        self,
        agent_specs: Sequence[str] = (
            "minimax",
            "alphabeta",
            "heuristic_minimax",
            "heuristic_alphabeta",
        ),
        depth: int = 3,
        map_keys: Sequence[str] = ("skirmish", "standard"),
        max_turns: int = 80,
        external_dir: str = "external_agents",
    ) -> None:
        self.agent_specs = list(agent_specs)
        self.depth = depth
        self.map_keys = list(map_keys)
        self.max_turns = max_turns
        self.external_dir = external_dir

    def play_match(
        self,
        spec_p1: str,
        spec_p2: str,
        map_key: str,
    ) -> Dict[str, object]:
        """Play a single full game between spec_p1 (Player 1) and spec_p2 (Player 2)."""
        state = MAPS[map_key]()
        agent1 = build_agent(spec_p1, depth=self.depth, external_dir=self.external_dir)
        agent2 = build_agent(spec_p2, depth=self.depth, external_dir=self.external_dir)
        agent1.reset()
        agent2.reset()

        p1_times: List[float] = []
        p2_times: List[float] = []
        p1_nodes: List[int] = []
        p2_nodes: List[int] = []

        while not state.is_terminal() and state.turn < self.max_turns:
            current = state.current_player
            agent = agent1 if current == 1 else agent2

            t0 = time.perf_counter()
            action = agent.get_action(state.clone())
            dt = time.perf_counter() - t0

            if current == 1:
                p1_times.append(dt)
                if agent.last_metrics is not None:
                    p1_nodes.append(agent.last_metrics.nodes_explored)
            else:
                p2_times.append(dt)
                if agent.last_metrics is not None:
                    p2_nodes.append(agent.last_metrics.nodes_explored)

            state = TransitionEngine.apply_action(state, action)

        winner = state.get_winner()
        # If max_turns reached without terminal destruction, tie-break by HP sum
        tie_broken_winner = winner
        p1_hp = state.tanks[1].hp + state.bases[1].hp
        p2_hp = state.tanks[2].hp + state.bases[2].hp
        if winner is None:
            if p1_hp > p2_hp:
                tie_broken_winner = 1
            elif p2_hp > p1_hp:
                tie_broken_winner = 2
            else:
                tie_broken_winner = 0

        return {
            "map": map_key,
            "p1_spec": spec_p1,
            "p2_spec": spec_p2,
            "depth": self.depth,
            "terminal_winner": winner if winner is not None else 0,
            "effective_winner": tie_broken_winner,
            "turns": state.turn,
            "p1_tank_hp": state.tanks[1].hp,
            "p1_base_hp": state.bases[1].hp,
            "p2_tank_hp": state.tanks[2].hp,
            "p2_base_hp": state.bases[2].hp,
            "p1_mean_time_ms": float(np.mean(p1_times) * 1000.0) if p1_times else 0.0,
            "p2_mean_time_ms": float(np.mean(p2_times) * 1000.0) if p2_times else 0.0,
            "p1_mean_nodes": float(np.mean(p1_nodes)) if p1_nodes else 0.0,
            "p2_mean_nodes": float(np.mean(p2_nodes)) if p2_nodes else 0.0,
        }

    def run_round_robin(
        self,
        output_matches_csv: Optional[str] = None,
        output_summary_csv: Optional[str] = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Run a full double round-robin tournament across all agent specs and maps."""
        matches: List[Dict[str, object]] = []
        for map_key in self.map_keys:
            for i, spec_a in enumerate(self.agent_specs):
                for j, spec_b in enumerate(self.agent_specs):
                    if i == j:
                        continue
                    matches.append(self.play_match(spec_a, spec_b, map_key))

        matches_df = pd.DataFrame(matches)

        # Aggregate win/draw/loss summary per agent
        summary_rows: List[Dict[str, object]] = []
        for spec in self.agent_specs:
            games = 0
            wins = 0
            draws = 0
            losses = 0
            hp_diff_list: List[int] = []
            time_ms_list: List[float] = []
            nodes_list: List[float] = []

            for m in matches:
                if m["p1_spec"] == spec:
                    games += 1
                    w = m["effective_winner"]
                    if w == 1:
                        wins += 1
                    elif w == 0:
                        draws += 1
                    else:
                        losses += 1
                    hp_diff_list.append(
                        (int(m["p1_tank_hp"]) + int(m["p1_base_hp"]))
                        - (int(m["p2_tank_hp"]) + int(m["p2_base_hp"]))
                    )
                    time_ms_list.append(float(m["p1_mean_time_ms"]))
                    nodes_list.append(float(m["p1_mean_nodes"]))
                elif m["p2_spec"] == spec:
                    games += 1
                    w = m["effective_winner"]
                    if w == 2:
                        wins += 1
                    elif w == 0:
                        draws += 1
                    else:
                        losses += 1
                    hp_diff_list.append(
                        (int(m["p2_tank_hp"]) + int(m["p2_base_hp"]))
                        - (int(m["p1_tank_hp"]) + int(m["p1_base_hp"]))
                    )
                    time_ms_list.append(float(m["p2_mean_time_ms"]))
                    nodes_list.append(float(m["p2_mean_nodes"]))

            display = (
                FOUR_REQUIRED_CONFIGS[spec].display_name
                if spec in FOUR_REQUIRED_CONFIGS
                else spec
            )
            win_rate = (wins + 0.5 * draws) / games if games > 0 else 0.0
            summary_rows.append(
                {
                    "agent_spec": spec,
                    "display_name": display,
                    "games": games,
                    "wins": wins,
                    "draws": draws,
                    "losses": losses,
                    "win_rate_pct": round(win_rate * 100.0, 2),
                    "avg_hp_diff": round(float(np.mean(hp_diff_list)), 2) if hp_diff_list else 0.0,
                    "mean_move_time_ms": round(float(np.mean(time_ms_list)), 2) if time_ms_list else 0.0,
                    "mean_nodes_explored": round(float(np.mean(nodes_list)), 1) if nodes_list else 0.0,
                }
            )

        summary_df = pd.DataFrame(summary_rows).sort_values(
            by=["win_rate_pct", "avg_hp_diff"], ascending=False
        )

        if output_matches_csv:
            os.makedirs(os.path.dirname(output_matches_csv), exist_ok=True)
            matches_df.to_csv(output_matches_csv, index=False)
        if output_summary_csv:
            os.makedirs(os.path.dirname(output_summary_csv), exist_ok=True)
            summary_df.to_csv(output_summary_csv, index=False)

        return matches_df, summary_df
