"""Reproducible tactical benchmark scenarios for Requirement 2 experiments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from ..core.maps import MapBuilder
from ..core.state import GameState


@dataclass(frozen=True)
class BenchmarkScenario:
    """A named, reproducible game scenario for comparing search configurations."""
    key: str
    title: str
    description: str
    builder: Callable[[], GameState]


BENCHMARK_SCENARIOS: Dict[str, BenchmarkScenario] = {
    "endgame": BenchmarkScenario(
        key="endgame",
        title="Endgame Duel (Close Quarters, 1-HP Tanks)",
        description="Both tanks are aligned in column 3 with 1 HP remaining; terminal states exist within 2-4 ply.",
        builder=MapBuilder.endgame_duel,
    ),
    "dodge": BenchmarkScenario(
        key="dodge",
        title="Incoming Bullet Evasion (Emergency Dodge)",
        description="An enemy speed-3 bullet at (3,3) is heading DOWN toward Tank 1 at (5,3) with 1 HP.",
        builder=MapBuilder.bullet_dodge_scenario,
    ),
    "skirmish": BenchmarkScenario(
        key="skirmish",
        title="Open Skirmish (9x9 Mid-Game Positioning)",
        description="Open 9x9 arena with light cover, testing heuristic guidance when terminal states are beyond search horizon.",
        builder=MapBuilder.open_skirmish,
    ),
    "standard": BenchmarkScenario(
        key="standard",
        title="Standard Battle City Arena (11x11 Opening)",
        description="Full 11x11 symmetric arena with base brick shields and midfield cover.",
        builder=MapBuilder.standard_arena,
    ),
}
