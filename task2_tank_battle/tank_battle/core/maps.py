"""Predefined maps and tactical test scenarios for the Tank Battle Game."""
from __future__ import annotations

from typing import Callable, Dict, Tuple

from .entities import Base, Bullet, Tank
from .state import GameState
from .types import BASE_INITIAL_HP, Direction, TANK_INITIAL_HP, WALL_INITIAL_HP


class MapBuilder:
    """Factory for standard game arenas and reproducible benchmark scenarios."""

    @staticmethod
    def standard_arena(width: int = 11, height: int = 11) -> GameState:
        """Symmetric 11x11 Battle City arena with bases, shielding walls, and center cover."""
        mid_c = width // 2
        mid_r = height // 2

        # Player 1 at bottom, Player 2 at top
        base1 = Base(player_id=1, row=height - 1, col=mid_c, hp=BASE_INITIAL_HP)
        base2 = Base(player_id=2, row=0, col=mid_c, hp=BASE_INITIAL_HP)

        tank1 = Tank(player_id=1, row=height - 2, col=mid_c - 2, direction=Direction.UP, hp=TANK_INITIAL_HP)
        tank2 = Tank(player_id=2, row=1, col=mid_c + 2, direction=Direction.DOWN, hp=TANK_INITIAL_HP)

        walls: Dict[Tuple[int, int], int] = {}

        # Base protective brick shields (HP = 3)
        for dc in (-1, 0, 1):
            walls[(height - 2, mid_c + dc)] = WALL_INITIAL_HP
            walls[(1, mid_c + dc)] = WALL_INITIAL_HP
        walls[(height - 1, mid_c - 1)] = WALL_INITIAL_HP
        walls[(height - 1, mid_c + 1)] = WALL_INITIAL_HP
        walls[(0, mid_c - 1)] = WALL_INITIAL_HP
        walls[(0, mid_c + 1)] = WALL_INITIAL_HP

        # Midfield tactical brick cover
        for c in (2, 3, width - 4, width - 3):
            walls[(mid_r - 1, c)] = WALL_INITIAL_HP
            walls[(mid_r + 1, c)] = WALL_INITIAL_HP
        walls[(mid_r, mid_c)] = WALL_INITIAL_HP

        return GameState(
            width=width,
            height=height,
            tanks={1: tank1, 2: tank2},
            bases={1: base1, 2: base2},
            walls=walls,
            current_player=1,
        )

    @staticmethod
    def open_skirmish(width: int = 9, height: int = 9) -> GameState:
        """Compact 9x9 fast-action arena with light cover."""
        mid_c = width // 2
        mid_r = height // 2

        base1 = Base(player_id=1, row=height - 1, col=mid_c, hp=BASE_INITIAL_HP)
        base2 = Base(player_id=2, row=0, col=mid_c, hp=BASE_INITIAL_HP)

        tank1 = Tank(player_id=1, row=height - 2, col=2, direction=Direction.UP, hp=TANK_INITIAL_HP)
        tank2 = Tank(player_id=2, row=1, col=width - 3, direction=Direction.DOWN, hp=TANK_INITIAL_HP)

        walls: Dict[Tuple[int, int], int] = {
            (height - 2, mid_c): WALL_INITIAL_HP,
            (1, mid_c): WALL_INITIAL_HP,
            (mid_r, mid_c - 2): WALL_INITIAL_HP,
            (mid_r, mid_c + 2): WALL_INITIAL_HP,
        }

        return GameState(
            width=width,
            height=height,
            tanks={1: tank1, 2: tank2},
            bases={1: base1, 2: base2},
            walls=walls,
            current_player=1,
        )

    @staticmethod
    def fortress_maze(width: int = 11, height: int = 11) -> GameState:
        """Corridor-heavy map emphasizing wall destruction and flank control."""
        state = MapBuilder.standard_arena(width, height)
        mid_r = height // 2
        for c in range(1, width - 1, 2):
            state.walls[(mid_r, c)] = WALL_INITIAL_HP
        return state

    @staticmethod
    def endgame_duel() -> GameState:
        """Close-quarters tactical scenario with low HP where terminal states are within 2-4 ply."""
        width, height = 7, 7
        base1 = Base(player_id=1, row=6, col=0, hp=2)
        base2 = Base(player_id=2, row=0, col=6, hp=2)

        tank1 = Tank(player_id=1, row=4, col=3, direction=Direction.UP, hp=1)
        tank2 = Tank(player_id=2, row=1, col=3, direction=Direction.DOWN, hp=1)

        walls: Dict[Tuple[int, int], int] = {
            (3, 1): 1,
            (3, 5): 1,
        }
        return GameState(
            width=width,
            height=height,
            tanks={1: tank1, 2: tank2},
            bases={1: base1, 2: base2},
            walls=walls,
            current_player=1,
        )

    @staticmethod
    def bullet_dodge_scenario() -> GameState:
        """Tactical test: an enemy bullet is 2 cells away heading straight at Tank 1."""
        width, height = 7, 7
        base1 = Base(player_id=1, row=6, col=6, hp=9)
        base2 = Base(player_id=2, row=0, col=0, hp=9)

        tank1 = Tank(player_id=1, row=5, col=3, direction=Direction.RIGHT, hp=1)
        tank2 = Tank(player_id=2, row=1, col=2, direction=Direction.DOWN, hp=4)

        incoming_bullet = Bullet(owner_id=2, row=3, col=3, direction=Direction.DOWN)
        return GameState(
            width=width,
            height=height,
            tanks={1: tank1, 2: tank2},
            bases={1: base1, 2: base2},
            walls={},
            bullets=[incoming_bullet],
            current_player=1,
        )


MAPS: Dict[str, Callable[[], GameState]] = {
    "standard": MapBuilder.standard_arena,
    "skirmish": MapBuilder.open_skirmish,
    "fortress": MapBuilder.fortress_maze,
    "endgame": MapBuilder.endgame_duel,
    "dodge": MapBuilder.bullet_dodge_scenario,
}
