"""At-most-one (AMO) CNF encodings (Strategy pattern).

An AMO constraint says "at most one of these literals is True". How it is
turned into clauses is the only thing that differs between the baseline
encoding (pairwise) and the optimised one (sequential counter), so it is
isolated behind one small interface that `CNFEncoder` depends on.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

Clause = List[int]


class AtMostOneEncoder(ABC):
    """Strategy: encode "at most one of `literals` is True" as CNF."""

    name = "abstract"

    @abstractmethod
    def encode(self, literals: Sequence[int], next_var: int) -> Tuple[List[Clause], int]:
        """Return (clauses, next_free_var).

        `next_var` is the first unused DIMACS variable id; encodings that need
        auxiliary variables take ids from there and return the new free id.
        """

    @abstractmethod
    def clause_count(self, k: int) -> int:
        """Number of clauses produced for k literals (used to verify the encoder)."""

    @abstractmethod
    def aux_var_count(self, k: int) -> int:
        """Number of auxiliary variables created for k literals."""


class PairwiseAMO(AtMostOneEncoder):
    """Baseline: one binary clause (~a v ~b) per pair of literals.

    `~(a ^ b) == (~a v ~b)` by De Morgan. No auxiliary variables, but k(k-1)/2
    clauses per line, which makes the whole N-Queens formula Theta(N^3).
    """

    name = "pairwise"

    def encode(self, literals, next_var):
        clauses = [[-a, -b] for a, b in combinations(literals, 2)]
        return clauses, next_var

    def clause_count(self, k):
        return k * (k - 1) // 2

    def aux_var_count(self, k):
        return 0


class SequentialCounterAMO(AtMostOneEncoder):
    """Optimisation: Sinz's sequential-counter encoding.

    Adds k-1 auxiliary variables s_1..s_{k-1}, where s_i means "some literal
    among x_1..x_i is True". Clauses:
        (~x_1 v s_1)
        (~x_i v s_i), (~s_{i-1} v s_i), (~x_i v ~s_{i-1})   for 1 < i < k
        (~x_k v ~s_{k-1})
    That is 3k-4 clauses (linear) instead of k(k-1)/2 (quadratic), so the whole
    formula becomes Theta(N^2) clauses.
    """

    name = "sequential"

    def encode(self, literals, next_var):
        k = len(literals)
        if k < 2:
            return [], next_var                      # nothing to constrain
        s = list(range(next_var, next_var + k - 1))  # fresh auxiliary variables
        clauses: List[Clause] = [[-literals[0], s[0]]]
        for i in range(1, k - 1):
            clauses.append([-literals[i], s[i]])        # x_i  -> s_i
            clauses.append([-s[i - 1], s[i]])           # s_{i-1} -> s_i
            clauses.append([-literals[i], -s[i - 1]])   # x_i and s_{i-1} not both
        clauses.append([-literals[k - 1], -s[k - 2]])
        return clauses, next_var + k - 1

    def clause_count(self, k):
        return 3 * k - 4 if k >= 2 else 0

    def aux_var_count(self, k):
        return k - 1 if k >= 2 else 0


# Registry used by the factory / CLI to look encodings up by name.
AMO_ENCODERS: Dict[str, type] = {
    cls.name: cls for cls in (PairwiseAMO, SequentialCounterAMO)
}
