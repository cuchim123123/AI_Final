"""Background worker threads for solving, animation, and experiments."""
from __future__ import annotations

import threading
import time
from typing import Optional

import pandas as pd
from PySide6.QtCore import QObject, QThread, Signal

from nqueens.experiments import MinConflictsExperiment, SATExperiment
from nqueens.experiments.variants import (
    optimization_variants,
    sat_variants,
    selector_variants,
)
from nqueens.factory import MinConflictsConfig, build_min_conflicts, build_sat
from nqueens.result import SolveResult
from nqueens.solvers import SELECTORS


class SolveWorker(QThread):
    """Background worker for a single SAT or Min-Conflicts solve."""

    solved = Signal(object)      # SolveResult
    error = Signal(str)

    def __init__(self, mode: str, n: int, params: dict, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.mode = mode
        self.n = n
        self.params = params
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            if self.mode == "sat":
                solver = build_sat(
                    encoding=self.params.get("encoding", "pairwise"),
                    column_alo=self.params.get("column_alo", False),
                    time_limit_s=self.params.get("time_limit_s", 60.0),
                )
                res = solver.solve(self.n, cancel_event=self.cancel_event)
            else:
                cfg = MinConflictsConfig(
                    selector=self.params.get("selector", "random"),
                    initializer=self.params.get("initializer", "random"),
                    max_steps_factor=self.params.get("max_steps_factor", 100),
                    restart_steps_factor=self.params.get("restart_steps_factor", None),
                )
                solver = build_min_conflicts(cfg, seed=self.params.get("seed", None))
                res = solver.solve(self.n, cancel_event=self.cancel_event)
            self.solved.emit(res)
        except Exception as e:
            self.error.emit(str(e))


class VisualizerWorker(QThread):
    """Worker driving step-by-step Min-Conflicts animation."""

    step_occurred = Signal(dict)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, n: int, config: MinConflictsConfig, seed: Optional[int] = None,
                 delay_ms: int = 50, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.n = n
        self.config = config
        self.seed = seed
        self.delay_ms = delay_ms

        self.cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # running by default
        self._single_step = threading.Event()

    def set_delay(self, ms: int) -> None:
        self.delay_ms = max(1, ms)

    def pause(self) -> None:
        self._pause_event.clear()

    def resume(self) -> None:
        self._pause_event.set()

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def step_once(self) -> None:
        """Advance exactly one step while paused."""
        self._single_step.set()

    def cancel(self) -> None:
        self.cancel_event.set()
        self._pause_event.set()
        self._single_step.set()

    def run(self) -> None:
        try:
            solver = build_min_conflicts(self.config, seed=self.seed)

            def _on_step(info: dict):
                self.step_occurred.emit(info)
                # Check for pause / single-step
                while not self.cancel_event.is_set():
                    if self._pause_event.is_set():
                        # Running normally
                        time.sleep(self.delay_ms / 1000.0)
                        break
                    elif self._single_step.is_set():
                        # User clicked "Step" while paused
                        self._single_step.clear()
                        break
                    else:
                        # Paused: sleep briefly and poll
                        time.sleep(0.04)

            res = solver.solve(self.n, step_callback=_on_step, cancel_event=self.cancel_event)
            self.finished.emit(res)
        except Exception as e:
            self.failed.emit(str(e))


class ExperimentWorker(QThread):
    """Runs batch experiments in the background."""

    progress = Signal(int, int, str)
    finished = Signal(object, object, object)  # (raw_df, summary_df, cmp_df)
    failed = Signal(str)

    def __init__(self, exp_type: str, params: dict, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.exp_type = exp_type
        self.params = params
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            raw_df = pd.DataFrame()
            summary_df = pd.DataFrame()
            cmp_df = pd.DataFrame()

            def _on_progress(done, total, msg):
                self.progress.emit(done, total, msg)

            if self.exp_type == "sat":
                encodings = self.params.get("encodings", ["pairwise"])
                ns = self.params.get("ns", None)
                repeats = self.params.get("repeats", 5)
                time_limit = self.params.get("time_limit", 30.0)
                column_alo = self.params.get("column_alo", False)

                exp = SATExperiment(
                    sat_variants(encodings, column_alo, time_limit),
                    ns=ns, repeats=repeats
                )
                raw_df = exp.run(verbose=False, progress_callback=_on_progress,
                                 cancel_event=self.cancel_event)
                summary_df = raw_df

            elif self.exp_type == "minconf":
                selectors = self.params.get("selectors", list(SELECTORS))
                ns = self.params.get("ns", None)
                runs = self.params.get("runs", 30)
                cfg = MinConflictsConfig(
                    initializer=self.params.get("init", "random"),
                    max_steps_factor=self.params.get("max_steps_factor", 100),
                    restart_steps_factor=self.params.get("restart_steps_factor", None)
                )
                exp = MinConflictsExperiment(
                    selector_variants(selectors, cfg),
                    ns=ns, runs=runs
                )
                raw_df = exp.run(verbose=False, progress_callback=_on_progress,
                                 cancel_event=self.cancel_event)
                summary_df = exp.summarize(raw_df)

            elif self.exp_type == "optimize":
                selectors = self.params.get("selectors", ["random", "max"])
                ns = self.params.get("ns", None)
                runs = self.params.get("runs", 30)
                max_steps_factor = self.params.get("max_steps_factor", 100)
                restart_factor = self.params.get("restart_factor", 10)

                variants, baseline_of = optimization_variants(
                    selectors, max_steps_factor, restart_factor
                )
                exp = MinConflictsExperiment(variants, ns=ns, runs=runs)
                raw_df = exp.run(verbose=False, progress_callback=_on_progress,
                                 cancel_event=self.cancel_event)
                summary_df = exp.summarize(raw_df)
                cmp_df = exp.compare_to_baseline(summary_df, baseline_of)

            self.finished.emit(raw_df, summary_df, cmp_df)
        except Exception as e:
            self.failed.emit(str(e))
