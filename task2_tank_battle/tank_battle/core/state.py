"""GameState representation with lightweight cloning and state hashing."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .entities import Base, Bullet, Tank
from .types import DEFAULT_MAX_TURNS, MAX_ACTIVE_BULLETS_PER_TANK

Coord = Tuple[int, int]


class GameState:
    """Authoritative state of the Tank Battle Game at a given turn/ply.

    Components (Zero-Sum Game Formulation):
    - width, height: grid dimensions (rows = height, cols = width)
    - tanks: {1: Tank, 2: Tank}
    - bases: {1: Base, 2: Base}
    - walls: {(row, col): hp} for destructible walls (1 <= hp <= 3)
    - steel_walls: frozenset of indestructible wall coordinates (optional)
    - bullets: list of active Bullet objects currently in flight
    - current_player: 1 (MAX) or 2 (MIN)
    - turn: current ply counter
    - max_turns: horizon limit to prevent infinite games
    """

    def __init__(
        self,
        width: int,
        height: int,
        tanks: Dict[int, Tank],
        bases: Dict[int, Base],
        walls: Dict[Coord, int],
        bullets: Optional[List[Bullet]] = None,
        current_player: int = 1,
        turn: int = 0,
        max_turns: int = DEFAULT_MAX_TURNS,
        steel_walls: Optional[frozenset[Coord]] = None,
    ) -> None:
        self.width = width
        self.height = height
        self.tanks = tanks
        self.bases = bases
        self.walls = walls
        self.bullets: List[Bullet] = bullets if bullets is not None else []
        self.current_player = current_player
        self.turn = turn
        self.max_turns = max_turns
        self.steel_walls: frozensenset[Coord] = steel_walls or frozenset()
        self.events: List[dict] = []  # collision/hit events from the most recent transition

    def clone(self) -> "GameState":
        """Fast shallow-structural clone avoiding copy.deepcopy overhead in search."""
        return GameState(
            width=self.width,
            height=self.height,
            tanks={pid: t.clone() for pid, t in self.tanks.items()},
            bases={pid: b.clone() for pid, b in self.bases.items()},
            walls=dict(self.walls),
            bullets=[b.clone() for b in self.bullets],
            current_player=self.current_player,
            turn=self.turn,
            max_turns=self.max_turns,
            steel_walls=self.steel_walls,
        )

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.height and 0 <= c < self.width

    def is_cell_blocked(self, r: int, c: int) -> bool:
        """True if cell (r, c) is out of bounds or occupied by a wall, base, or tank."""
        if not self.in_bounds(r, c):
            return True
        pos = (r, c)
        if pos in self.walls or pos in self.steel_walls:
            return True
        for base in self.bases.values():
            if base.is_alive and base.pos == pos:
                return True
        for tank in self.tanks.values():
            if tank.is_alive and tank.pos == pos:
                return True
        return False

    def count_active_bullets(self, player_id: int) -> int:
        return sum(1 for b in self.bullets if b.owner_id == player_id)

    def can_fire(self, player_id: int) -> bool:
        return self.count_active_bullets(player_id) < MAX_ACTIVE_BULLETS_PER_TANK

    def is_terminal(self) -> bool:
        """Game ends when any tank or base is destroyed or turn reaches max_turns."""
        for p in (1, 2):
            if not self.tanks[p].is_alive or not self.bases[p].is_alive:
                return True
        return self.turn >= self.max_turns

    def get_winner(self) -> Optional[int]:
        """Return 1 if Player 1 wins, 2 if Player 2 wins, 0 for draw, None if ongoing."""
        p1_alive = self.tanks[1].is_alive and self.bases[1].is_alive
        p2_alive = self.tanks[2].is_alive and self.bases[2].is_alive

        if not p1_alive and not p2_alive:
            return 0  # simultaneous destruction -> draw
        if not p2_alive:
            return 1  # Player 1 wins
        if not p1_alive:
            return 2  # Player 2 wins
        if self.turn >= self.max_turns:
            # Tie-breaker on timeout: compare total remaining HP, else draw (0)
            p1_hp = self.tanks[1].hp + self.bases[1].hp
            p2_hp = self.tanks[2].hp + self.bases[2].hp
            if p1_hp > p2_hp:
                return 1
            if p2_hp > p1_hp:
                return 2
            return 0
        return None

    def state_key(self) -> tuple:
        """Hashable canonical key representing the board configuration for Transposition Tables."""
        t1, t2 = self.tanks[1], self.tanks[2]
        b1, b2 = self.bases[1], self.bases[2]
        walls_tuple = tuple(sorted(self.walls.items()))
        bullets_tuple = tuple((b.owner_id, b.row, b.col, b.direction.value) for b in self.bullets)
        return (
            self.current_player,
            (t1.row, t1.col, t1.direction.value, t1.hp),
            (t2.row, t2.col, t2.direction.value, t2.hp),
            (b1.hp, b2.hp),
            walls_tuple,
            bullets_tuple,
        )

    def to_dict(self) -> dict:
        """Serialize state to a plain dictionary for safe external student plugin access."""
        return {
            "width": self.width,
            "height": self.height,
            "current_player": self.current_player,
            "turn": self.turn,
            "max_turns": self.max_turns,
            "tanks": {pid: t.to_dict() for pid, t in self.tanks.items()},
            "bases": {pid: b.to_dict() for pid, b in self.bases.items()},
            "walls": {f"{r},{c}": hp for (r, c), hp in self.walls.items()},
            "walls_tuple_map": dict(self.walls),
            "steel_walls": list(self.steel_walls),
            "bullets": [b.to_dict() for b in self.bullets],
        }
