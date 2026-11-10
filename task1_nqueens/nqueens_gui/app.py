"""Main window and application shell for PySide6 N-Queens GUI."""
from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
)

from .styles import DARK_THEME, LIGHT_THEME
from .views.experiment_view import ExperimentView
from .views.results_view import ResultsView
from .views.solve_view import SolveView
from .views.visualizer_view import VisualizerView


class MainWindow(QMainWindow):
    """Main window hosting the four interactive views."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("N-Queens Solver & Interactive Visualizer (PySAT & Min-Conflicts)")
        self.resize(1150, 780)
        self.setMinimumSize(950, 650)

        self._init_menu()
        self._init_tabs()
        self._init_status_bar()

    def _init_menu(self) -> None:
        menubar = self.menuBar()

        # View / Theme Menu
        view_menu = menubar.addMenu("&View")
        theme_menu = view_menu.addMenu("&Theme")

        theme_group = QActionGroup(self)
        self.act_dark = QAction("🌙 Dark Theme", self, checkable=True)
        self.act_light = QAction("☀️ Light Theme", self, checkable=True)
        self.act_dark.setChecked(True)

        theme_group.addAction(self.act_dark)
        theme_group.addAction(self.act_light)
        theme_menu.addAction(self.act_dark)
        theme_menu.addAction(self.act_light)

        self.act_dark.triggered.connect(lambda: self._set_theme(DARK_THEME))
        self.act_light.triggered.connect(lambda: self._set_theme(LIGHT_THEME))

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        act_formulation = QAction("Propositional Formulation (R1)", self)
        act_formulation.triggered.connect(self._show_formulation_dialog)
        help_menu.addAction(act_formulation)

        act_about = QAction("&About N-Queens Solver", self)
        act_about.triggered.connect(self._show_about_dialog)
        help_menu.addAction(act_about)

    def _set_theme(self, theme_stylesheet: str) -> None:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme_stylesheet)

    def _init_tabs(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.solve_view = SolveView(self)
        self.visualizer_view = VisualizerView(self)
        self.experiment_view = ExperimentView(self)
        self.results_view = ResultsView(self)

        self.tabs.addTab(self.solve_view, "🎯 Solve & Inspect")
        self.tabs.addTab(self.visualizer_view, "🎬 Local Search Visualizer")
        self.tabs.addTab(self.experiment_view, "📊 Experiment Runner")
        self.tabs.addTab(self.results_view, "📂 Results Browser")

        self.setCentralWidget(self.tabs)

    def _init_status_bar(self) -> None:
        status = QStatusBar()
        status.showMessage("Engine: PySAT (Glucose3) & Min-Conflicts  |  Python 3.11  |  Ready")
        self.setStatusBar(status)

    def _show_formulation_dialog(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("R1: Propositional Logic Formulation")
        dlg.resize(620, 500)
        vbox = QVBoxLayout(dlg)

        browser = QTextBrowser()
        formulation_text = """
        <div style="font-family: sans-serif; line-height: 1.5; color: #E6EDF3;">
        <h3 style="color: #58A6FF;">Propositional Logic Formulation (Requirement 1)</h3>
        <p><b>Variables:</b> <i>X(r, c)</i> is True iff square <i>(r, c)</i> contains a queen.<br>
        DIMACS ID: <code>r * N + c + 1</code> (total <i>N²</i> variables).</p>
        
        <p><b>Constraints:</b>
        <ul>
            <li><b>At least one queen per row (ALO):</b> (X(r,0) ∨ ... ∨ X(r, N-1))</li>
            <li><b>At most one queen per line (AMO):</b> For every pair of attacking squares on rows, columns, and diagonals: (¬A ∨ ¬B).</li>
        </ul>
        </p>

        <p><b>Constraint Discovery:</b><br>
        Buckets squares in O(N²) by <code>row: r</code>, <code>col: c</code>, <code>diag: r - c</code>, <code>anti-diag: r + c</code>. 
        Each bucket with ≥ 2 squares forms an attacking line.</p>

        <p><b>CNF Conversion:</b><br>
        - ALO rows are naturally in CNF (disjunction of literals).<br>
        - AMO pairwise constraints are converted via De Morgan: ¬(A ∧ B) ≡ (¬A ∨ ¬B).<br>
        - Closed-form pairwise clause count: <b>N + 2·N·C(N,2) + 4·C(N,3) + 2·C(N,2)</b> = Θ(N³).<br>
        - Sequential counter AMO replaces pairwise clauses with auxiliary variables s_i yielding Θ(N²) clauses.
        </p>
        </div>
        """
        browser.setHtml(formulation_text)
        vbox.addWidget(browser)
        dlg.exec()

    def _show_about_dialog(self) -> None:
        QMessageBox.about(
            self, "About N-Queens Solver",
            "<h3>N-Queens Propositional Logic & Local Search</h3>"
            "<p>Implements SAT Glucose3 with Pairwise and Sequential Counter encodings, "
            "and Min-Conflicts local search with Random, Max-Conflict, and Weighted-Conflict heuristics, "
            "random restarts, and greedy initialization.</p>"
            "<p>Built using PySide6 (Qt) and Object-Oriented Software Engineering principles.</p>"
        )


def create_app() -> QApplication:
    """Create and configure the Qt Application."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    return app
