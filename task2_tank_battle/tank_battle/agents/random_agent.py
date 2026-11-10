"""Simple baseline agents (RandomAgent and RuleBasedGreedyAgent)."""
from __future__ import annotations

import random
import time
from typing import Optional

from ..core.rules import TransitionEngine
from ..core.state import GameState
from ..core.types import Action, SearchMetrics
from .base import BaseAgent


class RandomAgent(BaseAgent):
    """Selects a uniformly random action from the 06 available actions."""

    def __init__(self, seed: Optional[int] = None) -> None:
        super().__init__(name="RandomAgent")
        self.rng = random.Random(seed)

    def get_action(self, state: GameState) -> Action:
        t0 = time.perf_counter()
        act = self.rng.choice(TransitionEngine.ALL_ACTIONS)
        self.last_metrics = SearchMetrics(
            algorithm=self.name,
            chosen_action=act,
            score=0.0,
            depth_reached=0,
            nodes_explored=1,
            time_s=time.perf_counter() - t0,
        )
        return act
