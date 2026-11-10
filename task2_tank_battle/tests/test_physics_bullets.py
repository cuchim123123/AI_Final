"""Unit tests for Tank Battle Game physics, entity health, and cell-by-cell bullet collisions."""
from __future__ import annotations

from tank_battle.core import (
    Action,
    BASE_INITIAL_HP,
    BULLET_SPEED,
     Base,
    Bullet,
    DAMAGE_PER_HIT,
    Direction,
    GameState,
    TANK_INITIAL_HP,
    Tank,
    TransitionEngine,
    WALL_INITIAL_HP,
)


def make_empty_state(width: int = 9, height: int = 9) -> GameState:
    return GameState(
        width=width,
        height=height,
        tanks={
            1: Tank(1, 7, 4, Direction.UP, TANK_INITIAL_HP),
            2: Tank(2, 1, 4, Direction.DOWN, TANK_INITIAL_HP),
        },
        bases={
            1: Base(1, 8, 0, BASE_INITIAL_HP),
            2: Base(2, 0, 8, BASE_INITIAL_HP),
        },
        walls={},
        current_player=1,
    )


def test_predefined_initial_health_and_damage_constants():
    assert TANK_INITIAL_HP == 6
    assert BASE_INITIAL_HP == 9
    assert WALL_INITIAL_HP == 3
    assert DAMAGE_PER_HIT == 1
    assert BULLET_SPEED == 3
    assert len(TransitionEngine.ALL_ACTIONS) == 6


def test_bullet_travels_3_cells_per_cycle_in_open_space():
    state = make_empty_state()
    state.tanks[2].col = 0  # move Tank 2 out of the line of fire
    next_s = TransitionEngine.apply_action(state, Action.FIRE)
    assert len(next_s.bullets) == 1
    # Tank 1 at (7, 4) fired UP -> bullet moved 3 cells: 7 -> 6 -> 5 -> 4
    assert next_s.bullets[0].pos == (4, 4)


def test_bullet_stops_immediately_at_wall_and_never_tunnels():
    state = make_empty_state()
    # Place a wall at (5, 4) (distance 2 from Tank 1 at (7, 4))
    # and place Tank 2 right behind that wall at (4, 4) (distance 3)
    state.walls[(5, 4)] = WALL_INITIAL_HP
    state.tanks[2].row, state.tanks[2].col = 4, 4

    s1 = TransitionEngine.apply_action(state, Action.FIRE)
    # Bullet must hit wall at (5, 4) on step 2, reduce wall HP from 3 to 2, and stop immediately!
    assert len(s1.bullets) == 0
    assert s1.walls[(5, 4)] == 2
    assert s1.tanks[2].hp == TANK_INITIAL_HP  # Tank 2 behind wall is untouched


def test_wall_is_destroyed_after_3_hits():
    state = make_empty_state()
    state.walls[(6, 4)] = 1  # 1 HP remaining
    s1 = TransitionEngine.apply_action(state, Action.FIRE)
    assert (6, 4) not in s1.walls
    assert len(s1.bullets) == 0


def test_tank_and_base_destruction_triggers_terminal_winner():
    state = make_empty_state()
    state.tanks[2].row, state.tanks[2].col = 5, 4  # 2 cells in front of Tank 1
    state.tanks[2].hp = 1

    s1 = TransitionEngine.apply_action(state, Action.FIRE)
    assert s1.tanks[2].hp == 0
    assert s1.is_terminal()
    assert s1.get_winner() == 1
