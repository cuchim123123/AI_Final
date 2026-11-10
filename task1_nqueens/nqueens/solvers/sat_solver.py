"""SAT-based solver using PySAT Glucose3."""
from __future__ import annotations

import threading
import time
from typing import Optional

from pysat.solvers import Glucose3

from ..amo import AtMostOneEncoder
from ..board import Board
from ..cnf import CNFEncoder
from ..result import SolveResult
from .base import Solver


class SATSolver(Solver):
    """Encodes N-Queens to CNF and solves it with Glucose3.

    The AMO encoding is injected (Dependency Injection): the default
    (`None` -> pairwise) is the baseline; pass `SequentialCounterAMO()` for
    the optimised encoding.

    Args:
        amo: at-most-one encoding strategy.
        column_alo: also add the (redundant) at-least-one-per-column clauses.
        time_limit_s: if set, abort the SAT search after this many seconds and
            report `solved=False` with `extra["timed_out"] = True`. `None`
            (default) means no limit.
    """

    def __init__(self, amo: Optional[AtMostOneEncoder] = None,
                 column_alo: bool = False,
                 time_limit_s: Optional[float] = None) -> None:
        self.amo = amo
        self.column_alo = column_alo
        self.time_limit_s = time_limit_s

    def solve(self, n: int,
              cancel_event: Optional[threading.Event] = None) -> SolveResult:
        # Clause construction is measured separately from the solver run.
        t0 = time.perf_counter()
        encoder = CNFEncoder(n, self.amo, self.column_alo)
        clauses = encoder.encode()
        build_time = time.perf_counter() - t0

        if cancel_event and cancel_event.is_set():
            return SolveResult(
                n=n, solved=False, time_s=0.0, board=None, num_clauses=len(clauses),
                extra={"variables": encoder.num_vars, "build_time_s": build_time,
                       "timed_out": False, "cancelled": True})

        with Glucose3(bootstrap_with=clauses) as g:
            t1 = time.perf_counter()
            sat, timed_out, cancelled = self._run(g, cancel_event)  # only solver run is timed
            solve_time = time.perf_counter() - t1
            model = g.get_model() if sat else None

        # `from_model` ignores auxiliary variables (ids > N^2).
        board = Board.from_model(model, n) if model else None
        return SolveResult(
            n=n, solved=bool(sat and board and board.is_valid() and not cancelled),
            time_s=solve_time, board=board, num_clauses=len(clauses),
            extra={"variables": encoder.num_vars, "build_time_s": build_time,
                   "timed_out": timed_out, "cancelled": cancelled})

    def _run(self, g: Glucose3, cancel_event: Optional[threading.Event] = None):
        """Run the solver; returns (satisfiable_or_None, timed_out, cancelled)."""
        if self.time_limit_s is None and cancel_event is None:
            return g.solve(), False, False

        timed_out = False
        cancelled = False
        stop_monitor = threading.Event()

        def _monitor():
            nonlocal timed_out, cancelled
            start_t = time.perf_counter()
            while not stop_monitor.wait(0.05):
                if cancel_event and cancel_event.is_set():
                    cancelled = True
                    g.interrupt()
                    break
                if self.time_limit_s is not None and (time.perf_counter() - start_t) >= self.time_limit_s:
                    timed_out = True
                    g.interrupt()
                    break

        monitor_thread = threading.Thread(target=_monitor, daemon=True)
        monitor_thread.start()
        try:
            result = g.solve_limited(expect_interrupt=True)  # None if interrupted
        finally:
            stop_monitor.set()
            monitor_thread.join(timeout=1.0)

        return result, timed_out, cancelled
