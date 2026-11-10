"""Factory: build configured solvers from plain names / settings.

Keeps the CLI and the experiments independent of concrete classes: they only
deal with names ("pairwise", "greedy", ...) and `MinConflictsConfig`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .amo import AMO_ENCODERS
from .solvers.initializers import INITIALIZERS
from .solvers.min_conflicts import MinConflictsSolver
from .solvers.sat_solver import SATSolver
from .solvers.selectors import SELECTORS


def _lookup(registry: dict, name: str, what: str):
    """Instantiate registry[name] or fail with the list of valid names."""
    if name not in registry:
        raise ValueError(f"unknown {what} '{name}'; choose from {sorted(registry)}")
    return registry[name]()


def build_sat(encoding: str = "pairwise", column_alo: bool = False,
              time_limit_s: Optional[float] = None) -> SATSolver:
    """SAT solver using the named AMO encoding ('pairwise' = baseline)."""
    return SATSolver(_lookup(AMO_ENCODERS, encoding, "encoding"), column_alo,
                     time_limit_s)


@dataclass(frozen=True)
class MinConflictsConfig:
    """Declarative description of one Min-Conflicts variant.

    Defaults describe the baseline: random start, random variable selection,
    a single attempt (no restarts).
    """
    selector: str = "random"
    initializer: str = "random"
    max_steps_factor: int = 100
    restart_steps_factor: Optional[int] = None   # None = no restarts


def build_min_conflicts(config: MinConflictsConfig,
                        seed: Optional[int] = None) -> MinConflictsSolver:
    """Min-Conflicts solver for `config`, with its own seeded RNG."""
    return MinConflictsSolver(
        selector=_lookup(SELECTORS, config.selector, "selector"),
        initializer=_lookup(INITIALIZERS, config.initializer, "initializer"),
        max_steps_factor=config.max_steps_factor,
        restart_steps_factor=config.restart_steps_factor,
        seed=seed)
