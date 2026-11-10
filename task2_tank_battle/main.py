"""CLI entry point for Task 2: Adversarial Search — Tank Battle Game."""
from __future__ import annotations

import argparse
import os
import sys

# Ensure task2_tank_battle is on sys.path when invoked from root or subfolder
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from tank_battle.agents.plugin_loader import PluginLoader
from tank_battle.core.maps import MAPS
from tank_battle.core.rules import TransitionEngine
from tank_battle.experiments.benchmark_runner import SearchBenchmark, TournamentRunner
from tank_battle.experiments.plotting import plot_search_benchmarks, plot_tournament_summary
from tank_battle.experiments.scenarios import BENCHMARK_SCENARIOS
from tank_battle.factory import FOUR_REQUIRED_CONFIGS, build_agent


def render_ascii_board(state) -> str:
    """Render an ASCII representation of the Tank Battle arena for terminal display."""
    grid = [[" ." for _ in range(state.width)] for _ in range(state.height)]
    for (r, c), hp in state.walls.items():
        grid[r][c] = f"W{hp}"
    for pid, base in state.bases.items():
        if base.is_alive:
            grid[base.row][base.col] = f"B{pid}"
        else:
            grid[base.row][base.col] = "XX"
    for b in state.bullets:
        if 0 <= b.row < state.height and 0 <= b.col < state.width:
            grid[b.row][b.col] = " *"
    for pid, tank in state.tanks.items():
        if tank.is_alive:
            grid[tank.row][tank.col] = f"T{pid}"
        else:
            grid[tank.row][tank.col] = "!!"

    lines = ["   " + " ".join(f"{c:2d}" for c in range(state.width))]
    for r in range(state.height):
        lines.append(f"{r:2d} " + " ".join(grid[r]))
    return "\n".join(lines)


