"""Incremental conflict bookkeeping shared by initializers and the solver."""
from __future__ import annotations

from typing import List, Optional


class ConflictTracker:
    """One-queen-per-column state with O(1) conflict evaluation.

    `rows[c]` is the row of column c's queen (None while not yet placed).
    Counters of queens per row / diagonal / anti-diagonal let us compute how
    many queens attack any square without scanning the board.
    """

    def __init__(self, n: int) -> None:
        self.n = n
        self.rows: List[Optional[int]] = [None] * n
        self._row_cnt = [0] * n
        self._diag_cnt = [0] * (2 * n - 1)   # indexed by r - c + n - 1
        self._anti_cnt = [0] * (2 * n - 1)   # indexed by r + c

    @classmethod
    def from_rows(cls, rows: List[int]) -> "ConflictTracker":
        """Build a fully-placed tracker from a list of rows (one per column)."""
        tracker = cls(len(rows))
        for c, r in enumerate(rows):
            tracker.place(c, r)
        return tracker

    def _update(self, c: int, r: int, delta: int) -> None:
        self._row_cnt[r] += delta
        self._diag_cnt[r - c + self.n - 1] += delta
        self._anti_cnt[r + c] += delta

    def place(self, c: int, r: int) -> None:
        """Put the (not yet placed) queen of column c on row r."""
        self.rows[c] = r
        self._update(c, r, +1)

    def move(self, c: int, r: int) -> None:
        """Move column c's queen to row r in O(1)."""
        self._update(c, self.rows[c], -1)
        self.rows[c] = r
        self._update(c, r, +1)

    def conflicts_at(self, c: int, r: int) -> int:
        """Number of other queens attacking square (r, c).

        If column c's own queen already sits on row r it is counted once in
        each of the three counters, so subtract those 3 self-hits.
        """
        cnt = (self._row_cnt[r] + self._diag_cnt[r - c + self.n - 1]
               + self._anti_cnt[r + c])
        return cnt - 3 if self.rows[c] == r else cnt

    def conflict_vector(self) -> List[int]:
        """Conflicts of every placed queen at its current square."""
        return [self.conflicts_at(c, r) for c, r in enumerate(self.rows)]
