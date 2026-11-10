"""Common result object for all solvers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .board import Board


@dataclass
class SolveResult:
    n: int
    solved: bool
    time_s: float
    board: Optional[Board] = None
    steps: int = 0
    num_clauses: int = 0
    extra: dict = field(default_factory=dict)
