"""Transposition Table for caching evaluated game states during Alpha-Beta search."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional

from ..core.types import Action


class BoundFlag(IntEnum):
    EXACT = 0
    LOWERBOUND = 1
    UPPERBOUND = 2


@dataclass
class TTEntry:
    depth: int
    flag: BoundFlag
    value: float
    best_action: Optional[Action]


class TranspositionTable:
    """Bounded dictionary cache storing minimax search results keyed by canonical state_key."""

    def __init__(self, max_size: int = 100_000) -> None:
        self.max_size = max_size
        self._table: Dict[tuple, TTEntry] = {}
        self.hits: int = 0

    def clear(self) -> None:
        self._table.clear()
        self.hits = 0

    def lookup(self, key: tuple) -> Optional[TTEntry]:
        entry = self._table.get(key)
        if entry is not None:
            self.hits += 1
        return entry

    def store(
        self,
        key: tuple,
        depth: int,
        flag: BoundFlag,
        value: float,
        best_action: Optional[Action],
    ) -> None:
        if len(self._table) >= self.max_size:
            self._table.clear()
        existing = self._table.get(key)
        if existing is None or depth >= existing.depth:
            self._table[key] = TTEntry(depth=depth, flag=flag, value=value, best_action=best_action)
