"""Headless smoke & integration tests for the Requirement 3 PyGame GUI."""
from __future__ import annotations

import os

import pygame
import pytest

from tank_battle.core.types import Action
from tank_battle.gui.app import TankBattleApp


@pytest.fixture(autouse=True)
def headless_pygame(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    yield
    pygame.quit()


def test_pygame_gui_initializes_and_renders_ai_vs_ai():
    ext_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_agents")
    app = TankBattleApp(
        external_dir=ext_dir,
        initial_p1="heuristic_alphabeta",
        initial_p2="alphabeta",
        initial_map="skirmish",
        initial_depth=2,
    )
    app.render_frame()
    assert app.state.turn == 0

    # Step 2 turns (Player 1 then Player 2)
    app.step_once()
    assert app.state.turn == 1
    assert app.last_metrics[1] is not None

    app.step_once()
    assert app.state.turn == 2
    assert app.last_metrics[2] is not None
    app.render_frame()


def test_pygame_gui_human_and_plugin_integration():
    ext_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "external_agents")
    app = TankBattleApp(
        external_dir=ext_dir,
        initial_p1="human",
        initial_p2="plugin:sample_student_agent",
        initial_map="endgame",
        initial_depth=2,
    )
    assert app.is_human_turn() is True

    # Human executes MOVE_LEFT on Turn 1
    app.step_once(human_action=Action.MOVE_LEFT)
    assert app.state.turn == 1
    assert app.is_human_turn() is False

    # External student plugin executes Turn 2
    app.step_once()
    assert app.state.turn == 2
    app.render_frame()
