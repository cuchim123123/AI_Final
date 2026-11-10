"""Interactive PyGame GUI application for operating the Tank Battle Game (Requirement 3)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import pygame

from ..agents.base import BaseAgent
from ..agents.plugin_loader import PluginLoader
from ..core.maps import MAPS
from ..core.rules import TransitionEngine
from ..core.state import GameState
from ..core.types import Action, BASE_INITIAL_HP, SearchMetrics, TANK_INITIAL_HP
from ..factory import FOUR_REQUIRED_CONFIGS, build_agent
from .renderer import (
    ArenaRenderer,
    BG_COLOR,
    HP_CRIT,
    HP_GOOD,
    HP_WARN,
    P1_PRIMARY,
    P2_PRIMARY,
    TEXT_WHITE,
)

PANEL_BG = (30, 41, 59)
CARD_BG = (15, 23, 42)
CARD_BORDER = (51, 65, 85)
BTN_BG = (51, 65, 85)
BTN_HOVER = (71, 85, 105)
BTN_ACTIVE = (14, 165, 233)
TEXT_MUTED = (148, 163, 184)


@dataclass
class UIButton:
    """Clickable rectangular button in the PyGame sidebar HUD."""
    rect: pygame.Rect
    label: str
    on_click: Callable[[], None]
    accent_color: Optional[tuple[int, int, int]] = None


class TankBattleApp:
    """PyGame GUI Application for Tank Battle & External Student Agent Integration."""

    WINDOW_W = 1180
    WINDOW_H = 740
    SIDEBAR_X = 730
    SIDEBAR_W = 435

    def __init__(
        self,
        external_dir: str = "external_agents",
        initial_p1: str = "heuristic_alphabeta",
        initial_p2: str = "alphabeta",
        initial_map: str = "standard",
        initial_depth: int = 3,
    ) -> None:
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.WINDOW_W, self.WINDOW_H))
        pygame.display.set_caption(
            "Task 2: Adversarial Search — Tank Battle Game (Minimax / Alpha-Beta / Heuristic / Plugins)"
        )
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_sec = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_body = pygame.font.SysFont("Consolas", 13)
        self.font_bold = pygame.font.SysFont("Consolas", 13, bold=True)

        self.external_dir = external_dir
        self.controller_specs: List[str] = []
        self.reload_plugins(reset_match=False)

        self.p1_idx = self._find_spec_index(initial_p1, default=0)
        self.p2_idx = self._find_spec_index(initial_p2, default=1)
        self.map_keys = list(MAPS.keys())
        self.map_idx = self.map_keys.index(initial_map) if initial_map in self.map_keys else 0
        self.depths = [1, 2, 3, 4]
        self.depth_idx = self.depths.index(initial_depth) if initial_depth in self.depths else 2

        self.speeds = [("1x (3 t/s)", 330), ("2x (6 t/s)", 165), ("4x (12 t/s)", 80), ("MAX (Fast)", 15)]
        self.speed_idx = 1

        self.arena_renderer = ArenaRenderer(pygame.Rect(16, 16, 700, 708))
        self.buttons: List[UIButton] = []
        self._build_buttons()

        self.state: GameState = MAPS[self.map_keys[self.map_idx]]()
        self.agents: Dict[int, Optional[BaseAgent]] = {1: None, 2: None}
        self.last_metrics: Dict[int, Optional[SearchMetrics]] = {1: None, 2: None}
        self.last_actions: Dict[int, str] = {1: "—", 2: "—"}
        self.action_log: List[str] = []
        self.running_sim: bool = False
        self.last_step_tick: int = pygame.time.get_ticks()

        self.reset_match()

    def _find_spec_index(self, spec: str, default: int = 0) -> int:
        if spec in self.controller_specs:
            return self.controller_specs.index(spec)
        return min(default, max(0, len(self.controller_specs) - 1))

    def _format_spec_label(self, spec: str) -> str:
        if spec == "human":
            return "Human (Keyboard WASD/Space)"
        if spec == "random":
            return "Random Baseline Agent"
        if spec in FOUR_REQUIRED_CONFIGS:
            return FOUR_REQUIRED_CONFIGS[spec].display_name
        return spec

    def reload_plugins(self, reset_match: bool = True) -> None:
        """Scan external_agents/ directory for student group plugins."""
        base_specs = [
            "heuristic_alphabeta",
            "heuristic_minimax",
            "alphabeta",
            "minimax",
            "human",
            "random",
        ]
        discovered = PluginLoader.discover_directory(self.external_dir)
        plugin_specs = sorted(discovered.keys())
        self.controller_specs = base_specs + plugin_specs
        if reset_match and hasattr(self, "state"):
            self.p1_idx %= len(self.controller_specs)
            self.p2_idx %= len(self.controller_specs)
            self.reset_match()

    def _build_buttons(self) -> None:
        sx = self.SIDEBAR_X + 14
        w_full = self.SIDEBAR_W - 28
        w_half = (w_full - 10) // 2

        self.buttons = [
            UIButton(pygame.Rect(sx, 60, w_full, 30), "P1 Controller", self._cycle_p1, P1_PRIMARY),
            UIButton(pygame.Rect(sx, 112, w_full, 30), "P2 Controller", self._cycle_p2, P2_PRIMARY),
            UIButton(pygame.Rect(sx, 154, w_half, 28), "Depth", self._cycle_depth),
            UIButton(pygame.Rect(sx + w_half + 10, 154, w_half, 28), "Map", self._cycle_map),
            UIButton(pygame.Rect(sx, 190, w_half, 32), "Start / Pause [Space]", self.toggle_pause, BTN_ACTIVE),
            UIButton(pygame.Rect(sx + w_half + 10, 190, w_half, 32), "Step 1 Turn [N]", self.step_once),
            UIButton(pygame.Rect(sx, 228, w_half, 28), "Reset Match [R]", self.reset_match),
            UIButton(pygame.Rect(sx + w_half + 10, 228, w_half, 28), "Speed", self._cycle_speed),
            UIButton(pygame.Rect(sx, 262, w_full, 26), "Reload External Student Plugins [P]", lambda: self.reload_plugins(True)),
        ]

    def _cycle_p1(self) -> None:
        self.p1_idx = (self.p1_idx + 1) % len(self.controller_specs)
        self.reset_match()

    def _cycle_p2(self) -> None:
        self.p2_idx = (self.p2_idx + 1) % len(self.controller_specs)
        self.reset_match()

    def _cycle_depth(self) -> None:
        self.depth_idx = (self.depth_idx + 1) % len(self.depths)
        self.reset_match()

    def _cycle_map(self) -> None:
        self.map_idx = (self.map_idx + 1) % len(self.map_keys)
        self.reset_match()

    def _cycle_speed(self) -> None:
        self.speed_idx = (self.speed_idx + 1) % len(self.speeds)

    def toggle_pause(self) -> None:
        if not self.state.is_terminal():
            self.running_sim = not self.running_sim
            self.last_step_tick = pygame.time.get_ticks()

    def reset_match(self) -> None:
        """Reset the arena and instantiate selected P1 and P2 controllers."""
        self.running_sim = False
        map_key = self.map_keys[self.map_idx]
        self.state = MAPS[map_key]()
        depth = self.depths[self.depth_idx]

        for pid, idx in ((1, self.p1_idx), (2, self.p2_idx)):
            spec = self.controller_specs[idx]
            if spec == "human":
                self.agents[pid] = None
            else:
                agent = build_agent(spec, depth=depth, external_dir=self.external_dir)
                agent.reset()
                self.agents[pid] = agent

        self.last_metrics = {1: None, 2: None}
        self.last_actions = {1: "—", 2: "—"}
        self.action_log = [f"Match ready on '{map_key}' (d={depth}). Press SPACE or Step."]

    def is_human_turn(self) -> bool:
        if self.state.is_terminal():
            return False
        return self.agents[self.state.current_player] is None

    def step_once(self, human_action: Optional[Action] = None) -> None:
        """Advance the game by 1 turn using either the active AI agent or `human_action`."""
        if self.state.is_terminal():
            self.running_sim = False
            return

        pid = self.state.current_player
        agent = self.agents[pid]

        if agent is None:
            if human_action is None:
                return
            chosen = human_action
            self.last_metrics[pid] = SearchMetrics(
                algorithm="Human Player",
                chosen_action=chosen,
                score=0.0,
                depth_reached=0,
                nodes_explored=1,
            )
        else:
            chosen = agent.get_action(self.state.clone())
            self.last_metrics[pid] = agent.last_metrics

        self.last_actions[pid] = chosen.value
        TransitionEngine.apply_action_inplace(self.state, chosen, record_events=True)

        m = self.last_metrics[pid]
        t_ms = f"{m.time_s * 1000:.1f}ms" if m else "0ms"
        nodes = m.nodes_explored if m else 1
        log_entry = f"T{self.state.turn:02d} P{pid}: {chosen.value:<10} ({nodes} st, {t_ms})"
        self.action_log.append(log_entry)
        if len(self.action_log) > 6:
            self.action_log = self.action_log[-6:]

        if self.state.is_terminal():
            self.running_sim = False
            w = self.state.get_winner()
            self.action_log.append(f"GAME OVER -> Winner: Player {w}" if w else "GAME OVER -> Draw")

    def render_frame(self) -> None:
        """Render both the 2D Tank Battle Arena and the Telemetry Sidebar HUD."""
        self.screen.fill(BG_COLOR)
        self.arena_renderer.draw(self.screen, self.state)
        self._draw_sidebar()
        pygame.display.flip()

    def _draw_sidebar(self) -> None:
        panel_rect = pygame.Rect(self.SIDEBAR_X, 16, self.SIDEBAR_W, self.WINDOW_H - 32)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, CARD_BORDER, panel_rect, 2, border_radius=10)

        sx = self.SIDEBAR_X + 14
        title = self.font_title.render("TANK BATTLE — CONTROL & TELEMETRY", True, TEXT_WHITE)
        self.screen.blit(title, (sx, 24))

        # Controller labels above buttons
        lbl_p1 = self.font_sec.render("Player 1 (MAX — Bottom Cyan):", True, P1_PRIMARY)
        self.screen.blit(lbl_p1, (sx, 42))
        lbl_p2 = self.font_sec.render("Player 2 (MIN — Top Crimson):", True, P2_PRIMARY)
        self.screen.blit(lbl_p2, (sx, 94))

        # Update dynamic button captions
        p1_spec = self.controller_specs[self.p1_idx]
        p2_spec = self.controller_specs[self.p2_idx]
        self.buttons[0].label = f"P1: {self._format_spec_label(p1_spec)}"
        self.buttons[1].label = f"P2: {self._format_spec_label(p2_spec)}"
        self.buttons[2].label = f"Search Depth: d = {self.depths[self.depth_idx]}"
        self.buttons[3].label = f"Map: {self.map_keys[self.map_idx]}"
        self.buttons[4].label = "Pause [Space]" if self.running_sim else "Start / Resume [Space]"
        self.buttons[7].label = f"Speed: {self.speeds[self.speed_idx][0]}"

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            hovered = btn.rect.collidepoint(mouse_pos)
            bg = BTN_HOVER if hovered else (btn.accent_color if btn.accent_color == BTN_ACTIVE and self.running_sim else BTN_BG)
            pygame.draw.rect(self.screen, bg, btn.rect, border_radius=6)
            border_c = btn.accent_color if btn.accent_color else CARD_BORDER
            pygame.draw.rect(self.screen, border_c, btn.rect, 2, border_radius=6)
            txt = self.font_bold.render(btn.label, True, TEXT_WHITE)
            self.screen.blit(
                txt,
                (btn.rect.centerx - txt.get_width() // 2, btn.rect.centery - txt.get_height() // 2),
            )

        # Turn & Human Prompt Banner
        status_y = 294
        turn_str = f"Turn: {self.state.turn:03d}  |  Active Turn: Player {self.state.current_player}"
        if self.is_human_turn():
            turn_str = f"HUMAN P{self.state.current_player}: WASD/Arrows=Move, F/Enter=FIRE, Q=STAY"
            col = HP_WARN
        else:
            col = P1_PRIMARY if self.state.current_player == 1 else P2_PRIMARY
        st_lbl = self.font_bold.render(turn_str, True, col)
        self.screen.blit(st_lbl, (sx, status_y))

        # Telemetry Cards for Player 1 & Player 2
        self._draw_player_telemetry_card(pid=1, y=318, color=P1_PRIMARY)
        self._draw_player_telemetry_card(pid=2, y=458, color=P2_PRIMARY)

        # Recent Action & Collision Log Card
        log_rect = pygame.Rect(sx, 598, self.SIDEBAR_W - 28, 116)
        pygame.draw.rect(self.screen, CARD_BG, log_rect, border_radius=8)
        pygame.draw.rect(self.screen, CARD_BORDER, log_rect, 1, border_radius=8)
        hdr = self.font_bold.render("Recent Turn & Search Telemetry Log:", True, TEXT_MUTED)
        self.screen.blit(hdr, (log_rect.x + 8, log_rect.y + 5))
        for i, line in enumerate(self.action_log[-5:]):
            row_txt = self.font_body.render(line, True, TEXT_WHITE)
            self.screen.blit(row_txt, (log_rect.x + 8, log_rect.y + 24 + i * 17))

    def _draw_player_telemetry_card(
        self, pid: int, y: int, color: tuple[int, int, int]
    ) -> None:
        sx = self.SIDEBAR_X + 14
        card_rect = pygame.Rect(sx, y, self.SIDEBAR_W - 28, 132)
        pygame.draw.rect(self.screen, CARD_BG, card_rect, border_radius=8)
        pygame.draw.rect(self.screen, color, card_rect, 2, border_radius=8)

        tank = self.state.tanks[pid]
        base = self.state.bases[pid]
        metrics = self.last_metrics[pid]

        role = "MAX" if pid == 1 else "MIN"
        hdr = self.font_sec.render(
            f"Player {pid} ({role})  |  Tank HP: {tank.hp}/{TANK_INITIAL_HP}  |  Base HP: {base.hp}/{BASE_INITIAL_HP}",
            True,
            color,
        )
        self.screen.blit(hdr, (card_rect.x + 10, card_rect.y + 6))

        if metrics is None:
            sub = self.font_body.render("Waiting for first decision...", True, TEXT_MUTED)
            self.screen.blit(sub, (card_rect.x + 10, card_rect.y + 34))
            return

        lines = [
            f"Action : {metrics.chosen_action.value:<12} | Eval Score : {metrics.score:+.1f}",
            f"Time   : {metrics.time_s * 1000:6.2f} ms    | Depth      : {metrics.depth_reached} ply",
            f"States : {metrics.nodes_explored:<7d}      | Pruned     : {metrics.nodes_pruned} ({metrics.pruning_ratio * 100:.1f}%)",
            f"TT Hits: {metrics.tt_hits:<7d}      | Facing     : {tank.direction.name}",
        ]
        for idx, text in enumerate(lines):
            surf = self.font_body.render(text, True, TEXT_WHITE)
            self.screen.blit(surf, (card_rect.x + 10, card_rect.y + 32 + idx * 22))

    def run(self) -> None:
        """Main interactive PyGame loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.buttons:
                        if btn.rect.collidepoint(event.pos):
                            btn.on_click()
                            break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.toggle_pause()
                    elif event.key == pygame.K_n:
                        self.step_once()
                    elif event.key == pygame.K_r:
                        self.reset_match()
                    elif event.key == pygame.K_p:
                        self.reload_plugins(True)
                    elif self.is_human_turn():
                        human_act = self._map_key_to_action(event.key)
                        if human_act is not None:
                            self.step_once(human_action=human_act)

            # Automatic turn stepping when simulation is active and current player is AI
            if self.running_sim and not self.state.is_terminal() and not self.is_human_turn():
                now = pygame.time.get_ticks()
                delay_ms = self.speeds[self.speed_idx][1]
                if now - self.last_step_tick >= delay_ms:
                    self.step_once()
                    self.last_step_tick = now

            self.render_frame()
            self.clock.tick(60)

        pygame.quit()

    @staticmethod
    def _map_key_to_action(key: int) -> Optional[Action]:
        mapping = {
            pygame.K_w: Action.MOVE_UP,
            pygame.K_UP: Action.MOVE_UP,
            pygame.K_s: Action.MOVE_DOWN,
            pygame.K_DOWN: Action.MOVE_DOWN,
            pygame.K_a: Action.MOVE_LEFT,
            pygame.K_LEFT: Action.MOVE_LEFT,
            pygame.K_d: Action.MOVE_RIGHT,
            pygame.K_RIGHT: Action.MOVE_RIGHT,
            pygame.K_f: Action.FIRE,
            pygame.K_RETURN: Action.FIRE,
            pygame.K_q: Action.STAY,
        }
        return mapping.get(key)
