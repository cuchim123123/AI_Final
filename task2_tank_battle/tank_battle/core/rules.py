"""Deterministic Transition Engine & Physics for the Tank Battle Game."""
from __future__ import annotations

from typing import List, Tuple

from .entities import Bullet
from .state import GameState
from .types import Action, BULLET_SPEED, DAMAGE_PER_HIT


class TransitionEngine:
    """Implements the formal Zero-Sum Game transition function Result(s, a) -> s'.

    Game Cycle Order:
    1. Active player's tank executes its chosen Action (MOVE_*, FIRE, or STAY).
    2. All active bullets advance up to BULLET_SPEED (3) cells, processed
       cell by cell (sub-steps 1..3) with immediate collision detection after
       every single cell movement.
    3. Turn counter increments and active player switches (1 <-> 2).
    """

    ALL_ACTIONS: Tuple[Action, ...] = (
        Action.MOVE_UP,
        Action.MOVE_DOWN,
        Action.MOVE_LEFT,
        Action.MOVE_RIGHT,
        Action.FIRE,
        Action.STAY,
    )

    @classmethod
    def get_legal_actions(cls, state: GameState, prune_redundant: bool = False) -> List[Action]:
        """Return available actions for the current player.

        By specification, a tank has 06 actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT,
        MOVE_RIGHT, FIRE, STAY.
        When `prune_redundant=True` (used in search optimization), blocked moves that
        do not even change facing direction and illegal FIRE (when a bullet is already
        active) are pruned because they are strictly equivalent to STAY.
        """
        if not prune_redundant:
            return list(cls.ALL_ACTIONS)

        player = state.current_player
        tank = state.tanks[player]
        actions: List[Action] = []

        if state.can_fire(player):
            actions.append(Action.FIRE)

        for move_act in (Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT):
            target_dir = move_act.direction
            dr, dc = target_dir.delta
            nr, nc = tank.row + dr, tank.col + dc
            if not state.is_cell_blocked(nr, nc) or tank.direction != target_dir:
                actions.append(move_act)

        actions.append(Action.STAY)
        return actions

    @classmethod
    def apply_action(cls, state: GameState, action: Action, record_events: bool = False) -> GameState:
        """Return successor state s' = Result(s, action) without mutating s."""
        next_state = state.clone()
        cls.apply_action_inplace(next_state, action, record_events=record_events)
        return next_state

    @classmethod
    def apply_action_inplace(cls, state: GameState, action: Action, record_events: bool = False) -> None:
        """Mutate `state` in place by applying `action` for `state.current_player`."""
        if record_events:
            state.events.clear()

        player = state.current_player
        tank = state.tanks[player]

        # -------------------------------------------------------------------
        # Step 1: Tank Action Execution
        # -------------------------------------------------------------------
        if action.direction is not None:
            new_dir = action.direction
            tank.direction = new_dir
            dr, dc = new_dir.delta
            nr, nc = tank.row + dr, tank.col + dc
            if not state.is_cell_blocked(nr, nc):
                tank.row = nr
                tank.col = nc
        elif action == Action.FIRE:
            if state.can_fire(player):
                state.bullets.append(
                    Bullet(owner_id=player, row=tank.row, col=tank.col, direction=tank.direction)
                )
        elif action == Action.STAY:
            pass

        # -------------------------------------------------------------------
        # Step 2: Cell-by-Cell Bullet Movement (up to 3 cells per cycle)
        # -------------------------------------------------------------------
        cls._advance_bullets(state, record_events=record_events)

        # -------------------------------------------------------------------
        # Step 3: Advance Turn & Switch Active Player
        # -------------------------------------------------------------------
        state.turn += 1
        state.current_player = 2 if player == 1 else 1

    @classmethod
    def _advance_bullets(cls, state: GameState, record_events: bool = False) -> None:
        """Move all active bullets up to BULLET_SPEED (3) cells, one cell at a time."""
        for _sub_step in range(BULLET_SPEED):
            if not state.bullets:
                break

            surviving: List[Bullet] = []
            old_positions = [(b.row, b.col) for b in state.bullets]
            new_positions: List[Tuple[int, int]] = []

            for b in state.bullets:
                dr, dc = b.direction.delta
                new_positions.append((b.row + dr, b.col + dc))

            # Detect bullet-on-bullet collisions (same destination cell or head-on swap)
            collided_indices = set()
            n_bul = len(state.bullets)
            for i in range(n_bul):
                for j in range(i + 1, n_bul):
                    if state.bullets[i].owner_id == state.bullets[j].owner_id:
                        continue
                    same_cell = new_positions[i] == new_positions[j]
                    head_on_swap = (
                        new_positions[i] == old_positions[j]
                        and new_positions[j] == old_positions[i]
                    )
                    if same_cell or head_on_swap:
                        collided_indices.add(i)
                        collided_indices.add(j)
                        if record_events:
                            state.events.append({"type": "bullet_clash", "pos": new_positions[i]})

            # Process single-cell step & entity collision for each bullet
            for idx, b in enumerate(state.bullets):
                if idx in collided_indices:
                    continue

                nr, nc = new_positions[idx]
                b.row, b.col = nr, nc

                # 1. Out of grid bounds
                if not state.in_bounds(nr, nc):
                    if record_events:
                        state.events.append({"type": "out_of_bounds", "pos": (nr, nc)})
                    continue

                # 2. Indestructible steel wall
                if (nr, nc) in state.steel_walls:
                    if record_events:
                        state.events.append({"type": "hit_steel", "pos": (nr, nc)})
                    continue

                # 3. Destructible Wall (Initial HP=3, Damage=1)
                if (nr, nc) in state.walls:
                    state.walls[(nr, nc)] -= DAMAGE_PER_HIT
                    destroyed = state.walls[(nr, nc)] <= 0
                    if destroyed:
                        del state.walls[(nr, nc)]
                    if record_events:
                        state.events.append({
                            "type": "hit_wall",
                            "pos": (nr, nc),
                            "destroyed": destroyed,
                        })
                    continue  # Bullet stops immediately after hitting wall

                # 4. Base Collision (Initial HP=9, Damage=1)
                hit_base = False
                for pid, base in state.bases.items():
                    if base.is_alive and base.pos == (nr, nc):
                        base.hp = max(0, base.hp - DAMAGE_PER_HIT)
                        hit_base = True
                        if record_events:
                            state.events.append({
                                "type": "hit_base",
                                "player_id": pid,
                                "pos": (nr, nc),
                                "hp": base.hp,
                            })
                        break
                if hit_base:
                    continue  # Bullet stops immediately after hitting base

                # 5. Tank Collision (Initial HP=6, Damage=1)
                hit_tank = False
                for pid, tank in state.tanks.items():
                    if pid != b.owner_id and tank.is_alive and tank.pos == (nr, nc):
                        tank.hp = max(0, tank.hp - DAMAGE_PER_HIT)
                        hit_tank = True
                        if record_events:
                            state.events.append({
                                "type": "hit_tank",
                                "player_id": pid,
                                "pos": (nr, nc),
                                "hp": tank.hp,
                            })
                        break
                if hit_tank:
                    continue  # Bullet stops immediately after hitting tank

                # No collision in this single-cell step -> bullet stays in flight
                surviving.append(b)

            state.bullets = surviving
            if state.is_terminal():
                break
