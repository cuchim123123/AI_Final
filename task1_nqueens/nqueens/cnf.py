"""CNF encoding of N-Queens."""
from __future__ import annotations

from typing import List, Optional

from .amo import AtMostOneEncoder, PairwiseAMO
from .constraints import ConstraintGenerator

Clause = List[int]


class CNFEncoder:
    """Turns the discovered constraints into CNF clauses.

    * ALO per row:   (X(r,0) v ... v X(r,N-1))
    * AMO per line:  delegated to an injected `AtMostOneEncoder`
                     (pairwise by default = baseline).
    * optional ALO per column (redundant, helps propagation).

    Board variables are numbered 1..N^2 (`var(r, c)`); any auxiliary variables
    needed by the AMO encoding come after them.
    """

    def __init__(self, n: int, amo: Optional[AtMostOneEncoder] = None,
                 column_alo: bool = False) -> None:
        self.n = n
        self.amo = amo or PairwiseAMO()
        self.column_alo = column_alo
        self._clauses: Optional[List[Clause]] = None  # cache
        self._num_vars = n * n

    def var(self, r: int, c: int) -> int:
        """DIMACS id of X(r, c)."""
        return r * self.n + c + 1

    def decode(self, var: int) -> tuple:
        """Inverse of `var` (valid for board variables only)."""
        return divmod(var - 1, self.n)

    def encode(self) -> List[Clause]:
        """Build (once) and return the full clause list."""
        if self._clauses is None:
            n = self.n
            # "Each row holds at least one queen."
            clauses: List[Clause] = [[self.var(r, c) for c in range(n)]
                                     for r in range(n)]
            if self.column_alo:
                clauses += [[self.var(r, c) for r in range(n)] for c in range(n)]
            # "Each row/column/diagonal holds at most one queen."
            next_var = n * n + 1
            for line in ConstraintGenerator(n).lines():
                literals = [self.var(r, c) for r, c in line.squares]
                new_clauses, next_var = self.amo.encode(literals, next_var)
                clauses.extend(new_clauses)
            self._clauses = clauses
            self._num_vars = next_var - 1
        return self._clauses

    @property
    def num_vars(self) -> int:
        """Total variables, including auxiliary ones."""
        self.encode()
        return self._num_vars

    @property
    def num_clauses(self) -> int:
        return len(self.encode())

    @staticmethod
    def expected_clause_count(n: int, amo: Optional[AtMostOneEncoder] = None,
                              column_alo: bool = False) -> int:
        """Closed-form clause count derived from the board geometry alone.

        Independent of `ConstraintGenerator`, so tests can use it to
        cross-check the discovery algorithm and the encoder together.
        For pairwise AMO it equals N + 2N*C(N,2) + 4*C(N,3) + 2*C(N,2) (+N).
        """
        amo = amo or PairwiseAMO()
        # Rows and columns: 2N lines of length N.
        lengths = [n] * (2 * n)
        # Per diagonal direction: two diagonals of each length 2..N-1, one of length N.
        one_direction = [k for k in range(2, n)] * 2 + [n]
        lengths += one_direction * 2
        total = n + sum(amo.clause_count(k) for k in lengths if k >= 2)
        return total + (n if column_alo else 0)
