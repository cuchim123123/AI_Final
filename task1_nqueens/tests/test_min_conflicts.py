"""Min-Conflicts: baseline behaviour, selectors, greedy init, restarts."""
import random

import pytest

from nqueens.factory import MinConflictsConfig, build_min_conflicts
from nqueens.solvers import (SELECTORS, ConflictTracker, GreedyInitializer,
                             MinConflictsSolver, RandomInitializer)


def solve(n, seed, **cfg):
    return build_min_conflicts(MinConflictsConfig(**cfg), seed).solve(n)


# ---- regression: the baseline must behave exactly like the original version
@pytest.mark.parametrize("selector,n,seed,steps", [
    ("random", 16, 5, 91), ("random", 32, 0, 83), ("random", 64, 3, 53),
    ("max", 16, 5, 24), ("max", 32, 0, 97), ("max", 64, 3, 81),
    ("weighted", 16, 5, 56), ("weighted", 32, 0, 42), ("weighted", 64, 3, 109)])
def test_baseline_is_unchanged(selector, n, seed, steps):
    r = solve(n, seed, selector=selector)
    assert r.solved and r.steps == steps and r.extra["restarts"] == 0


def test_conflict_tracker_matches_board():
    rng = random.Random(1)
    rows = [rng.randrange(10) for _ in range(10)]
    tracker = ConflictTracker.from_rows(rows)
    from nqueens.board import Board
    # every conflict is counted from both queens involved
    assert sum(tracker.conflict_vector()) == 2 * Board.from_columns(rows).count_attacking_pairs()


@pytest.mark.parametrize("n", [8, 30, 100])
def test_greedy_initializer_beats_random(n):
    rng = random.Random(3)
    def conflicts(init):
        return sum(ConflictTracker.from_rows(init.build(n, rng)).conflict_vector())
    assert conflicts(GreedyInitializer()) < conflicts(RandomInitializer())


@pytest.mark.parametrize("selector", list(SELECTORS))
@pytest.mark.parametrize("initializer", ["random", "greedy"])
@pytest.mark.parametrize("n", [8, 16])
def test_selectors_and_initializers_solve(selector, initializer, n):
    # Without restarts a single run may stall; require most seeds to succeed.
    results = [solve(n, s, selector=selector, initializer=initializer) for s in range(10)]
    assert sum(r.solved for r in results) >= 6
    assert all(r.board.is_valid() for r in results if r.solved)


@pytest.mark.parametrize("selector", list(SELECTORS))
@pytest.mark.parametrize("initializer", ["random", "greedy"])
def test_restarts_always_solve_small_boards(selector, initializer):
    for n in (8, 12):
        for s in range(10):
            r = solve(n, s, selector=selector, initializer=initializer,
                      restart_steps_factor=10)
            assert r.solved and r.board.is_valid()


def test_restart_budget_is_respected():
    # Impossible board (N=3): the solver must stop at the total budget.
    r = MinConflictsSolver(max_steps_factor=10, restart_steps_factor=2, seed=0).solve(3)
    assert not r.solved and r.steps == 30 and r.extra["restarts"] >= 4


def test_reproducible():
    a = solve(16, 5, restart_steps_factor=5, initializer="greedy")
    b = solve(16, 5, restart_steps_factor=5, initializer="greedy")
    assert a.steps == b.steps and a.board.queens == b.board.queens


def test_unknown_names_are_rejected():
    with pytest.raises(ValueError):
        build_min_conflicts(MinConflictsConfig(selector="nope"))
