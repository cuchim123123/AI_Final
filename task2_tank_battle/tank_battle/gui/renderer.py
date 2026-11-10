"""PyGame Arena Renderer for the Tank Battle Game."""
from __future__ import annotations

from typing import Tuple

import pygame

from ..core.entities import Base, Bullet, Tank
from ..core.state import GameState
from ..core.types import BASE_INITIAL_HP, Direction, TANK_INITIAL_HP, WALL_INITIAL_HP

# Color Palette (High-Contrast Dark Tactical Theme)
BG_COLOR = (15, 23, 42)          # Slate 900
GRID_TILE_A = (30, 41, 59)       # Slate 800
GRID_TILE_B = (24, 34, 50)       # Slightly darker slate
GRID_LINE = (51, 65, 85)         # Slate 700

P1_PRIMARY = (56, 189, 248)      # Sky 400 (Player 1 MAX)
P1_DARK = (3, 105, 161)          # Sky 700
P2_PRIMARY = (248, 113, 113)     # Red 400 (Player 2 MIN)
P2_DARK = (185, 28, 28)          # Red 700

WALL_HP3_COLOR = (180, 83, 9)    # Amber 700 (Intact brick wall, HP=3)
WALL_HP2_COLOR = (217, 119, 6)   # Amber 600 (Cracked brick wall, HP=2)
WALL_HP1_COLOR = (245, 158, 11)  # Amber 500 (Heavily damaged wall, HP=1)
WALL_MORTAR = (69, 26, 3)
STEEL_COLOR = (148, 163, 184)    # Slate 400

HP_GOOD = (34, 197, 94)          # Green 500
HP_WARN = (234, 179, 8)          # Yellow 500
HP_CRIT = (239, 68, 68)          # Red 500
TEXT_WHITE = (248, 250, 252)


