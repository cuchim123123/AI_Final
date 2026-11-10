"""Tactical Move Ordering to maximize Alpha-Beta pruning efficiency."""
from __future__ import annotations

from typing import List, Optional

from ..core.state import GameState
from ..core.types import Action, BULLET_SPEED


class MoveOrderer:
    """Orders candidate actions from most promising to least promising.

    In Alpha-Beta Pruning, examining the best action first approaches the
    theoretical optimal branching reduction O(b^(d/2)).
    """

    @classmethod
    def order_actions(
        cls,
        state: GameState,
        actions: List[Action],
        tt_best_action: Optional[Action] = None,
    ) -> List[Action]:
        player = state.current_player
        tank = state.tanks[player]
        enemy_id = 2 if player == 1 else 1
        enemy_tank = state.tanks[enemy_id]
        enemy_base = state.bases[enemy_id]

        in_bullet_danger = cls._is_in_bullet_path(state, tank.row, tank.col, player)
        aligned_to_shoot = cls._is_aligned_to_shoot(
            tank.row, tank.col, tank.direction, enemy_tank.pos, enemy_base.pos
        )

        def priority(act: Action) -> float:
            # 1. Principal Variation / Transposition Table move always goes first
            if tt_best_action is not None and act == tt_best_action:
                return 1000.0

            score = 0.0
            if act == Action.FIRE:
                if not state.can_fire(player):
                    return -500.0
                score += 180.0 if aligned_to_shoot else 40.0

            elif act.direction is not None:
                dr, dc = act.direction.delta
                nr, nc = tank.row + dr, tank.col + dc
                blocked = state.is_cell_blocked(nr, nc)

                # If currently threatened by an enemy bullet, strongly prioritize stepping off-axis
                if in_bullet_danger and not blocked:
                    if not cls._is_in_bullet_path(state, nr, nc, player):
                        score += 250.0

                if not blocked:
                    # Reward moving closer to enemy tank or enemy base
                    old_d = min(
                        abs(tank.row - enemy_tank.row) + abs(tank.col - enemy_tank.col),
                        abs(tank.row - enemy_base.row) + abs(tank.col - enemy_base.col),
                    )
                    new_d = min(
                        abs(nr - enemy_tank.row) + abs(nc - enemy_tank.col),
                        abs(nr - enemy_base.row) + abs(nc - enemy_base.col),
                    )
                    score += 25.0 * (old_d - new_d)
                    if nr == enemy_tank.row or nc == enemy_tank.col or nr == enemy_base.row or nc == enemy_base.col:
                        score += 20.0
                else:
                    # Blocked move only rotates the tank
                    if cls._is_aligned_to_shoot(
                        tank.row, tank.col, act.direction, enemy_tank.pos, enemy_base.pos
                    ):
                        score += 35.0
                    else:
                        score -= 80.0

            elif act == Action.STAY:
                score -= 30.0 if not in_bullet_danger else -200.0

            return score

        return sorted(actions, key=priority, reverse=True)

    @staticmethod
    def _is_in_bullet_path(state: GameState, r: int, c: int, player_id: int) -> bool:
        """True if an enemy bullet is heading toward (r, c) within 1-2 cycles."""
        for b in state.bullets:
            if b.owner_id == player_id:
                continue
            dr, dc = b.direction.delta
            br, bc = b.row, b.col
            for _ in range(2 * BULLET_SPEED):
                br += dr
                bc += dc
                if not state.in_bounds(br, bc) or (br, bc) in state.walls or (br, bc) in state.steel_walls:
                    break
                if (br, bc) == (r, c):
                    return True
        return False

    @staticmethod
    def _is_aligned_to_shoot(r: int, c: int, direction, target1, target2) -> bool:
        """True if ray from (r, c) in `direction` passes through `target1` or `target2`."""
        dr, dc = direction.delta
        for tr, tc in (target1, target2):
            if dr != 0 and c == tc and (tr - r) * dr > 0:
                return True
            if dc != 0 and r == tr and (tc - c) * dc > 0:
                return True
        return False
