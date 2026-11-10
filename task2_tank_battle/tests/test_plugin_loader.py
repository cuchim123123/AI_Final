"""Unit tests for the External Student Group Algorithm Plugin Loader & Sandbox (R3)."""
from __future__ import annotations

import os
from tank_battle.agents import PluginLoader
from tank_battle.core import Action, MapBuilder


def test_load_sample_student_agent_and_execute():
    sample_path = os.path.join(
        os.path.dirname(__file__), "..", "external_agents", "sample_student_agent.py"
    )
    agent = PluginLoader.load_from_file(sample_path)
    state = MapBuilder.standard_arena()
    action = agent.get_action(state)
    assert isinstance(action, Action)
    assert agent.last_metrics is not None


def test_plugin_sandbox_prevents_state_mutation(tmp_path):
    malicious_code = '''
def get_action(state):
    # Attempt to cheat by killing enemy tank and giving self 999 HP
    state.tanks[1].hp = 999
    state.tanks[2].hp = 0
    return "FIRE"
'''
    plugin_file = tmp_path / "cheater_agent.py"
    plugin_file.write_text(malicious_code, encoding="utf-8")

    agent = PluginLoader.load_from_file(str(plugin_file))
    state = MapBuilder.standard_arena()
    act = agent.get_action(state)
    assert act == Action.FIRE
    # Authoritative game state must be completely untouched!
    assert state.tanks[1].hp == 6
    assert state.tanks[2].hp == 6


def test_plugin_invalid_return_falls_back_to_stay(tmp_path):
    broken_code = '''
def get_action(state):
    return "TELEPORT_TO_MOON"
'''
    plugin_file = tmp_path / "broken_agent.py"
    plugin_file.write_text(broken_code, encoding="utf-8")

    agent = PluginLoader.load_from_file(str(plugin_file))
    state = MapBuilder.standard_arena()
    act = agent.get_action(state)
    assert act == Action.STAY
