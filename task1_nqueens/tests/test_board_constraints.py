"""Board validation and constraint discovery."""
from nqueens.board import Board
from nqueens.constraints import ConstraintGenerator


def test_board_valid_invalid():
    assert Board(4, [(0, 1), (1, 3), (2, 0), (3, 2)]).is_valid()
    bad = Board(4, [(0, 0), (1, 1), (2, 2), (3, 3)])
    assert not bad.is_valid() and bad.count_attacking_pairs() == 6


def test_board_rejects_wrong_queen_count():
    assert not Board(4, [(0, 1), (1, 3), (2, 0)]).is_valid()


def test_constraints_no_duplicate_pairs():
    pairs = [frozenset(p) for ln in ConstraintGenerator(4).lines() for p in ln.pairs()]
    assert len(pairs) == len(set(pairs))
    assert len(pairs) == 76  # 80 clauses - 4 row ALO
