"""Min-Conflicts local search (one queen per column)."""
from __future__ import annotations

import random
import threading
import time
from typing import Callable, List, Optional, Tuple

from ..board import Board
from ..result import SolveResult
from .base import Solver
from .conflict_tracker import ConflictTracker
from .initializers import Initializer, RandomInitializer
from .selectors import RandomSelector, VariableSelector


class MinConflictsSolver(Solver):
    """Min-Conflicts with injectable selection, initialisation and restarts.

    With the defaults it is the plain Lecture 08 algorithm (the baseline):
    random start, random conflicted variable, one attempt, no restarts.

    Args:
        selector: strategy choosing which conflicted column to repair.
        initializer: strategy producing the start state of each attempt.
        max_steps_factor: total step budget is `max_steps_factor * N`.
        restart_steps_factor: if set, an attempt is abandoned after
            `restart_steps_factor * N` steps and a fresh one is started from a
            new initial state, until the *total* budget is used up. `None`
            means a single attempt (no restarts). Keeping the total budget
            fixed makes restart / no-restart runs directly comparable.
        seed: seed of the solver's private RNG (reproducible runs).
    """

    def __init__(self, selector: Optional[VariableSelector] = None,
                 initializer: Optional[Initializer] = None,
                 max_steps_factor: int = 100,
                 restart_steps_factor: Optional[int] = None,
                 seed: Optional[int] = None) -> None:
        self.selector = selector or RandomSelector()
        self.initializer = initializer or RandomInitializer()
        self.max_steps_factor = max_steps_factor
        self.restart_steps_factor = restart_steps_factor
        self.seed = seed

    def solve(self, n: int,
              step_callback: Optional[Callable[[dict], None]] = None,
              cancel_event: Optional[threading.Event] = None) -> SolveResult:
        rng = random.Random(self.seed)
        budget = self.max_steps_factor * n
        attempt_limit = (budget if self.restart_steps_factor is None
                         else self.restart_steps_factor * n)

        t0 = time.perf_counter()
        steps = 0
        restarts = 0
        solved = False
        cancelled = False
        tracker: Optional[ConflictTracker] = None

        while True:
            if cancel_event and cancel_event.is_set():
                cancelled = True
                break
            tracker = ConflictTracker.from_rows(self.initializer.build(n, rng))
            if step_callback:
                conflicts = tracker.conflict_vector()
                step_callback({
                    "step": steps,
                    "col": -1,
                    "row": -1,
                    "rows": list(tracker.rows),
                    "conflicts": conflicts,
                    "total_conflicts": sum(conflicts) // 2,
                    "restarts": restarts,
                    "solved": not any(conflicts),
                })
            solved, used, cancelled = self._attempt(
                tracker, min(attempt_limit, budget - steps), rng,
                step_callback=step_callback, cancel_event=cancel_event,
                step_offset=steps, restarts=restarts
            )
            steps += used
            if solved or steps >= budget or cancelled:
                break
            restarts += 1                       # abandon this state, start afresh
        elapsed = time.perf_counter() - t0

        board = Board.from_columns(tracker.rows) if (tracker and tracker.rows) else None
        return SolveResult(
            n=n, solved=bool(solved and board and board.is_valid() and not cancelled),
            time_s=elapsed, board=board, steps=steps,
            extra={"selector": self.selector.name,
                   "initializer": self.initializer.name,
                   "restarts": restarts,
                   "cancelled": cancelled})

    def _attempt(self, tracker: ConflictTracker, step_limit: int,
                 rng: random.Random,
                 step_callback: Optional[Callable[[dict], None]] = None,
                 cancel_event: Optional[threading.Event] = None,
                 step_offset: int = 0,
                 restarts: int = 0) -> Tuple[bool, int, bool]:
        """One Min-Conflicts run from the tracker's state.

        Returns (solved, steps_used, cancelled). Stops as soon as there is no conflict,
        `step_limit` repair steps have been made, or cancellation is triggered.
        """
        n = tracker.n
        steps = 0
        while True:
            if cancel_event and cancel_event.is_set():
                return False, steps, True
            conflicts = tracker.conflict_vector()
            conflicted: List[int] = [c for c in range(n) if conflicts[c] > 0]
            if not conflicted:
                return True, steps, False
            if steps >= step_limit:
                return False, steps, False
            # 1. choose the variable (column) to repair ...
            col = self.selector.select(conflicted, conflicts, rng)
            # 2. ... and move its queen to a minimum-conflict row (random ties).
            scores = [tracker.conflicts_at(col, r) for r in range(n)]
            best = min(scores)
            new_row = rng.choice([r for r in range(n) if scores[r] == best])
            tracker.move(col, new_row)
            steps += 1
            if step_callback:
                new_conflicts = tracker.conflict_vector()
                step_callback({
                    "step": step_offset + steps,
                    "col": col,
                    "row": new_row,
                    "rows": list(tracker.rows),
                    "conflicts": new_conflicts,
                    "total_conflicts": sum(new_conflicts) // 2,
                    "restarts": restarts,
                    "solved": not any(new_conflicts),
                })
