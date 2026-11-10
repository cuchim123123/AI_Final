"""Unit tests for the 4 Adversarial Search configurations (Minimax, Alpha-Beta, Heuristic)."""
from __future__ import annotations

import pytest

from tank_battle.core import Action, MapBuilder
from tank_battle.factory import build_search_engine


@pytest.mark.parametrize("depth", [1, 2, 3])
def test_minimax_and_alphabeta_return_identical_scores(depth: int):
    state = MapBuilder.endgame_duel()
    mm = build_search_engine("minimax", depth=depth)
    ab = build_search_engine("alphabeta", depth=depth)

    res_mm = mm.search(state)
    res_ab = ab.search(state)

    assert res_mm.score == pytest.approx(res_ab.score)
    assert res_ab.nodes_explored <= res_mm.nodes_explored


@pytest.mark.parametrize("depth", [1, 2, 3])
def test_heuristic_minimax_and_heuristic_alphabeta_return_identical_scores(depth: int):
    state = MapBuilder.open_skirmish()
    hmm = build_search_engine("heuristic_minimax", depth=depth)
    hab = build_search_engine(
        "heuristic_alphabeta",
        depth=depth,
        use_move_ordering=True,
        use_transposition_table=False,  # disable TT to test pure exact alpha-beta equivalence
    )

    res_hmm = hmm.search(state)
    res_hab = hab.search(state)

    assert res_hmm.score == pytest.approx(res_hab.score)
    if depth >= 2:
        assert res_hab.nodes_explored < res_hmm.nodes_explored
    else:
        assert res_hab.nodes_explored <= res_hmm.nodes_explored


def test_endgame_kill_shot_chooses_fire():
    state = MapBuilder.endgame_duel()
    # Tank 1 at (4,3) facing UP toward Tank 2 at (1,3) with 1 HP (distance 3 = 1 cycle hit!)
    engine = build_search_engine("heuristic_alphabeta", depth=2)
    metrics = engine.search(state)
    assert metrics.chosen_action == Action.FIRE
    assert metrics.score > 9000.0


def test_bullet_dodge_scenario_evades_incoming_bullet():
    state = MapBuilder.bullet_dodge_scenario()
    # Enemy bullet at (3,3) moving DOWN toward Tank 1 at (5,3) with 1 HP
    engine = build_search_engine("heuristic_alphabeta", depth=2)
    metrics = engine.search(state)
    # Staying on column 3 (STAY, MOVE_UP, MOVE_DOWN) results in immediate death
    assert metrics.chosen_action in (Action.MOVE_LEFT, Action.MOVE_RIGHT)
