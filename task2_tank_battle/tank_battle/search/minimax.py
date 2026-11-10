"""Adversarial Search Engine: Minimax, Alpha-Beta Pruning, and Heuristic Search."""
from __future__ import annotations

import math
import time
from typing import List, Optional, Tuple

from ..core.rules import TransitionEngine
from ..core.state import GameState
from ..core.types import Action, SearchMetrics
from .evaluators import StateEvaluator
from .move_ordering import MoveOrderer
from .transposition import BoundFlag, TranspositionTable


class SearchTimeout(Exception):
    """Raised internally when an iterative-deepening time budget expires."""


class AdversarialSearchEngine:
    """Configurable Zero-Sum Game Tree Search Engine (Lecture 07).

    Supports all 4 required assignment configurations:
    1. Minimax Search               (use_alpha_beta=False, evaluator=BasicEvaluator)
    2. Alpha-Beta Search            (use_alpha_beta=True,  evaluator=BasicEvaluator)
    3. Heuristic Minimax Search     (use_alpha_beta=False, evaluator=TacticalHeuristicEvaluator)
    4. Heuristic Alpha-Beta Search  (use_alpha_beta=True,  evaluator=TacticalHeuristicEvaluator)

    Plus optional real-time optimizations:
    - Tactical Move Ordering (`use_move_ordering`)
    - Transposition Table caching (`use_transposition_table`)
    - Iterative Deepening with time budget (`use_iterative_deepening`, `time_limit_s`)
    """

    def __init__(
        self,
        name: str,
        evaluator: StateEvaluator,
        max_depth: int = 3,
        use_alpha_beta: bool = True,
        use_move_ordering: bool = False,
        use_transposition_table: bool = False,
        use_iterative_deepening: bool = False,
        time_limit_s: Optional[float] = None,
    ) -> None:
        self.name = name
        self.evaluator = evaluator
        self.max_depth = max_depth
        self.use_alpha_beta = use_alpha_beta
        self.use_move_ordering = use_move_ordering
        self.use_transposition_table = use_transposition_table
        self.use_iterative_deepening = use_iterative_deepening
        self.time_limit_s = time_limit_s
        self.tt = TranspositionTable()
        self.position_history: dict[tuple, int] = {}

        # Per-search counters
        self._nodes_explored: int = 0
        self._nodes_pruned: int = 0
        self._deadline: Optional[float] = None

    @staticmethod
    def progress_key(state: GameState, player_id: int) -> tuple:
        """Fingerprint of tank position and global material/wall HP state."""
        t = state.tanks[player_id]
        wall_sum = sum(state.walls.values())
        hp_sig = (
            state.tanks[1].hp,
            state.tanks[2].hp,
            state.bases[1].hp,
            state.bases[2].hp,
            wall_sum,
        )
        return (t.row, t.col, hp_sig)

    def _root_action_adjustment(
        self, state: GameState, action: Action, child: GameState
    ) -> float:
        """Signed root utility adjustment (from MAX's perspective) to prevent loops/wall-stalls."""
        if not self.position_history:
            return 0.0

        player = state.current_player
        sign = 1.0 if player == 1 else -1.0
        penalty = 0.0

        # 1. Penalize bumping into a blocked wall/border cell that fails to move the tank
        if action.direction is not None and child.tanks[player].pos == state.tanks[player].pos:
            penalty += 18.0

        # 2. Penalize repeating a (tank_pos, material_hp_signature) state when no progress occurred
        key = self.progress_key(child, player)
        repeats = self.position_history.get(key, 0)
        if repeats >= 1:
            penalty += 38.0 * repeats

        return -sign * penalty

    def search(self, state: GameState) -> SearchMetrics:
        """Execute adversarial search from `state` and return chosen action + telemetry."""
        t0 = time.perf_counter()
        self._nodes_explored = 0
        self._nodes_pruned = 0
        self.tt.clear()
        self._deadline = (t0 + self.time_limit_s) if self.time_limit_s is not None else None

        maximizing = state.current_player == 1
        best_action = Action.STAY
        best_score = -math.inf if maximizing else math.inf
        depth_reached = 0

        if self.use_iterative_deepening and self.max_depth > 1:
            for d in range(1, self.max_depth + 1):
                try:
                    score, action = self._search_root(state, depth=d, maximizing=maximizing, pv_move=best_action)
                    best_score = score
                    best_action = action
                    depth_reached = d
                except SearchTimeout:
                    break
        else:
            try:
                best_score, best_action = self._search_root(
                    state, depth=self.max_depth, maximizing=maximizing, pv_move=None
                )
                depth_reached = self.max_depth
            except SearchTimeout:
                depth_reached = max(1, depth_reached)

        elapsed = time.perf_counter() - t0
        return SearchMetrics(
            algorithm=self.name,
            chosen_action=best_action,
            score=best_score,
            depth_reached=depth_reached,
            nodes_explored=self._nodes_explored,
            nodes_pruned=self._nodes_pruned,
            tt_hits=self.tt.hits,
            time_s=elapsed,
        )

    def _search_root(
        self,
        state: GameState,
        depth: int,
        maximizing: bool,
        pv_move: Optional[Action] = None,
    ) -> Tuple[float, Action]:
        actions = self._get_ordered_actions(state, pv_move)
        best_action = actions[0]
        alpha = -math.inf
        beta = math.inf

        if maximizing:
            best_val = -math.inf
            for idx, act in enumerate(actions):
                child = TransitionEngine.apply_action(state, act)
                adj = self._root_action_adjustment(state, act, child)
                raw_val = self._minimax(child, depth - 1, alpha - adj, beta - adj, maximizing=False)
                val = raw_val + adj
                if val > best_val:
                    best_val = val
                    best_action = act
                if self.use_alpha_beta:
                    alpha = max(alpha, best_val)
                    if alpha >= beta:
                        self._nodes_pruned += len(actions) - idx - 1
                        break
            return best_val, best_action
        else:
            best_val = math.inf
            for idx, act in enumerate(actions):
                child = TransitionEngine.apply_action(state, act)
                adj = self._root_action_adjustment(state, act, child)
                raw_val = self._minimax(child, depth - 1, alpha - adj, beta - adj, maximizing=True)
                val = raw_val + adj
                if val < best_val:
                    best_val = val
                    best_action = act
                if self.use_alpha_beta:
                    beta = min(beta, best_val)
                    if alpha >= beta:
                        self._nodes_pruned += len(actions) - idx - 1
                        break
            return best_val, best_action

    def _minimax(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
    ) -> float:
        self._nodes_explored += 1
        if self._deadline is not None and (self._nodes_explored & 63) == 0:
            if time.perf_counter() >= self._deadline:
                raise SearchTimeout()

        # Terminal or depth-cutoff check
        if depth <= 0 or state.is_terminal():
            return self.evaluator.evaluate(state)

        alpha_orig = alpha
        beta_orig = beta
        tt_move: Optional[Action] = None
        state_key: Optional[tuple] = None

        # Transposition Table Lookup
        if self.use_transposition_table and self.use_alpha_beta:
            state_key = state.state_key()
            entry = self.tt.lookup(state_key)
            if entry is not None:
                tt_move = entry.best_action
                if entry.depth >= depth:
                    if entry.flag == BoundFlag.EXACT:
                        return entry.value
                    elif entry.flag == BoundFlag.LOWERBOUND:
                        alpha = max(alpha, entry.value)
                    elif entry.flag == BoundFlag.UPPERBOUND:
                        beta = min(beta, entry.value)
                    if alpha >= beta:
                        return entry.value

        actions = self._get_ordered_actions(state, tt_move)
        best_action: Optional[Action] = actions[0]

        if maximizing:
            best_val = -math.inf
            for idx, act in enumerate(actions):
                child = TransitionEngine.apply_action(state, act)
                val = self._minimax(child, depth - 1, alpha, beta, maximizing=False)
                if val > best_val:
                    best_val = val
                    best_action = act
                if self.use_alpha_beta:
                    alpha = max(alpha, best_val)
                    if alpha >= beta:
                        self._nodes_pruned += len(actions) - idx - 1
                        break
        else:
            best_val = math.inf
            for idx, act in enumerate(actions):
                child = TransitionEngine.apply_action(state, act)
                val = self._minimax(child, depth - 1, alpha, beta, maximizing=True)
                if val < best_val:
                    best_val = val
                    best_action = act
                if self.use_alpha_beta:
                    beta = min(beta, best_val)
                    if alpha >= beta:
                        self._nodes_pruned += len(actions) - idx - 1
                        break

        # Store in Transposition Table
        if self.use_transposition_table and self.use_alpha_beta and state_key is not None:
            if best_val <= alpha_orig:
                flag = BoundFlag.UPPERBOUND
            elif best_val >= beta_orig:
                flag = BoundFlag.LOWERBOUND
            else:
                flag = BoundFlag.EXACT
            self.tt.store(state_key, depth, flag, best_val, best_action)

        return best_val

    def _get_ordered_actions(
        self, state: GameState, tt_best_action: Optional[Action] = None
    ) -> List[Action]:
        actions = list(TransitionEngine.ALL_ACTIONS)
        if self.use_move_ordering:
            return MoveOrderer.order_actions(state, actions, tt_best_action=tt_best_action)
        return actions
