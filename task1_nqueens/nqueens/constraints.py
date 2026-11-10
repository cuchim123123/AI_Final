"""Constraint discovery: find all lines of mutually attacking squares."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, Iterator, List, Tuple

Square = Tuple[int, int]


@dataclass(frozen=True)
class Line:
    """Squares that mutually attack each other (a row/column/diagonal)."""
    kind: str  # 'row' | 'col' | 'diag' | 'anti'
    key: int
    squares: Tuple[Square, ...]

    def pairs(self) -> Iterator[Tuple[Square, Square]]:
        return combinations(self.squares, 2)


class ConstraintGenerator:
    """Discovers constraints by bucketing squares on row/col/diagonal keys.

    O(N^2) bucketing; every bucket with >= 2 squares is an at-most-one line.
    """

    def __init__(self, n: int) -> None:
        self.n = n

    def lines(self) -> List[Line]:
        buckets: Dict[Tuple[str, int], List[Square]] = {}
        for r in range(self.n):
            for c in range(self.n):
                for key in (("row", r), ("col", c),
                            ("diag", r - c), ("anti", r + c)):
                    buckets.setdefault(key, []).append((r, c))
        return [Line(k[0], k[1], tuple(sq))
                for k, sq in buckets.items() if len(sq) >= 2]
