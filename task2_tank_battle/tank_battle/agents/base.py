"""Abstract Base Agent interface (Strategy pattern) for all tank controllers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..core.state import GameState
from ..core.types import Action, SearchMetrics


class BaseAgent(ABC):
    """Strategy interface implemented by all AI, Human, and External Plugin agents."""

    def __init__(self, name: str = "Agent") -> None:
        self.name = name
        self.last_metrics: Optional[SearchMetrics] = None

    @abstractmethod
    def get_action(self, state: GameState) -> Action:
        """Select and return one of the 06 legal Actions for `state.current_player`."""

    def reset(self) -> None:
        """Optional hook called at the start of a new match."""
        self.last_metrics = None
