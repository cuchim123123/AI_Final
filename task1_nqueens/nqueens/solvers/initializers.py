"""Initial-state strategies for Min-Conflicts."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Dict, List

from .conflict_tracker import ConflictTracker


class Initializer(ABC):
    """Strategy producing the starting assignment (row of each column)."""

    name = "abstract"

    @abstractmethod
    def build(self, n: int, rng: random.Random) -> List[int]:
        """Return rows[c] for every column c."""


class RandomInitializer(Initializer):
    """Baseline (Lecture 08): every queen on a uniformly random row."""

    name = "random"

    def build(self, n, rng):
        return [rng.randrange(n) for _ in range(n)]


class GreedyInitializer(Initializer):
    """Optimisation: place columns left to right, each on a minimum-conflict row.

    Each queen only considers queens already placed, so the start state has far
    fewer conflicts than a random one and the local search has less to repair.
    Costs O(N^2) once per start (O(N) per queen).
    """

    name = "greedy"

    def build(self, n, rng):
        tracker = ConflictTracker(n)
        for c in range(n):
            scores = [tracker.conflicts_at(c, r) for r in range(n)]
            best = min(scores)
            tracker.place(c, rng.choice([r for r in range(n) if scores[r] == best]))
        return list(tracker.rows)


# Registry used by the factory / CLI to look initializers up by name.
INITIALIZERS: Dict[str, type] = {
    cls.name: cls for cls in (RandomInitializer, GreedyInitializer)
}
