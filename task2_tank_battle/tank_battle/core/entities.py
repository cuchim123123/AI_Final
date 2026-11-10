"""Game entities (Tank, Base, Bullet) with fast cloning for tree search."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .types import BASE_INITIAL_HP, Direction, TANK_INITIAL_HP


@dataclass
class Tank:
    """Represents a player's tank on the chessboard-like grid."""
    player_id: int
    row: int
    col: int
    direction: Direction
    hp: int = TANK_INITIAL_HP

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.row, self.col)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def clone(self) -> "Tank":
        return Tank(self.player_id, self.row, self.col, self.direction, self.hp)

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "row": self.row,
            "col": self.col,
            "direction": self.direction.name,
            "hp": self.hp,
        }


@dataclass
class Base:
    """Represents a player's stationary headquarters base."""
    player_id: int
    row: int
    col: int
    hp: int = BASE_INITIAL_HP

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.row, self.col)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def clone(self) -> "Base":
        return Base(self.player_id, self.row, self.col, self.hp)

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "row": self.row,
            "col": self.col,
            "hp": self.hp,
        }


@dataclass
class Bullet:
    """Represents a projectile traveling at 3 cells per cycle."""
    owner_id: int
    row: int
    col: int
    direction: Direction

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.row, self.col)

    def clone(self) -> "Bullet":
        return Bullet(self.owner_id, self.row, self.col, self.direction)

    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "row": self.row,
            "col": self.col,
            "direction": self.direction.name,
        }
