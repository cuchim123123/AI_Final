"""Embedded Matplotlib canvas with dark-theme styling support."""
from __future__ import annotations

from typing import List, Optional

import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


def apply_dark_theme_to_figure(fig: Figure) -> None:
    """Style a Matplotlib figure for seamless dark mode."""
    fig.patch.set_facecolor("#161B22")
    for ax in fig.get_axes():
        ax.set_facecolor("#0D1117")
        ax.tick_params(colors="#C9D1D9", labelsize=8)
        ax.xaxis.label.set_color("#C9D1D9")
        ax.yaxis.label.set_color("#C9D1D9")
        ax.title.set_color("#F0F6FC")
        for spine in ax.spines.values():
            spine.set_color("#30363D")
        ax.grid(True, linestyle="--", alpha=0.3, color="#30363D")
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor("#161B22")
            legend.get_frame().set_edgecolor("#30363D")
            for text in legend.get_texts():
                text.set_color("#C9D1D9")


class MatplotlibCanvas(QWidget):
    """A Qt widget embedding a Matplotlib Figure."""

    def __init__(self, parent=None, width=5, height=4, dpi=100) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        apply_dark_theme_to_figure(self.figure)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def set_figure(self, fig: Figure) -> None:
        """Replace the current figure with a new one."""
        layout = self.layout()
        layout.removeWidget(self.canvas)
        self.canvas.deleteLater()

        self.figure = fig
        apply_dark_theme_to_figure(self.figure)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        self.canvas.draw()


class LiveConflictPlot(QWidget):
    """Real-time convergence chart (Conflicts vs Steps) for Min-Conflicts visualizer."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(4.5, 3.0), dpi=95)
        self.canvas = FigureCanvasQTAgg(self.figure)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Search Convergence", fontsize=11, fontweight="bold", pad=8)
        self.ax.set_xlabel("Step", fontsize=9)
        self.ax.set_ylabel("Total Conflicts", fontsize=9)
        apply_dark_theme_to_figure(self.figure)
        self.figure.tight_layout()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.steps: List[int] = []
        self.conflicts: List[int] = []
        self.line, = self.ax.plot([], [], color="#58A6FF", lw=2.0, label="Attacking Pairs")
        legend = self.ax.legend(loc="upper right", fontsize=8)
        if legend:
            legend.get_frame().set_facecolor("#161B22")
            legend.get_frame().set_edgecolor("#30363D")
            for text in legend.get_texts():
                text.set_color("#C9D1D9")

    def reset(self) -> None:
        self.steps = []
        self.conflicts = []
        self.line.set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def add_point(self, step: int, total_conflicts: int) -> None:
        self.steps.append(step)
        self.conflicts.append(total_conflicts)
        self.line.set_data(self.steps, self.conflicts)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()
