"""CNF encoders (baseline pairwise + optimised sequential) and the SAT solver."""
import pytest
from pysat.solvers import Glucose3

from nqueens.amo import PairwiseAMO, SequentialCounterAMO
from nqueens.cnf import CNFEncoder
from nqueens.constraints import ConstraintGenerator
from nqueens.factory import build_sat

AMOS = [PairwiseAMO, SequentialCounterAMO]


def test_var_roundtrip():
    e = CNFEncoder(6)
    assert all(e.decode(e.var(r, c)) == (r, c) for r in range(6) for c in range(6))


@pytest.mark.parametrize("amo_cls", AMOS)
@pytest.mark.parametrize("alo", [False, True])
@pytest.mark.parametrize("n", range(4, 11))
def test_clause_count_matches_geometry(n, alo, amo_cls):
    amo = amo_cls()
    e = CNFEncoder(n, amo, alo)
    assert e.num_clauses == CNFEncoder.expected_clause_count(n, amo, alo)


@pytest.mark.parametrize("n", range(4, 11))
def test_pairwise_matches_closed_form(n):
    """Hand-derived formula: N + 2N*C(N,2) + 4*C(N,3) + 2*C(N,2)."""
    c2, c3 = n * (n - 1) // 2, n * (n - 1) * (n - 2) // 6
    assert CNFEncoder(n).num_clauses == n + 2 * n * c2 + 4 * c3 + 2 * c2


def test_known_counts_n4():
    assert CNFEncoder(4).num_clauses == 80
    assert CNFEncoder(4, SequentialCounterAMO()).num_clauses == 112


def test_sequential_has_fewer_clauses_for_large_n():
    n = 30
    assert (CNFEncoder(n, SequentialCounterAMO()).num_clauses
            < CNFEncoder(n, PairwiseAMO()).num_clauses)


@pytest.mark.parametrize("amo_cls", AMOS)
def test_aux_variable_count(amo_cls):
    amo = amo_cls()
    e = CNFEncoder(8, amo)
    lines = [len(ln.squares) for ln in ConstraintGenerator(8).lines()]
    assert e.num_vars == 64 + sum(amo.aux_var_count(k) for k in lines)


@pytest.mark.parametrize("amo_cls", AMOS)
def test_amo_semantics(amo_cls):
    """For 4 literals: at most one True is satisfiable, two True is not."""
    amo = amo_cls()
    clauses, _ = amo.encode([1, 2, 3, 4], next_var=5)
    for ones, expect in [([], True), ([2], True), ([1, 4], False), ([1, 2, 3], False)]:
        assumptions = [v if v in ones else -v for v in (1, 2, 3, 4)]
        with Glucose3(bootstrap_with=clauses) as g:
            assert g.solve(assumptions=assumptions) is expect


@pytest.mark.parametrize("encoding", ["pairwise", "sequential"])
@pytest.mark.parametrize("n", range(4, 13))
def test_sat_solves(encoding, n):
    r = build_sat(encoding).solve(n)
    assert r.solved and r.board.is_valid()


@pytest.mark.parametrize("encoding", ["pairwise", "sequential"])
@pytest.mark.parametrize("n", [2, 3])
def test_sat_unsat_small(encoding, n):
    assert not build_sat(encoding).solve(n).solved


@pytest.mark.parametrize("amo_cls", AMOS)
def test_encodings_have_same_solutions(amo_cls):
    """Projected on board variables both encodings admit all 4 solutions of N=6."""
    n = 6
    e = CNFEncoder(n, amo_cls())
    solutions = set()
    with Glucose3(bootstrap_with=e.encode()) as g:
        while g.solve():
            board = frozenset(l for l in g.get_model() if 0 < l <= n * n)
            solutions.add(board)
            g.add_clause([-l for l in board] + [l for l in range(1, n * n + 1)
                                                if l not in board])  # block it
    assert len(solutions) == 4
