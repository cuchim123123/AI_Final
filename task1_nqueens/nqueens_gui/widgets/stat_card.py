"""Reusable statistics card widget for displaying metrics."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    """A clean card displaying a title, large metric value, and optional subtext."""

    def __init__(self, title: str, value: str = "-", subtext: str = "",
                 color: str = "#58A6FF", parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            StatCard {
                background-color: #21262D;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #8B949E; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")

        self.val_label = QLabel(value)
        self.val_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 700; background: transparent;")

        self.sub_label = QLabel(subtext)
        self.sub_label.setStyleSheet("color: #6E7681; font-size: 10px; background: transparent;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.val_label)
        layout.addWidget(self.sub_label)

    def set_value(self, value: str, subtext: str = None, color: str = None) -> None:
        self.val_label.setText(str(value))
        if subtext is not None:
            self.sub_label.setText(subtext)
        if color is not None:
            self.val_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 700; background: transparent;")
