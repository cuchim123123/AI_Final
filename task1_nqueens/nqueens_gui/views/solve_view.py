"""Tab 1: Single Run Solver & Interactive Board View."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nqueens.amo import AMO_ENCODERS
from nqueens.board import Board
from nqueens.result import SolveResult
from nqueens.solvers import INITIALIZERS, SELECTORS
from ..widgets.board_view import BoardView
from ..widgets.stat_card import StatCard
from ..workers import SolveWorker


class SolveView(QWidget):
    """View allowing the user to configure and solve an individual N-Queens instance."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.worker: SolveWorker | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        splitter = QSplitter(Qt.Horizontal)

        # -------------------- LEFT PANEL: CONTROLS --------------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Board Size Group
        size_group = QGroupBox("Board Dimension")
        size_form = QFormLayout(size_group)
        self.n_spin = QSpinBox()
        self.n_spin.setRange(4, 500)
        self.n_spin.setValue(8)
        self.n_spin.valueChanged.connect(self._on_n_changed)
        size_form.addRow("Queens (N):", self.n_spin)
        left_layout.addWidget(size_group)

        # Algorithm Selection Group
        algo_group = QGroupBox("Algorithm Family")
        algo_layout = QVBoxLayout(algo_group)
        self.radio_sat = QRadioButton("PySAT (Glucose3 - Propositional Logic)")
        self.radio_mc = QRadioButton("Local Search (Min-Conflicts - Lecture 08)")
        self.radio_mc.setChecked(True)
        self.radio_sat.toggled.connect(self._on_algo_toggled)
        algo_layout.addWidget(self.radio_mc)
        algo_layout.addWidget(self.radio_sat)
        left_layout.addWidget(algo_group)

        # Options Container (Stacked widget)
        self.options_stack = QStackedWidget()

        # Page 0: Min-Conflicts Options
        mc_page = QWidget()
        mc_form = QFormLayout(mc_page)
        mc_form.setContentsMargins(0, 4, 0, 4)

        self.mc_selector = QComboBox()
        self.mc_selector.addItem("random (Baseline Lecture 08)", "random")
        self.mc_selector.addItem("max (Proposed Heuristic H1)", "max")
        self.mc_selector.addItem("weighted (Proposed Heuristic H2)", "weighted")
        mc_form.addRow("Variable Heuristic:", self.mc_selector)

        self.mc_init = QComboBox()
        self.mc_init.addItem("random (Baseline)", "random")
        self.mc_init.addItem("greedy (Optimized start)", "greedy")
        mc_form.addRow("Initial State:", self.mc_init)

        self.mc_restarts = QCheckBox("Enable Random Restarts")
        self.mc_restarts.setChecked(False)
        self.mc_restarts.toggled.connect(self._on_restarts_toggled)
        mc_form.addRow("Restarts:", self.mc_restarts)

        self.mc_restart_factor = QSpinBox()
        self.mc_restart_factor.setRange(1, 100)
        self.mc_restart_factor.setValue(10)
        self.mc_restart_factor.setEnabled(False)
        mc_form.addRow("Restart Limit (x N steps):", self.mc_restart_factor)

        self.mc_max_factor = QSpinBox()
        self.mc_max_factor.setRange(10, 2000)
        self.mc_max_factor.setValue(100)
        mc_form.addRow("Total Budget (x N steps):", self.mc_max_factor)

        self.mc_seed = QLineEdit()
        self.mc_seed.setPlaceholderText("Optional integer seed")
        mc_form.addRow("Random Seed:", self.mc_seed)

        mc_group = QGroupBox("Min-Conflicts Settings")
        mc_group_layout = QVBoxLayout(mc_group)
        mc_group_layout.addWidget(mc_page)
        self.options_stack.addWidget(mc_group)

        # Page 1: SAT Options
        sat_page = QWidget()
        sat_form = QFormLayout(sat_page)
        sat_form.setContentsMargins(0, 4, 0, 4)

        self.sat_encoding = QComboBox()
        self.sat_encoding.addItem("pairwise (Baseline O(N^3))", "pairwise")
        self.sat_encoding.addItem("sequential (Optimized O(N^2))", "sequential")
        sat_form.addRow("At-Most-One Encoding:", self.sat_encoding)

        self.sat_column_alo = QCheckBox("Add Column ALO (Redundant)")
        self.sat_column_alo.setChecked(False)
        sat_form.addRow("Clauses:", self.sat_column_alo)

        self.sat_timeout = QDoubleSpinBox()
        self.sat_timeout.setRange(1.0, 300.0)
        self.sat_timeout.setValue(30.0)
        self.sat_timeout.setSuffix(" s")
        sat_form.addRow("Solve Time Limit:", self.sat_timeout)

        sat_group = QGroupBox("SAT Glucose3 Settings")
        sat_group_layout = QVBoxLayout(sat_group)
        sat_group_layout.addWidget(sat_page)
        self.options_stack.addWidget(sat_group)

        left_layout.addWidget(self.options_stack)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_solve = QPushButton("⚡ Solve Board")
        self.btn_solve.setProperty("class", "primary")
        self.btn_solve.clicked.connect(self._on_solve_clicked)

        self.btn_cancel = QPushButton("✖ Cancel")
        self.btn_cancel.setProperty("class", "danger")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)

        btn_layout.addWidget(self.btn_solve)
        btn_layout.addWidget(self.btn_cancel)
        left_layout.addLayout(btn_layout)

        # Equivalent CLI Copy
        self.btn_copy_cli = QPushButton("📋 Copy Equivalent CLI Command")
        self.btn_copy_cli.clicked.connect(self._copy_cli_command)
        left_layout.addWidget(self.btn_copy_cli)

        left_layout.addStretch()

        # Wrap in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left_widget)
        scroll.setMinimumWidth(320)
        scroll.setMaximumWidth(400)
        splitter.addWidget(scroll)

        # -------------------- RIGHT PANEL: BOARD & STATS --------------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Stat cards row
        stats_layout = QHBoxLayout()
        self.card_status = StatCard("Status", "READY", subtext="Awaiting solve command")
        self.card_time = StatCard("Execution Time", "-", subtext="Wall-clock")
        self.card_work = StatCard("Steps / Clauses", "-", subtext="Search workload")
        self.card_valid = StatCard("Validation", "-", subtext="Attacking pairs")

        stats_layout.addWidget(self.card_status)
        stats_layout.addWidget(self.card_time)
        stats_layout.addWidget(self.card_work)
        stats_layout.addWidget(self.card_valid)
        right_layout.addLayout(stats_layout)

        # Chessboard canvas
        self.board_view = BoardView()
        self.board_view.set_board(8, None)
        right_layout.addWidget(self.board_view, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

    def _on_n_changed(self, val: int) -> None:
        self.board_view.set_board(val, None)

    def _on_algo_toggled(self) -> None:
        if self.radio_mc.isChecked():
            self.options_stack.setCurrentIndex(0)
        else:
            self.options_stack.setCurrentIndex(1)

    def _on_restarts_toggled(self, checked: bool) -> None:
        self.mc_restart_factor.setEnabled(checked)

    def _on_solve_clicked(self) -> None:
        n = self.n_spin.value()
        mode = "sat" if self.radio_sat.isChecked() else "minconf"

        # Warning for large N on slow configurations
        if mode == "sat":
            enc = self.sat_encoding.currentData()
            if enc == "sequential" and n >= 60:
                ret = QMessageBox.question(
                    self, "Performance Warning",
                    f"Sequential encoding at N={n} is known to be slow for Glucose and may time out.\nContinue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if ret != QMessageBox.Yes:
                    return
            elif enc == "pairwise" and n > 120:
                ret = QMessageBox.question(
                    self, "Memory Warning",
                    f"Pairwise encoding at N={n} generates over 2.5 million clauses.\nContinue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if ret != QMessageBox.Yes:
                    return

        params = {}
        if mode == "sat":
            params = {
                "encoding": self.sat_encoding.currentData(),
                "column_alo": self.sat_column_alo.isChecked(),
                "time_limit_s": self.sat_timeout.value(),
            }
        else:
            seed_val = None
            if self.mc_seed.text().strip():
                try:
                    seed_val = int(self.mc_seed.text().strip())
                except ValueError:
                    QMessageBox.warning(self, "Invalid Seed", "Seed must be an integer.")
                    return

            params = {
                "selector": self.mc_selector.currentData(),
                "initializer": self.mc_init.currentData(),
                "max_steps_factor": self.mc_max_factor.value(),
                "restart_steps_factor": self.mc_restart_factor.value() if self.mc_restarts.isChecked() else None,
                "seed": seed_val,
            }

        self.btn_solve.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.card_status.set_value("RUNNING...", "Solver running in background", color="#58A6FF")
        self.card_time.set_value("-")
        self.card_work.set_value("-")
        self.card_valid.set_value("-")

        self.worker = SolveWorker(mode, n, params, self)
        self.worker.solved.connect(self._on_solve_finished)
        self.worker.error.connect(self._on_solve_error)
        self.worker.start()

    def _on_cancel_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            self.card_status.set_value("CANCELLING...", color="#DC3545")
            self.worker.cancel()

    def _on_solve_finished(self, res: SolveResult) -> None:
        self.btn_solve.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        if res.extra.get("cancelled", False):
            self.card_status.set_value("CANCELLED", "User interrupted", color="#F85149")
            return

        if res.extra.get("timed_out", False):
            self.card_status.set_value("TIMED OUT", "Exceeded time limit", color="#F85149")
            self.card_time.set_value(f"{res.time_s:.3f} s")
            return

        if res.solved and res.board:
            self.card_status.set_value("SOLVED", "Valid solution found!", color="#3FB950")
            self.card_time.set_value(f"{res.time_s:.5f} s")
            if res.num_clauses > 0:
                self.card_work.set_value(f"{res.num_clauses:,} cls", f"Vars: {res.extra.get('variables', '-')}")
            else:
                self.card_work.set_value(f"{res.steps} steps", f"Restarts: {res.extra.get('restarts', 0)}")

            attacks = res.board.count_attacking_pairs()
            self.card_valid.set_value("VALID" if attacks == 0 else f"{attacks} attacks",
                                      "Independent Board check",
                                      color="#3FB950" if attacks == 0 else "#F85149")
            self.board_view.set_board(res.n, res.board.queens)
        else:
            self.card_status.set_value("FAILED / UNSAT", "No solution found", color="#F85149")
            self.card_time.set_value(f"{res.time_s:.5f} s")
            if res.board:
                self.board_view.set_board(res.n, res.board.queens)

    def _on_solve_error(self, err_msg: str) -> None:
        self.btn_solve.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.card_status.set_value("ERROR", "Exception occurred", color="#F85149")
        QMessageBox.critical(self, "Solver Error", f"An error occurred while solving:\n{err_msg}")

    def _copy_cli_command(self) -> None:
        n = self.n_spin.value()
        mode = "sat" if self.radio_sat.isChecked() else "minconf"
        if mode == "sat":
            enc = self.sat_encoding.currentData()
            alo = " --column-alo" if self.sat_column_alo.isChecked() else ""
            cmd = f".\\.venv\\Scripts\\python main.py demo --n {n} --encoding {enc}{alo}"
        else:
            sel = self.mc_selector.currentData()
            init = self.mc_init.currentData()
            restarts = f" --restarts --restart-factor {self.mc_restart_factor.value()}" if self.mc_restarts.isChecked() else ""
            seed_part = f" --seed {self.mc_seed.text().strip()}" if self.mc_seed.text().strip() else ""
            cmd = f".\\.venv\\Scripts\\python main.py demo --n {n} --selector {sel} --init {init}{restarts}{seed_part}"

        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(cmd)
        QMessageBox.information(self, "Command Copied", f"Copied command to clipboard:\n\n{cmd}")
