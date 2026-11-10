"""Interactive, high-contrast chessboard rendering widget."""
from __future__ import annotations

from typing import List, Optional, Set, Tuple

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget


class BoardView(QWidget):
    """Draws an N x N chessboard with queens, conflict highlights, and move tracking."""

    COLOR_BG = QColor("#161B22")
    COLOR_LIGHT = QColor("#C8A780")
    COLOR_DARK = QColor("#6D4627")
    COLOR_CONFLICT = QColor("#D90429")
    COLOR_MOVED = QColor("#1F6FEB")
    COLOR_QUEEN_LIGHT = QColor("#161B22")
    COLOR_QUEEN_DARK = QColor("#F0F6FC")
    COLOR_QUEEN_CONFLICT = QColor("#FFF3BF")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.n: int = 8
        self.queens: List[Tuple[int, int]] = []  # list of (r, c)
        self.conflicts: List[int] = []           # conflict count per queen/column
        self.conflicted_cols: Set[int] = set()
        self.last_move: Optional[Tuple[int, int]] = None  # (row, col)
        self.setMouseTracking(True)
        self.setMinimumSize(260, 260)

    def set_board(self, n: int, queens_or_rows,
                  conflicts: Optional[List[int]] = None,
                  last_move: Optional[Tuple[int, int]] = None) -> None:
        """Update board state and trigger redraw."""
        self.n = n
        self.last_move = last_move
        if queens_or_rows is None:
            self.queens = []
            self.conflicts = []
            self.conflicted_cols = set()
        elif isinstance(queens_or_rows, list) and len(queens_or_rows) > 0 and isinstance(queens_or_rows[0], tuple):
            self.queens = list(queens_or_rows)
            self._compute_attacks()
        else:
            self.queens = [(r, c) for c, r in enumerate(queens_or_rows) if r is not None]
            if conflicts is not None:
                self.conflicts = list(conflicts)
                self.conflicted_cols = {c for c, cnt in enumerate(conflicts) if cnt > 0}
            else:
                self._compute_attacks()
        self.update()

    def _compute_attacks(self) -> None:
        """Compute conflicts between queens if not supplied."""
        n = len(self.queens)
        self.conflicts = [0] * n
        self.conflicted_cols = set()
        for i in range(n):
            for j in range(i + 1, n):
                r1, c1 = self.queens[i]
                r2, c2 = self.queens[j]
                if r1 == r2 or c1 == c2 or (r1 - c1 == r2 - c2) or (r1 + c1 == r2 + c2):
                    self.conflicts[i] += 1
                    self.conflicts[j] += 1
                    self.conflicted_cols.add(c1)
                    self.conflicted_cols.add(c2)

    def clear(self) -> None:
        self.queens = []
        self.conflicts = []
        self.conflicted_cols = set()
        self.last_move = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # Fill background cleanly
        painter.fillRect(self.rect(), self.COLOR_BG)

        w = self.width()
        h = self.height()
        size = min(w, h) - 24
        if size <= 0 or self.n <= 0:
            return

        tile_size = size / self.n
        offset_x = (w - (tile_size * self.n)) / 2
        offset_y = (h - (tile_size * self.n)) / 2

        # Draw border
        border_rect = QRectF(offset_x - 3, offset_y - 3,
                             tile_size * self.n + 6, tile_size * self.n + 6)
        painter.setPen(QPen(QColor("#30363D"), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(border_rect)

        # Build queen lookup
        queen_map = {}
        for idx, (r, c) in enumerate(self.queens):
            conf = self.conflicts[idx] if idx < len(self.conflicts) else 0
            queen_map[(r, c)] = (conf, idx)

        # Draw tiles
        painter.setPen(Qt.NoPen)
        for r in range(self.n):
            for c in range(self.n):
                rect = QRectF(offset_x + c * tile_size, offset_y + r * tile_size,
                              tile_size, tile_size)
                is_dark = (r + c) % 2 == 1
                base_color = self.COLOR_DARK if is_dark else self.COLOR_LIGHT

                if (r, c) in queen_map:
                    conf, _ = queen_map[(r, c)]
                    if conf > 0:
                        tile_color = self.COLOR_CONFLICT
                    elif self.last_move and self.last_move == (r, c):
                        tile_color = self.COLOR_MOVED
                    else:
                        tile_color = base_color
                else:
                    tile_color = base_color

                painter.setBrush(QBrush(tile_color))
                painter.drawRect(rect)

        # Draw queens
        if self.n <= 28:
            font_size = max(9, int(tile_size * 0.64))
            font = QFont("Segoe UI Symbol", font_size, QFont.Bold)
            painter.setFont(font)

            for (r, c), (conf, _) in queen_map.items():
                rect = QRectF(offset_x + c * tile_size, offset_y + r * tile_size,
                              tile_size, tile_size)
                is_dark = (r + c) % 2 == 1
                if conf > 0:
                    q_color = self.COLOR_QUEEN_CONFLICT
                elif self.last_move and self.last_move == (r, c):
                    q_color = QColor("#FFFFFF")
                elif is_dark:
                    q_color = self.COLOR_QUEEN_DARK
                else:
                    q_color = self.COLOR_QUEEN_LIGHT

                painter.setPen(q_color)
                painter.drawText(rect, Qt.AlignCenter, "♛")
        elif self.n <= 70:
            radius = max(2.5, tile_size * 0.38)
            for (r, c), (conf, _) in queen_map.items():
                center_x = offset_x + (c + 0.5) * tile_size
                center_y = offset_y + (r + 0.5) * tile_size
                is_dark = (r + c) % 2 == 1
                if conf > 0:
                    color = self.COLOR_QUEEN_CONFLICT
                elif self.last_move and self.last_move == (r, c):
                    color = QColor("#FFFFFF")
                elif is_dark:
                    color = self.COLOR_QUEEN_DARK
                else:
                    color = self.COLOR_QUEEN_LIGHT

                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor("#000000"), 0.5))
                painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(radius), int(radius))
        else:
            for (r, c), (conf, _) in queen_map.items():
                rect = QRectF(offset_x + c * tile_size, offset_y + r * tile_size,
                              tile_size, tile_size)
                color = self.COLOR_QUEEN_CONFLICT if conf > 0 else self.COLOR_QUEEN_DARK
                painter.setBrush(QBrush(color))
                painter.drawRect(rect)

    def mouseMoveEvent(self, event) -> None:
        w, h = self.width(), self.height()
        size = min(w, h) - 24
        if size <= 0 or self.n <= 0:
            return
        tile_size = size / self.n
        offset_x = (w - (tile_size * self.n)) / 2
        offset_y = (h - (tile_size * self.n)) / 2

        pos = event.position()
        c = int((pos.x() - offset_x) // tile_size)
        r = int((pos.y() - offset_y) // tile_size)

        if 0 <= r < self.n and 0 <= c < self.n:
            has_queen = (r, c) in self.queens
            if has_queen:
                idx = self.queens.index((r, c))
                conf = self.conflicts[idx] if idx < len(self.conflicts) else 0
                QToolTip.showText(event.globalPosition().toPoint(),
                                  f"Queen at Row {r}, Col {c}\nConflicts: {conf}", self)
            else:
                QToolTip.showText(event.globalPosition().toPoint(),
                                  f"Square ({r}, {c}) - Empty", self)
        else:
            QToolTip.hideText()
