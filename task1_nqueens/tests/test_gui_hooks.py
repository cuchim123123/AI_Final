"""Tests for GUI hooks (callbacks, cancellation, figure generation)."""
import threading
import pandas as pd
import pytest

from nqueens.factory import MinConflictsConfig, build_min_conflicts, build_sat
from nqueens.experiments import SATExperiment, Plotter
from nqueens.experiments.variants import sat_variants


def test_min_conflicts_step_callback():
    steps_received = []

    def on_step(info: dict):
        steps_received.append(info)

    solver = build_min_conflicts(MinConflictsConfig(selector="random"), seed=42)
    res = solver.solve(8, step_callback=on_step)
    assert res.solved
    assert len(steps_received) > 0
    first = steps_received[0]
    assert "step" in first and "rows" in first and "total_conflicts" in first
    last = steps_received[-1]
    assert last["solved"] is True and last["total_conflicts"] == 0


def test_min_conflicts_cancellation():
    cancel_evt = threading.Event()
    cancel_evt.set()  # cancelled right away
    solver = build_min_conflicts(MinConflictsConfig(selector="random", max_steps_factor=1000), seed=42)
    res = solver.solve(100, cancel_event=cancel_evt)
    assert not res.solved
    assert res.extra["cancelled"] is True


def test_sat_cancellation():
    cancel_evt = threading.Event()
    cancel_evt.set()
    solver = build_sat("sequential", time_limit_s=10.0)
    res = solver.solve(64, cancel_event=cancel_evt)
    assert not res.solved
    assert res.extra["cancelled"] is True


def test_sat_experiment_progress_and_cancel():
    progress = []

    def on_progress(done, total, msg):
        progress.append((done, total, msg))

    cancel_evt = threading.Event()
    exp = SATExperiment(sat_variants(["pairwise"]), ns=[4, 5], repeats=1)
    df = exp.run(verbose=False, progress_callback=on_progress, cancel_event=cancel_evt)
    assert len(df) == 2
    assert len(progress) > 0

    # Test cancel
    cancel_evt.set()
    df_cancelled = exp.run(verbose=False, progress_callback=on_progress, cancel_event=cancel_evt)
    assert len(df_cancelled) == 0


def test_plotter_create_figures():
    plotter = Plotter()
    sat_df = pd.DataFrame([
        {"encoding": "pairwise", "N": 4, "clauses": 80, "solve_time_mean_s": 0.001, "solve_time_std_s": 0.0},
        {"encoding": "pairwise", "N": 8, "clauses": 736, "solve_time_mean_s": 0.002, "solve_time_std_s": 0.0},
    ])
    figs = plotter.create_sat_figures(sat_df)
    assert len(figs) == 2
    for name, fig in figs:
        assert fig is not None

    summary_df = pd.DataFrame([
        {"N": 8, "variant": "random", "steps_all_mean": 40.0, "time_all_mean_s": 0.001, "success_rate": 1.0},
    ])
    cmp_figs = plotter.create_compare_figures(summary_df)
    assert len(cmp_figs) == 3
