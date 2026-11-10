"""Named sets of solver variants for the experiments (built via the factory)."""
from __future__ import annotations

from functools import partial
from typing import Dict, Optional, Sequence, Tuple

from ..factory import MinConflictsConfig, build_min_conflicts, build_sat
from .runner import SATFactory, SeededFactory


def sat_variants(encodings: Sequence[str], column_alo: bool = False,
                 time_limit_s: Optional[float] = None) -> Dict[str, SATFactory]:
    """One SAT variant per AMO encoding name (each solve capped at time_limit_s)."""
    return {enc: partial(build_sat, enc, column_alo, time_limit_s)
            for enc in encodings}


def config_variant(config: MinConflictsConfig) -> SeededFactory:
    """A seed -> solver factory for one Min-Conflicts configuration."""
    return partial(build_min_conflicts, config)


def selector_variants(selectors: Sequence[str],
                      base: MinConflictsConfig) -> Dict[str, SeededFactory]:
    """Compare variable-selection heuristics; everything else comes from `base`."""
    return {sel: config_variant(MinConflictsConfig(
                selector=sel, initializer=base.initializer,
                max_steps_factor=base.max_steps_factor,
                restart_steps_factor=base.restart_steps_factor))
            for sel in selectors}


# Each optimisation = overrides applied on top of the baseline configuration.
# Name -> (initializer, uses_restarts)
_OPTIMIZATIONS = {
    "baseline": ("random", False),
    "greedy-init": ("greedy", False),
    "restarts": ("random", True),
    "greedy+restarts": ("greedy", True),
}


def optimization_variants(selectors: Sequence[str], max_steps_factor: int,
                          restart_steps_factor: int
                          ) -> Tuple[Dict[str, SeededFactory], Dict[str, str]]:
    """Baseline vs each optimisation, repeated for every selector.

    Variant names look like "max+greedy-init". Returns (variants, baseline_of)
    where baseline_of maps each variant to the plain variant with the *same
    selector* (e.g. "max+greedy-init" -> "max+baseline").
    """
    variants: Dict[str, SeededFactory] = {}
    baseline_of: Dict[str, str] = {}
    for sel in selectors:
        for opt, (init, restarts) in _OPTIMIZATIONS.items():
            name = f"{sel}+{opt}"
            variants[name] = config_variant(MinConflictsConfig(
                selector=sel, initializer=init, max_steps_factor=max_steps_factor,
                restart_steps_factor=restart_steps_factor if restarts else None))
            baseline_of[name] = f"{sel}+baseline"
    return variants, baseline_of
