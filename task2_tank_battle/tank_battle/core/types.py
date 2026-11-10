"""Core enumerations, constants, and data structures for the Tank Battle Game."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Predefined Game Entity Health & Physics Constants (from Assignment Table)
# ---------------------------------------------------------------------------
TANK_INITIAL_HP: int = 6
BASE_INITIAL_HP: int = 9
WALL_INITIAL_HP: int = 3
DAMAGE_PER_HIT: int = 1
BULLET_SPEED: int = 3          # cells per game cycle (processed cell by cell)
MAX_ACTIVE_BULLETS_PER_TANK: int = 1
DEFAULT_MAX_TURNS: int = 200


class Direction(Enum):
    """Cardinal directions on the grid (row_delta, col_delta)."""
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

    @property
    def delta(self) -> Tuple[int, int]:
        return self.value


class Action(Enum):
    """The 06 discrete actions available to a tank entity each turn."""
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    FIRE = "FIRE"
    STAY = "STAY"

    @property
    def direction(self) -> Optional[Direction]:
        """Return corresponding Direction if this is a movement action."""
        return _ACTION_TO_DIR.get(self)


_ACTION_TO_DIR: Dict[Action, Direction] = {
    Action.MOVE_UP: Direction.UP,
    Action.MOVE_DOWN: Direction.DOWN,
    Action.MOVE_LEFT: Direction.LEFT,
    Action.MOVE_RIGHT: Direction.RIGHT,
}


@dataclass
class SearchMetrics:
    """Telemetry recorded by an adversarial search algorithm on a single decision."""
    algorithm: str
    chosen_action: Action
    score: float
    depth_reached: int
    nodes_explored: int
    nodes_pruned: int = 0
    tt_hits: int = 0
    time_s: float = 0.0
    extra: dict = field(default_factory=dict)

    @property
    def elapsed_s(self) -> float:
        return self.time_s

    @property
    def pruning_ratio(self) -> float:
        total = self.nodes_explored + self.nodes_pruned
        return (self.nodes_pruned / total) if total > 0 else 0.0
