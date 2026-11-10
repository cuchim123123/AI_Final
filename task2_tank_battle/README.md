# Task 2: Adversarial Search — Tank Battle Game (3.0 Points)

A complete, modular implementation of the turn-based **Zero-Sum Tank Battle Game** controlled by Lecture 07 Adversarial Search algorithms (**Minimax Search**, **Alpha-Beta Pruning**, **Heuristic Minimax Search**, and **Heuristic Minimax with Alpha-Beta Pruning**), featuring a real-time **PyGame GUI** and a sandboxed **External Student Plugin Loader**.

---

## 1. Game Rules & Physics Summary

| Entity | Initial HP | Damage per Hit | Notes |
| :--- | :---: | :---: | :--- |
| **Tank** (`T1`, `T2`) | `6` | `1` | Moves 1 cell/turn (`UP`, `DOWN`, `LEFT`, `RIGHT`); fires speed-3 bullets |
| **Base** (`B1`, `B2`) | `9` | `1` | Stationary command center |
| **Wall** (`W3`..`W1`) | `3` | `1` | Destructible brick wall; disappears at `0 HP` |

- **06 Tank Actions:** `MOVE_UP`, `MOVE_DOWN`, `MOVE_LEFT`, `MOVE_RIGHT`, `FIRE`, `STAY`.
- **Speed-3 Cell-by-Cell Bullet Physics:** Each game cycle, active bullets advance up to `3` cells in the firing direction, checked **cell-by-cell** (`sub_step = 1, 2, 3`). If a bullet hits a wall, base, tank, opposing bullet, or grid boundary on any cell, the collision triggers immediately and the bullet stops.
- **Terminal Condition:** The game ends immediately when either a **base** or a **tank** is destroyed (`HP <= 0`).

---

## 2. Quick Start & Commands

Run from the repository root (`f:\Desktop\AI_Endterm`) using the virtual environment `.venv`:

### Launch the Interactive PyGame GUI (Requirement 3)
```powershell
.\.venv\Scripts\python task2_tank_battle/gui_main.py
```

#### PyGame GUI Controls & Features:
- **Sidebar Buttons:**
  - **P1 / P2 Controller Selectors:** Cycle between `4. Heuristic Minimax + Alpha-Beta`, `3. Heuristic Minimax`, `2. Alpha-Beta`, `1. Minimax`, `Human (Keyboard WASD/Space)`, `Random`, and any discovered external student plugins (`plugin:*`).
  - **Search Depth Selector:** Cycle search depth `d = 1, 2, 3, 4`.
  - **Map Selector:** Cycle between `standard` (11x11 Battle City), `skirmish` (9x9 fast arena), `fortress` (11x11 corridor maze), `endgame` (7x7 close-quarters duel), and `dodge` (7x7 bullet evasion test).
  - **Start / Pause (`Space`):** Start or pause continuous simulation.
  - **Step 1 Turn (`N`):** Advance exactly one game cycle and inspect telemetry.
  - **Reset Match (`R`):** Reset the current map and controllers.
  - **Speed Selector:** Cycle `1x (3 t/s)`, `2x (6 t/s)`, `4x (12 t/s)`, `MAX`.
  - **Reload External Student Plugins (`P`):** Dynamically hot-reload `.py` agents from `task2_tank_battle/external_agents/`.
- **Human Keyboard Controls (when P1 or P2 is set to `Human`):**
  - `W` / `Up Arrow`: `MOVE_UP`
  - `S` / `Down Arrow`: `MOVE_DOWN`
  - `A` / `Left Arrow`: `MOVE_LEFT`
  - `D` / `Right Arrow`: `MOVE_RIGHT`
  - `F` / `Enter`: `FIRE`
  - `Q`: `STAY`

---

### Run the CLI Demo, Benchmark, and Tournament (Requirement 2)

```powershell
# 1. Play a terminal match with ASCII board visualization
.\.venv\Scripts\python task2_tank_battle/main.py demo --p1 heuristic_alphabeta --p2 alphabeta --map skirmish --depth 3

# 2. Run the 4-configuration search benchmark across scenarios & depths (saves CSV + 3 PNG plots)
.\.venv\Scripts\python task2_tank_battle/main.py benchmark --depths 1 2 3 4 --trials 3

# 3. Run the head-to-head double round-robin tournament (saves CSVs + win-rate PNG plot)
.\.venv\Scripts\python task2_tank_battle/main.py tournament --depth 3 --maps skirmish standard
```

### Run All Unit & Integration Tests
```powershell
.\.venv\Scripts\python -m pytest task2_tank_battle/tests -v
```

---

## 3. Integrating Other Student Groups' Algorithms (Requirement 3 Plugin System)

Drop any Python file into [`task2_tank_battle/external_agents/`](external_agents/) implementing **one** of three supported contracts (see [`external_agents/README_PLUGIN.md`](external_agents/README_PLUGIN.md) and [`external_agents/sample_student_agent.py`](external_agents/sample_student_agent.py)):

1. **Contract A (Subclass `BaseAgent`):**
   ```python
   from tank_battle.agents.base import BaseAgent
   from tank_battle.core.types import Action

   class CustomAgent(BaseAgent):
       def get_action(self, state) -> Action:
           return Action.FIRE
   ```
2. **Contract B (Duck-typed class `Agent` or `create_agent()` factory):**
   Any class with `get_action(state)` or `choose_action(obs_dict)` returning `"MOVE_UP"`, `"MOVE_DOWN"`, `"MOVE_LEFT"`, `"MOVE_RIGHT"`, `"FIRE"`, or `"STAY"`.
3. **Contract C (Standalone function `choose_action(state_dict) -> str`):**
   Zero imports from this repository required! Receives a plain serializable Python `dict` snapshot of the board and returns an action string.

`SandboxedAgentAdapter` automatically deep-copies the state before passing it to external code, catches exceptions, and validates returned actions (falling back to `STAY` on invalid outputs).

---

## 4. Architecture & File Structure

```text
task2_tank_battle/
├── main.py                              # CLI: demo, benchmark, tournament
├── gui_main.py                          # PyGame GUI entry point
├── PLAN_TASK2.md                        # Detailed architectural & implementation plan
├── docs/
│   └── formulation.md                   # R1 Zero-Sum formulation & R2 experimental analysis
├── external_agents/
│   ├── README_PLUGIN.md                 # Plugin specification for external student groups
│   └── sample_student_agent.py          # Reference external agent plugin
├── results/
│   ├── search_benchmark.csv             # R2 benchmark metrics across 4 configs & depths 1..4
│   ├── tournament_matches.csv           # Individual match results
│   ├── tournament_summary.csv           # Aggregated tournament standings
│   ├── states_vs_depth.png              # Log-scale explored game states vs depth
│   ├── time_vs_depth.png                # Log-scale execution time vs depth
│   ├── pruning_ratio.png                # Alpha-Beta state reduction percentage
│   └── tournament_winrates.png          # Tournament win rate & real-time speed comparison
├── tank_battle/
│   ├── factory.py                       # Factory for the 4 required configs & plugins
│   ├── core/                            # GameState, Tank, Base, Bullet, TransitionEngine, Maps
│   ├── search/                          # Minimax/Alpha-Beta, Evaluators, MoveOrderer, TT
│   ├── agents/                          # BaseAgent, SearchAgent, RandomAgent, PluginLoader
│   ├── experiments/                     # SearchBenchmark, TournamentRunner, Matplotlib plots
│   └── gui/                             # PyGame ArenaRenderer & TankBattleApp
└── tests/                               # Physics, Search Equivalence, Plugin, and GUI tests
```
