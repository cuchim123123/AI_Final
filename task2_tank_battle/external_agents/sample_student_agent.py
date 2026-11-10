"""Sample External Student Group Algorithm demonstrating the Plugin Interface (R3).

Other student groups can write their own algorithm in a single `.py` file like this
and place it in `external_agents/` or load it directly via the PyGame GUI!
"""
from __future__ import annotations

AGENT_NAME = "GroupB_AggressorBot"


class GroupBAggressorAgent:
    """External student group agent using a tactical 2-ply lookahead + aggressive line-of-fire."""

    def __init__(self) -> None:
        self.name = AGENT_NAME

    def get_action(self, state) -> str:
        """Accepts `state` (GameState clone) and returns an action name string."""
        me = state.tanks[state.current_player]
        enemy_id = 2 if state.current_player == 1 else 1
        enemy_tank = state.tanks[enemy_id]
        enemy_base = state.bases[enemy_id]

        # 1. Dodge incoming enemy bullets first!
        for b in state.bullets:
            if b.owner_id == state.current_player:
                continue
            dr, dc = b.direction.delta
            for step in range(1, 4):
                if (b.row + dr * step, b.col + dc * step) == (me.row, me.col):
                    # Step perpendicular to the bullet direction
                    if dr != 0:
                        for move_name, dc_try in (("MOVE_LEFT", -1), ("MOVE_RIGHT", 1)):
                            if not state.is_cell_blocked(me.row, me.col + dc_try):
                                return move_name
                    else:
                        for move_name, dr_try in (("MOVE_UP", -1), ("MOVE_DOWN", 1)):
                            if not state.is_cell_blocked(me.row + dr_try, me.col):
                                return move_name

        # 2. If aligned with enemy tank or enemy base along current facing direction, FIRE!
        dr, dc = me.direction.delta
        if state.can_fire(state.current_player):
            for target in (enemy_tank, enemy_base):
                if dr != 0 and me.col == target.col and (target.row - me.row) * dr > 0:
                    return "FIRE"
                if dc != 0 and me.row == target.row and (target.col - me.col) * dc > 0:
                    return "FIRE"

        # 3. If sharing row/column with enemy tank or base, turn to face it
        for target in (enemy_tank, enemy_base):
            if me.row == target.row:
                return "MOVE_RIGHT" if target.col > me.col else "MOVE_LEFT"
            if me.col == target.col:
                return "MOVE_DOWN" if target.row > me.row else "MOVE_UP"

        # 4. Otherwise advance toward aligning with enemy base or enemy tank
        target = enemy_base if abs(me.row - enemy_base.row) < abs(me.row - enemy_tank.row) else enemy_tank
        if abs(me.row - target.row) <= abs(me.col - target.col):
            desired = "MOVE_DOWN" if target.row > me.row else "MOVE_UP"
        else:
            desired = "MOVE_RIGHT" if target.col > me.col else "MOVE_LEFT"

        return desired
