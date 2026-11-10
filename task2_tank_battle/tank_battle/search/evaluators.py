"""Evaluation functions for Zero-Sum Adversarial Search (Basic vs. Tactical Heuristic)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from ..core.entities import Base, Bullet, Tank
from ..core.state import GameState
from ..core.types import BULLET_SPEED, Direction

TERMINAL_UTILITY: float = 10000.0


class StateEvaluator(ABC):
    """Strategy interface for evaluating a GameState from Player 1 (MAX)'s perspective.

    Zero-Sum Property:
    Positive values favor Player 1 (MAX); negative values favor Player 2 (MIN).
    """

    name: str = "abstract"

    @staticmethod
    def terminal_utility(state: GameState) -> float:
        """Exact utility U(s) for terminal states.

        Prefers faster wins (+10000 - turn) and slower losses (-10000 + turn).
        """
        winner = state.get_winner()
        if winner == 1:
            return TERMINAL_UTILITY - state.turn
        if winner == 2:
            return -TERMINAL_UTILITY + state.turn
        return 0.0

    @abstractmethod
    def evaluate(self, state: GameState) -> float:
        """Return utility U(s) if terminal, else heuristic estimate Eval(s)."""


class BasicEvaluator(StateEvaluator):
    """Baseline evaluator used for standard Minimax & Alpha-Beta Search.

    Uses terminal win/loss utility, remaining HP difference, and a minimal
    progress tie-breaker so baseline agents advance rather than stall against walls,
    without any of TacticalHeuristicEvaluator's bullet raycasting, line-of-fire
    alignment, parry detection, or base-shield heuristics.
    """

    name: str = "basic"

    def evaluate(self, state: GameState) -> float:
        if state.is_terminal():
            return self.terminal_utility(state)

        t1, t2 = state.tanks[1], state.tanks[2]
        b1, b2 = state.bases[1], state.bases[2]
        hp_score = 100.0 * (t1.hp - t2.hp) + 100.0 * (b1.hp - b2.hp)

        d1 = abs(t1.row - b2.row) + abs(t1.col - b2.col)
        d2 = abs(t2.row - b1.row) + abs(t2.col - b1.col)
        return hp_score + 1.0 * (d2 - d1)


class TacticalHeuristicEvaluator(StateEvaluator):
    """Rich domain-specific Heuristic Evaluation Function Eval(s) for Heuristic Minimax.

    Combines 6 zero-sum tactical features with turn-aware bullet parry/dodge analysis:
    1. Tank HP differential (w = 240 per HP)
    2. Base HP differential (w = 220 per HP)
    3. Turn-Aware Speed-3 Bullet Trajectory Threat, Parry & Evasion Analysis
    4. Cardinal Line-of-Fire & Aim Alignment on Enemy Base and Enemy Tank
    5. Offensive Base Approach & Lane Alignment
    6. Base Shield & Cardinal Lane Wall Integrity (w = 26 per cardinal wall HP, 12 per shield HP)
    """

    name: str = "heuristic"

    def evaluate(self, state: GameState) -> float:
        if state.is_terminal():
            return self.terminal_utility(state)

        t1, t2 = state.tanks[1], state.tanks[2]
        b1, b2 = state.bases[1], state.bases[2]

        # 1 & 2. Realized Material HP Differentials
        score = 240.0 * (t1.hp - t2.hp) + 220.0 * (b1.hp - b2.hp)

        # 3. Base Shield & Cardinal Lane Wall Integrity
        score += 12.0 * (self._base_shield_hp(state, b1) - self._base_shield_hp(state, b2))
        score += 26.0 * (self._cardinal_lane_wall_hp(state, b1) - self._cardinal_lane_wall_hp(state, b2))

        # 4. Turn-Aware Bullet Trajectory Analysis (Speed = 3 cells/cycle)
        score += self._evaluate_bullet_threats(state)

        # 5. Offensive Positioning & Line-of-Fire Alignment (Player 1 minus Player 2)
        score += self._evaluate_player_offense(state, t1, t2, b2)
        score -= self._evaluate_player_offense(state, t2, t1, b1)

        return score

    @classmethod
    def _evaluate_bullet_threats(cls, state: GameState) -> float:
        """Trace active bullets up to 2 cycles (6 cells) with turn/parry/dodge awareness."""
        delta_score = 0.0
        for b in state.bullets:
            dr, dc = b.direction.delta
            r, c = b.row, b.col
            enemy_id = 2 if b.owner_id == 1 else 1
            enemy_base = state.bases[enemy_id]
            friendly_base = state.bases[b.owner_id]

            for step in range(1, 2 * BULLET_SPEED + 1):
                r += dr
                c += dc
                if not state.in_bounds(r, c) or (r, c) in state.steel_walls:
                    break

                urgency = 1.0 if step <= BULLET_SPEED else 0.5

                if (r, c) in state.walls:
                    # Penalize shooting one's own base shield walls
                    if abs(r - friendly_base.row) <= 1 and abs(c - friendly_base.col) <= 1:
                        own_wall_pen = -18.0 * urgency
                        delta_score += own_wall_pen if b.owner_id == 1 else -own_wall_pen
                        break

                    is_cardinal_base_wall = (
                        (r == enemy_base.row or c == enemy_base.col)
                        and abs(r - enemy_base.row) + abs(c - enemy_base.col) <= 5
                    )
                    is_shield_wall = (
                        abs(r - enemy_base.row) <= 1 and abs(c - enemy_base.col) <= 1
                    )
                    if is_cardinal_base_wall:
                        breach = 16.0 * urgency
                    elif is_shield_wall:
                        breach = 8.0 * urgency
                    else:
                        breach = 3.5 * urgency
                    delta_score += breach if b.owner_id == 1 else -breach
                    break

                # Check if bullet path intersects an enemy tank
                hit_entity = False
                for pid, tank in state.tanks.items():
                    if pid != b.owner_id and tank.is_alive and tank.pos == (r, c):
                        impact = cls._score_tank_bullet_threat(state, b, tank, step)
                        delta_score += impact if pid == 2 else -impact
                        hit_entity = True
                        break
                if hit_entity:
                    break

                # Check if bullet path intersects a base (hitting Base 2 favors P1; hitting Base 1 favors P2)
                for pid, base in state.bases.items():
                    if base.is_alive and base.pos == (r, c):
                        impact = 145.0 * urgency
                        delta_score += impact if pid == 2 else -impact
                        hit_entity = True
                        break
                if hit_entity:
                    break

        return delta_score

    @staticmethod
    def _score_tank_bullet_threat(
        state: GameState, bullet: Bullet, target_tank: Tank, step: int
    ) -> float:
        """Score a bullet heading toward `target_tank` in `step` cells based on turn & parry ability."""
        pid = target_tank.player_id
        dr, dc = bullet.direction.delta

        # Can target_tank parry by firing head-on into the bullet?
        tdr, tdc = target_tank.direction.delta
        facing_bullet = (tdr == -dr and tdc == -dc)
        can_parry = facing_bullet and state.can_fire(pid)

        # Can target_tank step sideways out of the bullet's line of fire?
        perp1 = (target_tank.row - dc, target_tank.col + dr)
        perp2 = (target_tank.row + dc, target_tank.col - dr)
        can_dodge_laterally = (
            not state.is_cell_blocked(*perp1) or not state.is_cell_blocked(*perp2)
        )

        if step <= BULLET_SPEED:
            if state.current_player != pid:
                # Target tank does NOT get a turn before this bullet advances 3 cells -> guaranteed hit!
                return 190.0
            # Target tank acts right now before the bullet advances
            if can_parry:
                # Easily parried in place by firing back -> minimal value (prevents parry loops!)
                return 5.0
            if can_dodge_laterally:
                # Forces target tank to spend its turn dodging out of the lane
                return 42.0
            # Trapped! Neither parry nor lateral dodge is available
            return 185.0
        else:
            # 4 <= step <= 6 (2 cycles away)
            if state.current_player == pid:
                # If target_tank stays here during its current turn, the bullet will be 1-3 cells
                # away on the opponent's next turn -> dangerous to stay if unable to parry!
                return 15.0 if can_parry else 65.0
            return 20.0

    @classmethod
    def _evaluate_player_offense(
        cls, state: GameState, attacker: Tank, enemy_tank: Tank, enemy_base: Base
    ) -> float:
        """Evaluate offensive alignment, lane approach, and aiming for `attacker`."""
        val = 0.0

        # 1. Approach enemy base & align with enemy base's column/row
        row_diff = abs(attacker.row - enemy_base.row)
        col_diff = abs(attacker.col - enemy_base.col)
        dist_base = row_diff + col_diff
        axis_base = min(row_diff, col_diff)
        val -= 12.0 * dist_base + 14.0 * axis_base

        # 2. Line-of-fire alignment with stationary enemy base (discounted if enemy tank blocks)
        val += cls._line_of_fire_base(state, attacker, enemy_tank, enemy_base.pos)

        # 3. Line-of-fire alignment with enemy tank
        val += cls._line_of_fire_tank(state, attacker, enemy_tank)

        return val

    @staticmethod
    def _line_of_fire_base(
        state: GameState, attacker: Tank, enemy_tank: Tank, base_pos: Tuple[int, int]
    ) -> float:
        """Reward being in the same row or column as the enemy base with clear/breachable lane."""
        br, bc = base_pos
        if attacker.row != br and attacker.col != bc:
            return 0.0

        if attacker.row == br:
            required_dir = Direction.RIGHT if bc > attacker.col else Direction.LEFT
            step_r, step_c = 0, (1 if bc > attacker.col else -1)
            dist = abs(bc - attacker.col)
        else:
            required_dir = Direction.DOWN if br > attacker.row else Direction.UP
            step_r, step_c = (1 if br > attacker.row else -1), 0
            dist = abs(br - attacker.row)

        wall_hp_blocking = 0
        tank_blocking = 0
        r, c = attacker.row, attacker.col
        for _ in range(1, dist):
            r += step_r
            c += step_c
            if (r, c) in state.steel_walls:
                return 0.0
            wall_hp_blocking += state.walls.get((r, c), 0)
            if enemy_tank.is_alive and enemy_tank.pos == (r, c):
                tank_blocking += 4

        denom = 1.0 + 0.55 * wall_hp_blocking + 0.8 * tank_blocking + 0.12 * dist
        score = 68.0 / denom
        if attacker.direction == required_dir:
            score += 22.0 / denom
        return score

    @staticmethod
    def _line_of_fire_tank(
        state: GameState, attacker: Tank, enemy_tank: Tank
    ) -> float:
        """Reward aiming directly at the enemy tank along an open cardinal line."""
        tr, tc = enemy_tank.pos
        if attacker.row != tr and attacker.col != tc:
            return 0.0

        if attacker.row == tr:
            required_dir = Direction.RIGHT if tc > attacker.col else Direction.LEFT
            step_r, step_c = 0, (1 if tc > attacker.col else -1)
            dist = abs(tc - attacker.col)
        else:
            required_dir = Direction.DOWN if tr > attacker.row else Direction.UP
            step_r, step_c = (1 if tr > attacker.row else -1), 0
            dist = abs(tr - attacker.row)

        if attacker.direction != required_dir:
            return 0.0

        wall_hp_blocking = 0
        r, c = attacker.row, attacker.col
        for _ in range(1, dist):
            r += step_r
            c += step_c
            if (r, c) in state.steel_walls:
                return 0.0
            wall_hp_blocking += state.walls.get((r, c), 0)

        if wall_hp_blocking == 0:
            return 32.0 if dist <= BULLET_SPEED else 14.0
        return 8.0 / (1.0 + wall_hp_blocking)

    @staticmethod
    def _base_shield_hp(state: GameState, base: Base) -> int:
        """Sum of HP of destructible walls immediately surrounding `base`."""
        total = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                total += state.walls.get((base.row + dr, base.col + dc), 0)
        return total

    @staticmethod
    def _cardinal_lane_wall_hp(state: GameState, base: Base) -> int:
        """Sum of HP of walls lying directly on the row or column of `base` within 5 cells."""
        total = 0
        for d in range(1, 6):
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                r, c = base.row + dr * d, base.col + dc * d
                total += state.walls.get((r, c), 0)
        return total
