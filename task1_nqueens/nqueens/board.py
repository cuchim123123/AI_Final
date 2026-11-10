"""Board: queen placements and independent validation."""
from __future__ import annotations

from typing import Iterable, List, Optional


class Board:
    """An N x N board holding a set of queen positions (row, col)."""

    def __init__(self, n: int, queens: Optional[Iterable[tuple]] = None) -> None:
        self.n = n
        self.queens: List[tuple] = sorted(queens) if queens is not None else []

    @classmethod
    def from_model(cls, model: Iterable[int], n: int) -> "Board":
        """Build from a SAT model (DIMACS literals, var = r*n + c + 1)."""
        queens = [divmod(lit - 1, n) for lit in model if 0 < lit <= n * n]
        return cls(n, queens)

    @classmethod
    def from_columns(cls, rows_by_col: List[int]) -> "Board":
        """Build from the one-queen-per-column form: rows_by_col[c] = row."""
        return cls(len(rows_by_col), [(r, c) for c, r in enumerate(rows_by_col)])

    @staticmethod
    def _attacks(a: tuple, b: tuple) -> bool:
        return (a[0] == b[0] or a[1] == b[1]
                or a[0] - a[1] == b[0] - b[1] or a[0] + a[1] == b[0] + b[1])

    def count_attacking_pairs(self) -> int:
        q = self.queens
        return sum(self._attacks(q[i], q[j])
                   for i in range(len(q)) for j in range(i + 1, len(q)))

    def is_valid(self) -> bool:
        """True iff exactly N distinct queens on the board and none attack."""
        return (len(self.queens) == self.n
                and len(set(self.queens)) == self.n
                and all(0 <= r < self.n and 0 <= c < self.n for r, c in self.queens)
                and self.count_attacking_pairs() == 0)

    def __str__(self) -> str:
        qs = set(self.queens)
        return "\n".join(
            " ".join("Q" if (r, c) in qs else "." for c in range(self.n))
            for r in range(self.n))
