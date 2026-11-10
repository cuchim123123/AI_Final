"""Headless tests for the PySide6 Graphical User Interface."""
import os
import sys
import pytest

# Ensure offscreen rendering for headless CI / testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from nqueens_gui.app import MainWindow, create_app
from nqueens_gui.widgets.board_view import BoardView
from nqueens_gui.widgets.stat_card import StatCard
from nqueens_gui.widgets.chart_widget import LiveConflictPlot, MatplotlibCanvas
from nqueens_gui.workers import SolveWorker, VisualizerWorker
from nqueens.factory import MinConflictsConfig


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    yield app


def test_board_view_headless(qapp):
    bv = BoardView()
    bv.set_board(8, [(0, 1), (1, 3), (2, 0), (3, 2), (4, 4), (5, 6), (6, 7), (7, 5)])
    assert bv.n == 8
    assert len(bv.queens) == 8
    # Test setting rows
    bv.set_board(4, [1, 3, 0, 2])
    assert len(bv.queens) == 4
    bv.clear()
    assert len(bv.queens) == 0


def test_stat_card_headless(qapp):
    card = StatCard("Test Metric", "123", "subtext")
    assert card.val_label.text() == "123"
    card.set_value("456", "new subtext", "#198754")
    assert card.val_label.text() == "456"
    assert card.sub_label.text() == "new subtext"


def test_chart_widgets_headless(qapp):
    plot = LiveConflictPlot()
    plot.add_point(1, 10)
    plot.add_point(2, 5)
    plot.add_point(3, 0)
    assert len(plot.steps) == 3
    plot.reset()
    assert len(plot.steps) == 0

    canvas = MatplotlibCanvas()
    assert canvas.figure is not None


def test_main_window_headless(qapp):
    win = MainWindow()
    assert win.tabs.count() == 4
    # Check that all views are loaded
    assert win.solve_view is not None
    assert win.visualizer_view is not None
    assert win.experiment_view is not None
    assert win.results_view is not None
    win.close()


def test_solve_worker_headless(qapp):
    results = []
    worker = SolveWorker("minconf", 8, {"selector": "random", "seed": 42})
    worker.solved.connect(lambda r: results.append(r))
    worker.start()
    worker.wait(5000)
    qapp.processEvents()
    assert len(results) == 1
    assert results[0].solved is True


def test_visualizer_worker_headless(qapp):
    steps = []
    cfg = MinConflictsConfig(selector="random", max_steps_factor=100)
    worker = VisualizerWorker(8, cfg, seed=42, delay_ms=1)
    worker.step_occurred.connect(lambda s: steps.append(s))
    worker.start()
    worker.wait(5000)
    qapp.processEvents()
    assert len(steps) > 0

