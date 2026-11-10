"""Adversarial Search Agent wrapping AdversarialSearchEngine."""
from __future__ import annotations

from ..core.state import GameState
from ..core.types import Action
from ..search.minimax import AdversarialSearchEngine
from .base import BaseAgent


class SearchAgent(BaseAgent):
    """Tank controller driven by Minimax / Alpha-Beta / Heuristic Search."""

    def __init__(self, engine: AdversarialSearchEngine) -> None:
        super().__init__(name=engine.name)
        self.engine = engine

    def get_action(self, state: GameState) -> Action:
        key = AdversarialSearchEngine.progress_key(state, state.current_player)
        self.engine.position_history[key] = self.engine.position_history.get(key, 0) + 1
        metrics = self.engine.search(state)
        self.last_metrics = metrics
        return metrics.chosen_action

    def reset(self) -> None:
        super().reset()
        self.engine.tt.clear()
        self.engine.position_history.clear()
