"""Tab 3: Experiment Runner, Table Analysis, and Embedded Plots."""
from __future__ import annotations

import os
from typing import List

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nqueens.experiments import Plotter
from ..widgets.chart_widget import MatplotlibCanvas
from ..workers import ExperimentWorker


class ExperimentView(QWidget):
    """View to configure and execute batch experiments with live charts and tables."""

    PRESETS = {
        "sat_quick": "4, 6, 8, 12, 16",
        "sat_full": "4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 50, 64, 80, 100",
        "mc_quick": "8, 16, 32, 64",
        "mc_full": "8, 16, 32, 64, 128, 256, 512, 1000",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.worker: ExperimentWorker | None = None
        self.raw_df: pd.DataFrame = pd.DataFrame()
        self.summary_df: pd.DataFrame = pd.DataFrame()
        self.cmp_df: pd.DataFrame = pd.DataFrame()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        splitter = QSplitter(Qt.Horizontal)

        # -------------------- LEFT PANEL: CONFIGURATION --------------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        cfg_group = QGroupBox("Experiment Selection")
        cfg_form = QFormLayout(cfg_group)

        self.combo_type = QComboBox()
        self.combo_type.addItem("R2: SAT Glucose3 Benchmark", "sat")
        self.combo_type.addItem("R3: Min-Conflicts Heuristics", "minconf")
        self.combo_type.addItem("Optimizations vs Baseline", "optimize")
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        cfg_form.addRow("Type:", self.combo_type)

        self.txt_ns = QLineEdit()
        self.txt_ns.setText(self.PRESETS["sat_quick"])
        cfg_form.addRow("N values:", self.txt_ns)

        preset_layout = QHBoxLayout()
        self.btn_preset_quick = QPushButton("⚡ Quick (Few N)")
        self.btn_preset_full = QPushButton("📊 Full Range")
        self.btn_preset_quick.clicked.connect(self._apply_quick_preset)
        self.btn_preset_full.clicked.connect(self._apply_full_preset)
        preset_layout.addWidget(self.btn_preset_quick)
        preset_layout.addWidget(self.btn_preset_full)
        cfg_form.addRow("Presets:", preset_layout)

        self.spin_runs = QSpinBox()
        self.spin_runs.setRange(1, 100)
        self.spin_runs.setValue(5)
        cfg_form.addRow("Repeats / Runs:", self.spin_runs)

        left_layout.addWidget(cfg_group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("🚀 Run Experiment")
        self.btn_run.setProperty("class", "primary")
        self.btn_run.clicked.connect(self._on_run_clicked)

        self.btn_cancel = QPushButton("✖ Cancel")
        self.btn_cancel.setProperty("class", "danger")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)

        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_cancel)
        left_layout.addLayout(btn_layout)

        # Progress bar
        self.lbl_progress = QLabel("Status: Idle")
        self.lbl_progress.setStyleSheet("color: #495057; font-size: 11px;")
        left_layout.addWidget(self.lbl_progress)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        left_layout.addWidget(self.progress_bar)

        # Export Buttons
        export_group = QGroupBox("Save & Export")
        export_layout = QVBoxLayout(export_group)

        self.txt_tag = QLineEdit()
        self.txt_tag.setPlaceholderText("custom_tag (default auto)")
        export_layout.addWidget(QLabel("Filename Prefix:"))
        export_layout.addWidget(self.txt_tag)

        self.btn_export = QPushButton("💾 Export CSVs & PNGs to results/")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export_clicked)
        export_layout.addWidget(self.btn_export)

        left_layout.addWidget(export_group)
        left_layout.addStretch()

        left_widget.setMinimumWidth(300)
        left_widget.setMaximumWidth(380)
        splitter.addWidget(left_widget)

        # -------------------- RIGHT PANEL: TABLES & CHARTS --------------------
        self.tabs = QTabWidget()

        # Tab 1: Summary Table
        self.table_summary = QTableWidget()
        self.table_summary.setAlternatingRowColors(True)
        self.tabs.addTab(self.table_summary, "📋 Summary Table")

        # Tab 2: Comparison Ratios Table
        self.table_cmp = QTableWidget()
        self.table_cmp.setAlternatingRowColors(True)
        self.tabs.addTab(self.table_cmp, "⚖️ Ratios vs Baseline")

        # Tab 3: Embedded Charts
        self.chart_tabs = QTabWidget()
        self.tabs.addTab(self.chart_tabs, "📈 Interactive Charts")

        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

    def _on_type_changed(self) -> None:
        t = self.combo_type.currentData()
        if t == "sat":
            self.txt_ns.setText(self.PRESETS["sat_quick"])
            self.spin_runs.setValue(5)
            self.tabs.setTabEnabled(1, False)
        elif t == "minconf":
            self.txt_ns.setText(self.PRESETS["mc_quick"])
            self.spin_runs.setValue(10)
            self.tabs.setTabEnabled(1, False)
        else:
            self.txt_ns.setText(self.PRESETS["mc_quick"])
            self.spin_runs.setValue(10)
            self.tabs.setTabEnabled(1, True)

    def _apply_quick_preset(self) -> None:
        t = self.combo_type.currentData()
        self.txt_ns.setText(self.PRESETS["sat_quick"] if t == "sat" else self.PRESETS["mc_quick"])

    def _apply_full_preset(self) -> None:
        t = self.combo_type.currentData()
        self.txt_ns.setText(self.PRESETS["sat_full"] if t == "sat" else self.PRESETS["mc_full"])

    def _parse_ns(self) -> List[int]:
        raw = self.txt_ns.text().replace(" ", "").split(",")
        ns = []
        for item in raw:
            if item.isdigit():
                val = int(item)
                if val >= 4:
                    ns.append(val)
        return sorted(list(set(ns)))

    def _on_run_clicked(self) -> None:
        ns = self._parse_ns()
        if not ns:
            QMessageBox.warning(self, "Invalid Input", "Please provide at least one valid N >= 4.")
            return

        t = self.combo_type.currentData()
        params = {"ns": ns}

        if t == "sat":
            params["encodings"] = ["pairwise", "sequential"]
            params["repeats"] = self.spin_runs.value()
            params["time_limit"] = 30.0
        elif t == "minconf":
            params["runs"] = self.spin_runs.value()
        else:
            params["runs"] = self.spin_runs.value()
            params["selectors"] = ["random", "max"]

        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_export.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_progress.setText("Status: Running benchmark...")

        self.worker = ExperimentWorker(t, params, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_cancel_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            self.lbl_progress.setText("Status: Cancelling...")
            self.worker.cancel()

    def _on_progress(self, done: int, total: int, msg: str) -> None:
        pct = int(done * 100 / max(1, total))
        self.progress_bar.setValue(pct)
        self.lbl_progress.setText(f"Status: {msg} ({done}/{total})")

    def _on_finished(self, raw_df: pd.DataFrame, summary_df: pd.DataFrame, cmp_df: pd.DataFrame) -> None:
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_export.setEnabled(True)
        self.progress_bar.setValue(100)
        self.lbl_progress.setText("Status: Experiment finished!")

        self.raw_df = raw_df
        self.summary_df = summary_df
        self.cmp_df = cmp_df

        self._populate_table(self.table_summary, summary_df)
        if not cmp_df.empty:
            self._populate_cmp_table(self.table_cmp, cmp_df)
            self.tabs.setTabEnabled(1, True)
        else:
            self.tabs.setTabEnabled(1, False)

        self._render_charts(summary_df)

    def _on_failed(self, err: str) -> None:
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.lbl_progress.setText("Status: Failed with error")
        QMessageBox.critical(self, "Experiment Error", f"Failed: {err}")

    def _populate_table(self, table: QTableWidget, df: pd.DataFrame) -> None:
        table.clear()
        if df.empty:
            return
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for r_idx, (_, row) in enumerate(df.iterrows()):
            for c_idx, val in enumerate(row):
                if isinstance(val, float):
                    txt = f"{val:.5f}" if abs(val) < 1 else f"{val:.3f}"
                else:
                    txt = str(val)
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r_idx, c_idx, item)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _populate_cmp_table(self, table: QTableWidget, df: pd.DataFrame) -> None:
        table.clear()
        if df.empty:
            return
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for r_idx, (_, row) in enumerate(df.iterrows()):
            for c_idx, (col_name, val) in enumerate(row.items()):
                item = QTableWidgetItem(f"{val:.3f}" if isinstance(val, float) else str(val))
                item.setTextAlignment(Qt.AlignCenter)

                # Color-code ratios: < 1.0 = green (cheaper), > 1.0 = red (costlier)
                if "ratio" in col_name and isinstance(val, (int, float)):
                    if val < 0.95:
                        item.setBackground(QColor("#1B4721"))
                        item.setForeground(QColor("#7EE787"))
                    elif val > 1.05:
                        item.setBackground(QColor("#5C1D24"))
                        item.setForeground(QColor("#FFA198"))

                table.setItem(r_idx, c_idx, item)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _render_charts(self, summary_df: pd.DataFrame) -> None:
        self.chart_tabs.clear()
        if summary_df.empty:
            return

        plotter = Plotter()
        t = self.combo_type.currentData()
        if t == "sat":
            figs = plotter.create_sat_figures(summary_df)
        else:
            figs = plotter.create_compare_figures(summary_df)

        for name, fig in figs:
            canvas = MatplotlibCanvas(self)
            canvas.set_figure(fig)
            self.chart_tabs.addTab(canvas, name.replace("_", " ").title())

    def _on_export_clicked(self) -> None:
        tag = self.txt_tag.text().strip() or self.combo_type.currentData()
        out_dir = "results"
        os.makedirs(out_dir, exist_ok=True)

        if not self.raw_df.empty:
            self.raw_df.to_csv(f"{out_dir}/{tag}_results.csv", index=False)
        if not self.summary_df.empty:
            self.summary_df.to_csv(f"{out_dir}/{tag}_summary.csv", index=False)
            plotter = Plotter(out_dir)
            if self.combo_type.currentData() == "sat":
                plotter.plot_sat(self.summary_df, tag=tag)
            else:
                plotter.plot_compare(self.summary_df, tag=tag)
        if not self.cmp_df.empty:
            self.cmp_df.to_csv(f"{out_dir}/{tag}_vs_baseline.csv", index=False)

        QMessageBox.information(self, "Export Successful",
                                f"Exported CSVs and plot images to '{out_dir}/' with tag '{tag}'.")