def cmd_demo(args: argparse.Namespace) -> None:
    """Run a single head-to-head match in the terminal."""
    ext_dir = os.path.join(THIS_DIR, "external_agents")
    state = MAPS[args.map]()
    agent1 = build_agent(args.p1, depth=args.depth, external_dir=ext_dir)
    agent2 = build_agent(args.p2, depth=args.depth, external_dir=ext_dir)
    agent1.reset()
    agent2.reset()

    print("=" * 72)
    print(f"TANK BATTLE MATCH: P1 [{agent1.name}] vs P2 [{agent2.name}] on map '{args.map}'")
    print("=" * 72)

    while not state.is_terminal() and state.turn < args.max_turns:
        pid = state.current_player
        agent = agent1 if pid == 1 else agent2
        action = agent.get_action(state.clone())
        metrics = agent.last_metrics
        state = TransitionEngine.apply_action(state, action)

        if args.verbose or state.turn % 5 == 0 or state.is_terminal():
            m_info = (
                f"nodes={metrics.nodes_explored}, pruned={metrics.nodes_pruned}, "
                f"t={metrics.elapsed_s * 1000:.1f}ms, score={metrics.score:.1f}"
                if metrics
                else "external/instant"
            )
            print(
                f"[Turn {state.turn:02d}] P{pid} -> {action.value:<10} | "
                f"T1 HP={state.tanks[1].hp} B1 HP={state.bases[1].hp} | "
                f"T2 HP={state.tanks[2].hp} B2 HP={state.bases[2].hp} | ({m_info})"
            )

    print("\nFinal Arena State:")
    print(render_ascii_board(state))
    winner = state.get_winner()
    print("-" * 72)
    print(
        f"Match Finished at Turn {state.turn} | Terminal Winner: {winner} | "
        f"P1 (Tank={state.tanks[1].hp}, Base={state.bases[1].hp}) vs "
        f"P2 (Tank={state.tanks[2].hp}, Base={state.bases[2].hp})"
    )


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Run Requirement 2 4-way search benchmark across depths and scenarios."""
    out_dir = os.path.abspath(args.out)
    csv_path = os.path.join(out_dir, "search_benchmark.csv")

    print("=" * 76)
    print("RUNNING REQUIREMENT 2 SEARCH BENCHMARK (4 CONFIGURATIONS)")
    print(f"Scenarios: {args.scenarios} | Depths: {args.depths} | Trials: {args.trials}")
    print("=" * 76)

    runner = SearchBenchmark(
        scenarios=args.scenarios,
        depths=args.depths,
        trials=args.trials,
    )
    df = runner.run(output_csv=csv_path)
    plots = plot_search_benchmarks(df, out_dir)

    summary_cols = [
        "scenario",
        "config_name",
        "depth",
        "time_mean_ms",
        "nodes_explored",
        "nodes_pruned",
        "state_reduction_vs_minimax",
        "chosen_action",
        "score",
    ]
    print("\nBenchmark Results Summary:")
    print(df[summary_cols].to_string(index=False))
    print(f"\nSaved CSV: {csv_path}")
    for name, path in plots.items():
        print(f"Saved Plot [{name}]: {path}")


def cmd_tournament(args: argparse.Namespace) -> None:
    """Run head-to-head round-robin tournament across the 4 configurations (+ plugins)."""
    out_dir = os.path.abspath(args.out)
    ext_dir = os.path.join(THIS_DIR, "external_agents")

    specs = list(FOUR_REQUIRED_CONFIGS.keys())
    if args.include_plugins:
        discovered = PluginLoader.discover_directory(ext_dir)
        specs.extend(sorted(discovered.keys()))

    print("=" * 76)
    print("RUNNING HEAD-TO-HEAD TANK BATTLE TOURNAMENT")
    print(f"Agents: {specs} | Depth: {args.depth} | Maps: {args.maps}")
    print("=" * 76)

    runner = TournamentRunner(
        agent_specs=specs,
        depth=args.depth,
        map_keys=args.maps,
        max_turns=args.max_turns,
        external_dir=ext_dir,
    )
    matches_csv = os.path.join(out_dir, "tournament_matches.csv")
    summary_csv = os.path.join(out_dir, "tournament_summary.csv")
    matches_df, summary_df = runner.run_round_robin(
        output_matches_csv=matches_csv,
        output_summary_csv=summary_csv,
    )
    plot_path = plot_tournament_summary(summary_df, out_dir)

    print("\nTournament Standings:")
    print(summary_df.to_string(index=False))
    print(f"\nSaved Matches CSV: {matches_csv}")
    print(f"Saved Summary CSV: {summary_csv}")
    print(f"Saved Tournament Plot: {plot_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Task 2: Adversarial Search — Tank Battle Game CLI"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # demo
    p_demo = sub.add_parser("demo", help="Play a single match in the terminal")
    p_demo.add_argument("--p1", default="heuristic_alphabeta", help="Player 1 agent spec")
    p_demo.add_argument("--p2", default="alphabeta", help="Player 2 agent spec")
    p_demo.add_argument("--map", default="skirmish", choices=list(MAPS.keys()))
    p_demo.add_argument("--depth", type=int, default=3)
    p_demo.add_argument("--max-turns", type=int, default=60)
    p_demo.add_argument("--verbose", action="store_true")
    p_demo.set_defaults(func=cmd_demo)

    # benchmark
    p_bench = sub.add_parser("benchmark", help="Run R2 4-configuration search benchmark")
    p_bench.add_argument(
        "--scenarios",
        nargs="+",
        default=["endgame", "dodge", "skirmish", "standard"],
        choices=list(BENCHMARK_SCENARIOS.keys()),
    )
    p_bench.add_argument("--depths", nargs="+", type=int, default=[1, 2, 3, 4])
    p_bench.add_argument("--trials", type=int, default=3)
    p_bench.add_argument(
        "--out",
        default=os.path.join(THIS_DIR, "results"),
        help="Directory to save CSVs and PNG plots",
    )
    p_bench.set_defaults(func=cmd_benchmark)

    # tournament
    p_tour = sub.add_parser("tournament", help="Run round-robin tournament")
    p_tour.add_argument("--depth", type=int, default=3)
    p_tour.add_argument(
        "--maps",
        nargs="+",
        default=["skirmish", "standard"],
        choices=list(MAPS.keys()),
    )
    p_tour.add_argument("--max-turns", type=int, default=60)
    p_tour.add_argument(
        "--include-plugins",
        action="store_true",
        default=True,
        help="Include external student plugins from external_agents/",
    )
    p_tour.add_argument(
        "--out",
        default=os.path.join(THIS_DIR, "results"),
        help="Directory to save CSVs and PNG plots",
    )
    p_tour.set_defaults(func=cmd_tournament)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
