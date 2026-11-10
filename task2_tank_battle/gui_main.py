"""PyGame GUI launcher for Task 2: Adversarial Search — Tank Battle Game."""
from __future__ import annotations

import argparse
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from tank_battle.core.maps import MAPS
from tank_battle.gui.app import TankBattleApp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch PyGame GUI for Task 2: Tank Battle Game"
    )
    parser.add_argument("--p1", default="heuristic_alphabeta", help="Initial Player 1 controller")
    parser.add_argument("--p2", default="alphabeta", help="Initial Player 2 controller")
    parser.add_argument("--map", default="standard", choices=list(MAPS.keys()))
    parser.add_argument("--depth", type=int, default=3, choices=[1, 2, 3, 4])
    args = parser.parse_args()

    ext_dir = os.path.join(THIS_DIR, "external_agents")
    app = TankBattleApp(
        external_dir=ext_dir,
        initial_p1=args.p1,
        initial_p2=args.p2,
        initial_map=args.map,
        initial_depth=args.depth,
    )
    app.run()


if __name__ == "__main__":
    main()
