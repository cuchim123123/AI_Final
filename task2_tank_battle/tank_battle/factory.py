"""Factory for building the 4 required Adversarial Search configurations & external plugins."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .agents.base import BaseAgent
from .agents.minimax_agent import SearchAgent
from .agents.plugin_loader import PluginLoader
from .agents.random_agent import RandomAgent
from .search.evaluators import BasicEvaluator, StateEvaluator, TacticalHeuristicEvaluator
from .search.minimax import AdversarialSearchEngine


@dataclass(frozen=True)
class SearchConfig:
    """Declarative specification for an adversarial search configuration."""
    key: str
    display_name: str
    use_alpha_beta: bool
    use_heuristic: bool
    default_depth: int = 3
    use_move_ordering: bool = False
    use_transposition_table: bool = False
    use_iterative_deepening: bool = False
    time_limit_s: Optional[float] = None


# ---------------------------------------------------------------------------
# The 4 Core Configurations Required by Requirement 2 (+ Optimized Real-Time)
# ---------------------------------------------------------------------------
FOUR_REQUIRED_CONFIGS: Dict[str, SearchConfig] = {
    "minimax": SearchConfig(
        key="minimax",
        display_name="1. Minimax Search",
        use_alpha_beta=False,
        use_heuristic=False,
        default_depth=3,
    ),
    "alphabeta": SearchConfig(
        key="alphabeta",
        display_name="2. Alpha-Beta Search",
        use_alpha_beta=True,
        use_heuristic=False,
        default_depth=3,
    ),
    "heuristic_minimax": SearchConfig(
        key="heuristic_minimax",
        display_name="3. Heuristic Minimax Search",
        use_alpha_beta=False,
        use_heuristic=True,
        default_depth=3,
    ),
    "heuristic_alphabeta": SearchConfig(
        key="heuristic_alphabeta",
        display_name="4. Heuristic Minimax + Alpha-Beta",
        use_alpha_beta=True,
        use_heuristic=True,
        default_depth=3,
        use_move_ordering=True,
        use_transposition_table=True,
    ),
}


def build_evaluator(use_heuristic: bool) -> StateEvaluator:
    return TacticalHeuristicEvaluator() if use_heuristic else BasicEvaluator()


def build_search_engine(
    config_key: str,
    depth: Optional[int] = None,
    use_move_ordering: Optional[bool] = None,
    use_transposition_table: Optional[bool] = None,
    use_iterative_deepening: Optional[bool] = None,
    time_limit_s: Optional[float] = None,
) -> AdversarialSearchEngine:
    """Instantiate one of the 4 required search engines with optional overrides."""
    if config_key not in FOUR_REQUIRED_CONFIGS:
        raise ValueError(
            f"Unknown search config '{config_key}'; choose from {list(FOUR_REQUIRED_CONFIGS)}"
        )
    cfg = FOUR_REQUIRED_CONFIGS[config_key]
    d = depth if depth is not None else cfg.default_depth
    mo = use_move_ordering if use_move_ordering is not None else cfg.use_move_ordering
    tt = use_transposition_table if use_transposition_table is not None else cfg.use_transposition_table
    id_flag = (
        use_iterative_deepening
        if use_iterative_deepening is not None
        else cfg.use_iterative_deepening
    )
    t_lim = time_limit_s if time_limit_s is not None else cfg.time_limit_s

    return AdversarialSearchEngine(
        name=f"{cfg.display_name} (d={d})",
        evaluator=build_evaluator(cfg.use_heuristic),
        max_depth=d,
        use_alpha_beta=cfg.use_alpha_beta,
        use_move_ordering=mo,
        use_transposition_table=tt,
        use_iterative_deepening=id_flag,
        time_limit_s=t_lim,
    )


def build_agent(
    spec: str,
    depth: Optional[int] = None,
    external_dir: str = "external_agents",
) -> BaseAgent:
    """Build an agent from a configuration key, 'random', or 'plugin:<filename>' / path."""
    if spec == "random":
        return RandomAgent()
    if spec in FOUR_REQUIRED_CONFIGS:
        return SearchAgent(build_search_engine(spec, depth=depth))
    if spec.startswith("plugin:"):
        discovered = PluginLoader.discover_directory(external_dir)
        if spec in discovered:
            return PluginLoader.load_from_file(discovered[spec])
        plugin_path = spec.split(":", 1)[1]
        return PluginLoader.load_from_file(plugin_path)
    if spec.endswith(".py"):
        return PluginLoader.load_from_file(spec)
    raise ValueError(f"Unknown agent specification: {spec!r}")
