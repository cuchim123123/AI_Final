"""Variable-selection strategies for Min-Conflicts."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import List


class VariableSelector(ABC):
    """Strategy choosing which conflicted column to repair next."""
    name = "abstract"

    @abstractmethod
    def select(self, conflicted: List[int], conflicts: List[int],
               rng: random.Random) -> int:
        """conflicted: columns with >=1 conflict; conflicts[c]: #attackers of c."""


class RandomSelector(VariableSelector):
    """Standard Min-Conflicts: uniformly random conflicted variable."""
    name = "random"

    def select(self, conflicted, conflicts, rng):
        return rng.choice(conflicted)


class MaxConflictSelector(VariableSelector):
    """Proposed H1: most-conflicted variable, ties broken randomly."""
    name = "max"

    def select(self, conflicted, conflicts, rng):
        best = max(conflicts[c] for c in conflicted)
        return rng.choice([c for c in conflicted if conflicts[c] == best])


class WeightedConflictSelector(VariableSelector):
    """Proposed H2: random pick with probability proportional to conflicts."""
    name = "weighted"

    def select(self, conflicted, conflicts, rng):
        return rng.choices(conflicted, weights=[conflicts[c] for c in conflicted])[0]


SELECTORS = {cls.name: cls for cls in
             (RandomSelector, MaxConflictSelector, WeightedConflictSelector)}
