"""Abstract solver interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..result import SolveResult


class Solver(ABC):
    @abstractmethod
    def solve(self, n: int) -> SolveResult:
        """Solve N-Queens for board size n."""