class ArenaRenderer:
    """Renders the 2D Tank Battle grid, entities, HP bars, bullets, and hit effects."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        pygame.font.init()
        self.font_small = pygame.font.SysFont("Consolas", 13, bold=True)
        self.font_badge = pygame.font.SysFont("Consolas", 15, bold=True)
        self.font_banner = pygame.font.SysFont("Segoe UI", 28, bold=True)

    def draw(self, surface: pygame.Surface, state: GameState) -> None:
        """Draw the complete game arena onto `surface` within `self.rect`."""
        cell_w = self.rect.width // state.width
        cell_h = self.rect.height // state.height
        cell_size = min(cell_w, cell_h)

        board_w = cell_size * state.width
        board_h = cell_size * state.height
        origin_x = self.rect.x + (self.rect.width - board_w) // 2
        origin_y = self.rect.y + (self.rect.height - board_h) // 2

        # 1. Draw Grid Background Tiles
        for r in range(state.height):
            for c in range(state.width):
                tile_rect = pygame.Rect(
                    origin_x + c * cell_size,
                    origin_y + r * cell_size,
                    cell_size,
                    cell_size,
                )
                color = GRID_TILE_A if (r + c) % 2 == 0 else GRID_TILE_B
                pygame.draw.rect(surface, color, tile_rect)
                pygame.draw.rect(surface, GRID_LINE, tile_rect, 1)

        # 2. Draw Indestructible Steel Walls
        for (r, c) in state.steel_walls:
            self._draw_steel_wall(surface, origin_x, origin_y, r, c, cell_size)

        # 3. Draw Destructible Brick Walls (HP = 3, 2, 1)
        for (r, c), hp in state.walls.items():
            self._draw_brick_wall(surface, origin_x, origin_y, r, c, cell_size, hp)

        # 4. Draw Bases (Initial HP = 9)
        for pid, base in state.bases.items():
            self._draw_base(surface, origin_x, origin_y, cell_size, base)

        # 5. Draw Tanks (Initial HP = 6)
        for pid, tank in state.tanks.items():
            self._draw_tank(surface, origin_x, origin_y, cell_size, tank)

        # 6. Draw Active Bullets (Speed = 3 cells/cycle)
        for bullet in state.bullets:
            if state.in_bounds(bullet.row, bullet.col):
                self._draw_bullet(surface, origin_x, origin_y, cell_size, bullet)

        # 7. Draw Recent Collision Events (Visual Flash Ring)
        for ev in state.events:
            pos = ev.get("pos")
            if pos and state.in_bounds(pos[0], pos[1]):
                cx = origin_x + pos[1] * cell_size + cell_size // 2
                cy = origin_y + pos[0] * cell_size + cell_size // 2
                pygame.draw.circle(surface, (251, 191, 36), (cx, cy), cell_size // 3, 3)

        # 8. Game Over Overlay Banner
        if state.is_terminal():
            self._draw_terminal_banner(surface, origin_x, origin_y, board_w, board_h, state)

    def _draw_brick_wall(
        self,
        surface: pygame.Surface,
        ox: int,
        oy: int,
        r: int,
        c: int,
        size: int,
        hp: int,
    ) -> None:
        pad = max(2, size // 14)
        rect = pygame.Rect(ox + c * size + pad, oy + r * size + pad, size - 2 * pad, size - 2 * pad)
        if hp >= 3:
            color = WALL_HP3_COLOR
        elif hp == 2:
            color = WALL_HP2_COLOR
        else:
            color = WALL_HP1_COLOR

        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.rect(surface, WALL_MORTAR, rect, 2, border_radius=4)

        # Brick mortar lines
        mid_y = rect.y + rect.height // 2
        pygame.draw.line(surface, WALL_MORTAR, (rect.left, mid_y), (rect.right, mid_y), 2)
        mid_x = rect.x + rect.width // 2
        pygame.draw.line(surface, WALL_MORTAR, (mid_x, rect.top), (mid_x, mid_y), 2)

        # HP badge in center
        lbl = self.font_small.render(f"{hp}/{WALL_INITIAL_HP}", True, TEXT_WHITE)
        surface.blit(
            lbl,
            (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2),
        )

    def _draw_steel_wall(
        self, surface: pygame.Surface, ox: int, oy: int, r: int, c: int, size: int
    ) -> None:
        pad = 3
        rect = pygame.Rect(ox + c * size + pad, oy + r * size + pad, size - 2 * pad, size - 2 * pad)
        pygame.draw.rect(surface, STEEL_COLOR, rect, border_radius=4)
        pygame.draw.rect(surface, (226, 232, 240), rect, 2, border_radius=4)

    def _draw_base(
        self, surface: pygame.Surface, ox: int, oy: int, size: int, base: Base
    ) -> None:
        x = ox + base.col * size
        y = oy + base.row * size
        pad = max(4, size // 10)
        rect = pygame.Rect(x + pad, y + pad, size - 2 * pad, size - 2 * pad)

        primary = P1_PRIMARY if base.player_id == 1 else P2_PRIMARY
        dark = P1_DARK if base.player_id == 1 else P2_DARK

        if not base.is_alive:
            pygame.draw.rect(surface, (60, 20, 20), rect, border_radius=6)
            pygame.draw.line(surface, HP_CRIT, rect.topleft, rect.bottomright, 4)
            pygame.draw.line(surface, HP_CRIT, rect.topright, rect.bottomleft, 4)
            return

        pygame.draw.rect(surface, dark, rect, border_radius=6)
        pygame.draw.rect(surface, primary, rect, 3, border_radius=6)

        # Diamond command emblem inside base
        cx, cy = rect.centerx, rect.centery - 2
        d = max(8, size // 5)
        diamond = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
        pygame.draw.polygon(surface, primary, diamond)

        # Label & HP Bar
        tag = self.font_small.render(f"B{base.player_id}:{base.hp}", True, TEXT_WHITE)
        surface.blit(tag, (rect.centerx - tag.get_width() // 2, rect.y + 3))
        self._draw_hp_bar(
            surface,
            x + 4,
            y + size - 9,
            size - 8,
            5,
            base.hp,
            BASE_INITIAL_HP,
        )

    def _draw_tank(
        self, surface: pygame.Surface, ox: int, oy: int, size: int, tank: Tank
    ) -> None:
        x = ox + tank.col * size
        y = oy + tank.row * size
        cx = x + size // 2
        cy = y + size // 2

        primary = P1_PRIMARY if tank.player_id == 1 else P2_PRIMARY
        dark = P1_DARK if tank.player_id == 1 else P2_DARK

        if not tank.is_alive:
            pygame.draw.circle(surface, (80, 25, 25), (cx, cy), size // 3)
            pygame.draw.line(surface, HP_CRIT, (x + 8, y + 8), (x + size - 8, y + size - 8), 3)
            pygame.draw.line(surface, HP_CRIT, (x + size - 8, y + 8), (x + 8, y + size - 8), 3)
            return

        # Tank chassis
        body_pad = max(8, size // 5)
        body_rect = pygame.Rect(
            x + body_pad,
            y + body_pad,
            size - 2 * body_pad,
            size - 2 * body_pad,
        )
        pygame.draw.rect(surface, dark, body_rect, border_radius=6)
        pygame.draw.rect(surface, primary, body_rect, 2, border_radius=6)

        # Turret gun barrel pointing in tank.direction
        dr, dc = tank.direction.delta
        barrel_len = size // 2 - 3
        end_x = cx + dc * barrel_len
        end_y = cy + dr * barrel_len
        pygame.draw.line(surface, (248, 250, 252), (cx, cy), (end_x, end_y), 5)
        pygame.draw.circle(surface, primary, (cx, cy), max(6, size // 6))

        # Tank ID & HP bar
        lbl = self.font_small.render(f"T{tank.player_id}", True, TEXT_WHITE)
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))

        self._draw_hp_bar(
            surface,
            x + 4,
            y + 3,
            size - 8,
            5,
            tank.hp,
            TANK_INITIAL_HP,
        )

    def _draw_bullet(
        self, surface: pygame.Surface, ox: int, oy: int, size: int, bullet: Bullet
    ) -> None:
        cx = ox + bullet.col * size + size // 2
        cy = oy + bullet.row * size + size // 2
        color = (125, 211, 252) if bullet.owner_id == 1 else (253, 186, 116)

        # Short directional tail showing bullet travel direction
        dr, dc = bullet.direction.delta
        tail_x = cx - dc * (size // 4)
        tail_y = cy - dr * (size // 4)
        pygame.draw.line(surface, color, (tail_x, tail_y), (cx, cy), 4)
        pygame.draw.circle(surface, (254, 240, 138), (cx, cy), max(5, size // 9))
        pygame.draw.circle(surface, color, (cx, cy), max(5, size // 9), 2)

    @staticmethod
    def _draw_hp_bar(
        surface: pygame.Surface,
        x: int,
        y: int,
        w: int,
        h: int,
        hp: int,
        max_hp: int,
    ) -> None:
        bg_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (15, 23, 42), bg_rect, border_radius=2)
        ratio = max(0.0, min(1.0, hp / max(1, max_hp)))
        fill_w = int(w * ratio)
        if fill_w > 0:
            color = HP_GOOD if ratio > 0.5 else (HP_WARN if ratio > 0.25 else HP_CRIT)
            pygame.draw.rect(surface, color, pygame.Rect(x, y, fill_w, h), border_radius=2)

    def _draw_terminal_banner(
        self,
        surface: pygame.Surface,
        ox: int,
        oy: int,
        bw: int,
        bh: int,
        state: GameState,
    ) -> None:
        winner = state.get_winner()
        if winner == 1:
            msg = "PLAYER 1 (MAX) WINS!"
            border_col = P1_PRIMARY
        elif winner == 2:
            msg = "PLAYER 2 (MIN) WINS!"
            border_col = P2_PRIMARY
        else:
            msg = "MATCH ENDED IN A DRAW!"
            border_col = HP_WARN

        banner_w = min(bw - 40, 420)
        banner_h = 90
        bx = ox + (bw - banner_w) // 2
        by = oy + (bh - banner_h) // 2
        rect = pygame.Rect(bx, by, banner_w, banner_h)
        pygame.draw.rect(surface, (15, 23, 42), rect, border_radius=10)
        pygame.draw.rect(surface, border_col, rect, 3, border_radius=10)

        txt = self.font_banner.render(msg, True, border_col)
        sub = self.font_badge.render(
            f"Finished in {state.turn} turns — Press R or Reset to play again",
            True,
            TEXT_WHITE,
        )
        surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.y + 16))
        surface.blit(sub, (rect.centerx - sub.get_width() // 2, rect.y + 56))
