"""Tab 2: Min-Conflicts Step-by-Step Interactive Animator."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from nqueens.factory import MinConflictsConfig
from nqueens.result import SolveResult
from ..widgets.board_view import BoardView
from ..widgets.chart_widget import LiveConflictPlot
from ..widgets.stat_card import StatCard
from ..workers import VisualizerWorker


class VisualizerView(QWidget):
    """Interactive visualizer animating the Min-Conflicts local search step-by-step."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.worker: VisualizerWorker | None = None
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

        # Configuration Group
        cfg_group = QGroupBox("Search Parameters")
        cfg_form = QFormLayout(cfg_group)

        self.n_spin = QSpinBox()
        self.n_spin.setRange(4, 100)
        self.n_spin.setValue(8)
        cfg_form.addRow("Queens (N):", self.n_spin)

        self.mc_selector = QComboBox()
        self.mc_selector.addItem("random (Baseline)", "random")
        self.mc_selector.addItem("max (Proposed H1)", "max")
        self.mc_selector.addItem("weighted (Proposed H2)", "weighted")
        cfg_form.addRow("Heuristic:", self.mc_selector)

        self.mc_init = QComboBox()
        self.mc_init.addItem("random (Baseline)", "random")
        self.mc_init.addItem("greedy (Optimized start)", "greedy")
        cfg_form.addRow("Start State:", self.mc_init)

        self.mc_restarts = QCheckBox("Enable Restarts")
        self.mc_restarts.setChecked(False)
        self.mc_restarts.toggled.connect(lambda c: self.mc_restart_factor.setEnabled(c))
        cfg_form.addRow("Restarts:", self.mc_restarts)

        self.mc_restart_factor = QSpinBox()
        self.mc_restart_factor.setRange(1, 100)
        self.mc_restart_factor.setValue(10)
        self.mc_restart_factor.setEnabled(False)
        cfg_form.addRow("Restart Limit:", self.mc_restart_factor)

        self.mc_seed = QLineEdit()
        self.mc_seed.setPlaceholderText("Optional seed")
        cfg_form.addRow("Seed:", self.mc_seed)

        left_layout.addWidget(cfg_group)

        # Animation Speed Group
        anim_group = QGroupBox("Animation Control")
        anim_layout = QVBoxLayout(anim_group)

        speed_label_layout = QHBoxLayout()
        speed_label_layout.addWidget(QLabel("Step Delay:"))
        self.lbl_speed = QLabel("60 ms")
        self.lbl_speed.setStyleSheet("font-weight: bold; color: #58A6FF;")
        speed_label_layout.addWidget(self.lbl_speed, alignment=Qt.AlignRight)
        anim_layout.addLayout(speed_label_layout)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(5, 500)
        self.speed_slider.setValue(60)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        anim_layout.addWidget(self.speed_slider)

        # Playback Buttons
        btn_grid1 = QHBoxLayout()
        self.btn_play = QPushButton("▶ Start")
        self.btn_play.setProperty("class", "success")
        self.btn_play.clicked.connect(self._on_play_clicked)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._on_pause_clicked)

        btn_grid1.addWidget(self.btn_play)
        btn_grid1.addWidget(self.btn_pause)
        anim_layout.addLayout(btn_grid1)

        btn_grid2 = QHBoxLayout()
        self.btn_step = QPushButton("⏭ Step Once")
        self.btn_step.setEnabled(False)
        self.btn_step.clicked.connect(self._on_step_clicked)

        self.btn_stop = QPushButton("⏹ Reset")
        self.btn_stop.setProperty("class", "danger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        btn_grid2.addWidget(self.btn_step)
        btn_grid2.addWidget(self.btn_stop)
        anim_layout.addLayout(btn_grid2)

        left_layout.addWidget(anim_group)

        # Real-time Convergence Chart
        chart_group = QGroupBox("Live Convergence Curve")
        chart_layout = QVBoxLayout(chart_group)
        self.chart_live = LiveConflictPlot()
        chart_layout.addWidget(self.chart_live)
        left_layout.addWidget(chart_group)

        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # -------------------- RIGHT PANEL: BOARD & STATS --------------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Metrics row
        stats_layout = QHBoxLayout()
        self.card_step = StatCard("Current Step", "0", subtext="Repairs made", color="#58A6FF")
        self.card_conflicts = StatCard("Attacking Pairs", "0", subtext="Objective value", color="#F85149")
        self.card_conflicted_cols = StatCard("Queens in Conflict", "0", subtext="Variables to fix", color="#D29922")
        self.card_restarts = StatCard("Restarts", "0", subtext="New states explored", color="#A371F7")

        stats_layout.addWidget(self.card_step)
        stats_layout.addWidget(self.card_conflicts)
        stats_layout.addWidget(self.card_conflicted_cols)
        stats_layout.addWidget(self.card_restarts)
        right_layout.addLayout(stats_layout)

        # Board View
        self.board_view = BoardView()
        self.board_view.set_board(8, None)
        right_layout.addWidget(self.board_view, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

    def _on_speed_changed(self, val: int) -> None:
        self.lbl_speed.setText(f"{val} ms")
        if self.worker:
            self.worker.set_delay(val)

    def _on_play_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            if self.worker.is_paused():
                self.worker.resume()
                self.btn_pause.setText("⏸ Pause")
                self.btn_step.setEnabled(False)
            return

        # Starting fresh animation
        n = self.n_spin.value()
        seed_val = None
        if self.mc_seed.text().strip():
            try:
                seed_val = int(self.mc_seed.text().strip())
            except ValueError:
                pass

        cfg = MinConflictsConfig(
            selector=self.mc_selector.currentData(),
            initializer=self.mc_init.currentData(),
            max_steps_factor=150,
            restart_steps_factor=self.mc_restart_factor.value() if self.mc_restarts.isChecked() else None
        )

        self.chart_live.reset()
        self.card_step.set_value("0")
        self.card_conflicts.set_value("-")
        self.card_conflicted_cols.set_value("-")
        self.card_restarts.set_value("0")

        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("⏸ Pause")
        self.btn_step.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.worker = VisualizerWorker(n, cfg, seed=seed_val, delay_ms=self.speed_slider.value(), parent=self)
        self.worker.step_occurred.connect(self._on_step_occurred)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_pause_clicked(self) -> None:
        if not self.worker or not self.worker.isRunning():
            return

        if self.worker.is_paused():
            self.worker.resume()
            self.btn_pause.setText("⏸ Pause")
            self.btn_step.setEnabled(False)
        else:
            self.worker.pause()
            self.btn_pause.setText("▶ Resume")
            self.btn_step.setEnabled(True)

    def _on_step_clicked(self) -> None:
        if self.worker and self.worker.isRunning() and self.worker.is_paused():
            self.worker.step_once()

    def _on_stop_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
        self._reset_buttons()

    def _on_step_occurred(self, info: dict) -> None:
        step = info["step"]
        rows = info["rows"]
        conflicts = info["conflicts"]
        total_conf = info["total_conflicts"]
        restarts = info["restarts"]
        col = info["col"]
        row = info["row"]
        last_move = (row, col) if col >= 0 and row >= 0 else None

        # Update stat cards
        self.card_step.set_value(str(step))
        self.card_conflicts.set_value(
            str(total_conf),
            color="#3FB950" if total_conf == 0 else "#F85149"
        )
        conf_cols_count = sum(1 for c in conflicts if c > 0)
        self.card_conflicted_cols.set_value(str(conf_cols_count))
        self.card_restarts.set_value(str(restarts))

        # Update board view
        self.board_view.set_board(len(rows), rows, conflicts=conflicts, last_move=last_move)

        # Update chart
        self.chart_live.add_point(step, total_conf)

    def _on_finished(self, res: SolveResult) -> None:
        self._reset_buttons()
        if res.solved:
            self.card_conflicts.set_value("0 (SOLVED!)", color="#3FB950")
        elif res.extra.get("cancelled", False):
            self.card_conflicts.set_value("CANCELLED", color="#8B949E")
        else:
            self.card_conflicts.set_value(f"LIMIT REACHED ({res.steps} steps)", color="#F85149")

    def _on_failed(self, msg: str) -> None:
        self._reset_buttons()

    def _reset_buttons(self) -> None:
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("⏸ Pause")
        self.btn_step.setEnabled(False)
        self.btn_stop.setEnabled(False)
