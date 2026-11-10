"""Dynamic Plugin Loader & Sandboxed Adapter for External Student Group Algorithms (R3).

Allows other student groups to drop a `.py` file into `external_agents/` (or load it
from the GUI/CLI) and compete in the exact same game environment.

Supported External Agent Formats:
1. Class inheriting from `BaseAgent` (or any class with `get_action(self, state)` or
   `choose_action(self, state)`).
2. Standalone module function `get_action(state)` or `choose_action(state)`.

The adapter passes a defensive clone of `GameState` (or `state.to_dict()` if the
external function expects a dict) so external code can never mutate the live board,
and normalizes returned strings ("MOVE_UP", "FIRE", etc.) or `Action` enums.
"""
from __future__ import annotations

import importlib.util
import inspect
import os
import time
from typing import Any, Callable, Dict, Optional

from ..core.state import GameState
from ..core.types import Action, SearchMetrics
from .base import BaseAgent

_STRING_TO_ACTION: Dict[str, Action] = {
    "MOVE_UP": Action.MOVE_UP,
    "UP": Action.MOVE_UP,
    "MOVE_DOWN": Action.MOVE_DOWN,
    "DOWN": Action.MOVE_DOWN,
    "MOVE_LEFT": Action.MOVE_LEFT,
    "LEFT": Action.MOVE_LEFT,
    "MOVE_RIGHT": Action.MOVE_RIGHT,
    "RIGHT": Action.MOVE_RIGHT,
    "FIRE": Action.FIRE,
    "SHOOT": Action.FIRE,
    "STAY": Action.STAY,
    "WAIT": Action.STAY,
    "NONE": Action.STAY,
}


def normalize_action(raw: Any) -> Action:
    """Convert an Action enum or string name into a validated Action enum."""
    if isinstance(raw, Action):
        return raw
    if isinstance(raw, str):
        key = raw.strip().upper()
        if key in _STRING_TO_ACTION:
            return _STRING_TO_ACTION[key]
    if hasattr(raw, "name") and isinstance(raw.name, str):
        key = raw.name.strip().upper()
        if key in _STRING_TO_ACTION:
            return _STRING_TO_ACTION[key]
    if hasattr(raw, "value") and isinstance(raw.value, str):
        key = raw.value.strip().upper()
        if key in _STRING_TO_ACTION:
            return _STRING_TO_ACTION[key]
    raise ValueError(f"Invalid action returned by external agent: {raw!r}")


class SandboxedAgentAdapter(BaseAgent):
    """Wraps an external student agent with state isolation, normalization, and fault tolerance."""

    def __init__(
        self,
        name: str,
        callable_fn: Callable[[Any], Any],
        pass_dict: bool = False,
        fallback_action: Action = Action.STAY,
    ) -> None:
        super().__init__(name=name)
        self._callable = callable_fn
        self._pass_dict = pass_dict
        self._fallback = fallback_action

    def get_action(self, state: GameState) -> Action:
        t0 = time.perf_counter()
        # Defensive copy so external code cannot tamper with the authoritative GameState
        safe_state = state.to_dict() if self._pass_dict else state.clone()
        try:
            raw_action = self._callable(safe_state)
            action = normalize_action(raw_action)
        except Exception:
            # If the external agent throws or returns garbage, fall back safely to STAY
            action = self._fallback

        elapsed = time.perf_counter() - t0
        self.last_metrics = SearchMetrics(
            algorithm=self.name,
            chosen_action=action,
            score=0.0,
            depth_reached=0,
            nodes_explored=1,
            time_s=elapsed,
        )
        return action


class PluginLoader:
    """Dynamically loads external student group algorithms from Python files."""

    @classmethod
    def load_from_file(cls, filepath: str, custom_name: Optional[str] = None) -> BaseAgent:
        """Load an external agent from `filepath` and wrap it in SandboxedAgentAdapter."""
        abs_path = os.path.abspath(filepath)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"External agent file not found: {abs_path}")

        mod_name = f"ext_agent_{os.path.splitext(os.path.basename(abs_path))[0]}"
        spec = importlib.util.spec_from_file_location(mod_name, abs_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create module spec for {abs_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        agent_name = custom_name or getattr(
            module, "AGENT_NAME", os.path.splitext(os.path.basename(abs_path))[0]
        )
        pass_dict = bool(getattr(module, "USE_DICT_STATE", False))

        # 1. Look for a class implementing get_action or choose_action
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is BaseAgent or obj is SandboxedAgentAdapter:
                continue
            if obj.__module__ != module.__name__:
                continue
            if hasattr(obj, "get_action") or hasattr(obj, "choose_action"):
                instance = obj()
                method = getattr(instance, "get_action", None) or getattr(instance, "choose_action")
                inst_name = getattr(instance, "name", agent_name)
                return SandboxedAgentAdapter(
                    name=f"Plugin:{inst_name}",
                    callable_fn=method,
                    pass_dict=pass_dict,
                )

        # 2. Look for a module-level function get_action(state) or choose_action(state)
        for fn_name in ("get_action", "choose_action"):
            fn = getattr(module, fn_name, None)
            if callable(fn):
                return SandboxedAgentAdapter(
                    name=f"Plugin:{agent_name}",
                    callable_fn=fn,
                    pass_dict=pass_dict,
                )

        raise ValueError(
            f"Plugin '{abs_path}' must define a class or function with `get_action(state)` or `choose_action(state)`."
        )

    @classmethod
    def discover_directory(cls, directory: str) -> Dict[str, str]:
        """Return `{plugin_key: filepath}` for all valid `.py` files in `directory`."""
        discovered: Dict[str, str] = {}
        if not os.path.isdir(directory):
            return discovered
        for fname in sorted(os.listdir(directory)):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            fpath = os.path.join(directory, fname)
            key = f"plugin:{os.path.splitext(fname)[0]}"
            discovered[key] = fpath
        return discovered
