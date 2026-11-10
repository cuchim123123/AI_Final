# AI Endterm Project (`AI_Final`)
## Task 1: $N$-Queens (Propositional Logic & Min-Conflicts) · Task 2: Tank Battle (Adversarial Search) · Task 3: Kakuro (CSP)

This repository contains the complete, modular Object-Oriented implementations, GUI applications, and experimental benchmarks for all three Endterm tasks:
- **[`task1_nqueens/`](task1_nqueens/)** — **Task 1 (3.0 Points):** $N$-Queens Problem using Propositional Logic (`PySAT` `Glucose3`), Local Search (`Min-Conflicts` with proposed heuristics $H_1$ Max-Conflict and $H_2$ Weighted-Conflict), and an interactive **PySide6 GUI**.
- **[`task2_tank_battle/`](task2_tank_battle/)** — **Task 2 (3.0 Points):** Turn-Based Zero-Sum **Tank Battle Game** controlled by Adversarial Search (**Minimax**, **Alpha-Beta Pruning**, **Heuristic Minimax**, and **Heuristic Minimax + Alpha-Beta**), with an interactive **PyGame GUI** and a dynamic **External Student Plugin Loader**.
- **[`task3_kakuro/`](task3_kakuro/)** — **Task 3 (3.0 Points):** $9 \times 9$ **Kakuro** puzzle modeled as a **Constraint Satisfaction Problem (CSP)** and solved with **Backtracking Search**, **Constraint Propagation**, **Forward Checking**, and the **MRV**, **Degree**, and **LCV** heuristics, with an independent solution validator and an interactive **Tkinter GUI**.

---

## 1. Environment Setup (Shared `.venv`)

```powershell
# 1. Create a Python 3.11 virtual environment
py -3.11 -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install all dependencies (Task 3 needs no extra packages; Tkinter ships with Python on Windows)
pip install -r requirements.txt

# 4. Run the Task 1 + Task 2 test suite (134 tests)
.\.venv\Scripts\python -m pytest -q

# 5. Run the Task 3 test suite (3 unittest tests, configured separately from pytest.ini)
cd task3_kakuro
..\.venv\Scripts\python -m unittest discover -s tests -v
cd ..
```

---

## 2. Task 1: $N$-Queens Problem — Propositional Logic & Min-Conflicts (`task1_nqueens/`)

### Requirements Mapping (3.0 Points)
| Requirement | Implementation & Deliverables | Points |
| :--- | :--- | :---: |
| **R1. Propositional Formulation & CNF** | Variables $X(r, c)$, $O(N^2)$ constraint discovery (`task1_nqueens/nqueens/constraints.py`), De Morgan CNF conversion (`task1_nqueens/nqueens/cnf.py`), closed-form clause proofs in [`task1_nqueens/docs/formulation.md`](task1_nqueens/docs/formulation.md). | **1.0 pt** |
| **R2. PySAT Glucose3 Solver & Experiments** | `SATSolver` (`task1_nqueens/nqueens/solvers/sat_solver.py`), benchmark runner over $N \ge 4$, clause counts $\Theta(N^3)$, runtime logging, [`task1_nqueens/results/sat_results.csv`](task1_nqueens/results/sat_results.csv), and plots. | **1.0 pt** |
| **R3. Min-Conflicts & Proposed Heuristics** | One-queen-per-column incremental conflict tracker, baseline random selector vs. proposed $H_1$ Max-Conflict and $H_2$ Weighted-Conflict selectors, 30 paired seeded runs up to $N=1000$ in [`task1_nqueens/results/`](task1_nqueens/results/). | **1.0 pt** |

### Quick Start Commands (Task 1)
```powershell
# Launch the PySide6 Desktop GUI for N-Queens
.\.venv\Scripts\python task1_nqueens/gui_main.py

# Run a quick N-Queens CLI demo (N=8)
.\.venv\Scripts\python task1_nqueens/main.py demo --n 8

# Run SAT and Min-Conflicts benchmarks
.\.venv\Scripts\python task1_nqueens/main.py sat --n-values 4 8 12 16 20 25 30 --encoding both
.\.venv\Scripts\python task1_nqueens/main.py mc --n-values 8 20 50 100 200 --trials 10
```
- Full details: [`task1_nqueens/README.md`](task1_nqueens/README.md) and [`task1_nqueens/docs/formulation.md`](task1_nqueens/docs/formulation.md).

---

## 3. Task 2: Adversarial Search — Tank Battle Game (`task2_tank_battle/`)

### Requirements Mapping (3.0 Points)
| Requirement | Implementation & Deliverables | Points |
| :--- | :--- | :---: |
| **R1. Zero-Sum Game Formulation** | Formal mathematical definition of $\mathcal{G} = \langle S_0, \text{Players}, \text{Actions}, \text{Result}, \text{Terminal-Test}, U \rangle$, cell-by-cell speed-3 bullet physics, and application of Minimax, Alpha-Beta, and Heuristic Minimax in [`task2_tank_battle/docs/formulation.md`](task2_tank_battle/docs/formulation.md). | **1.0 pt** |
| **R2. Tank Control & 4-Way Experimental Comparison** | Configurable `AdversarialSearchEngine` (`task2_tank_battle/tank_battle/search/minimax.py`) with `TacticalHeuristicEvaluator`, `MoveOrderer`, and `TranspositionTable`. Benchmarks & tournaments across **1. Minimax**, **2. Alpha-Beta**, **3. Heuristic Minimax**, and **4. Heuristic Minimax + Alpha-Beta** in [`task2_tank_battle/results/`](task2_tank_battle/results/). | **1.5 pts** |
| **R3. PyGame GUI & External Group Plugin System** | Interactive **PyGame GUI** (`task2_tank_battle/gui_main.py`) with live search telemetry and `PluginLoader` + `SandboxedAgentAdapter` (`task2_tank_battle/external_agents/`) to import and compete against other student groups' algorithms. | **0.5 pt** |

### Quick Start Commands (Task 2)
```powershell
# Launch the interactive PyGame GUI
.\.venv\Scripts\python task2_tank_battle/gui_main.py

# Play a terminal match with ASCII board visualization
.\.venv\Scripts\python task2_tank_battle/main.py demo --p1 heuristic_alphabeta --p2 alphabeta --map skirmish --depth 3

# Run the R2 4-configuration search benchmark (generates CSV + 3 PNG plots in task2_tank_battle/results/)
.\.venv\Scripts\python task2_tank_battle/main.py benchmark --depths 1 2 3 4 --trials 3

# Run the R2 head-to-head double round-robin tournament (generates CSVs + tournament PNG plot)
.\.venv\Scripts\python task2_tank_battle/main.py tournament --depth 3 --maps skirmish standard
```

### Task 2 Experimental Highlights
- **Alpha-Beta Pruning Efficiency:** Reduces explored game states by **60%–96.4%** at depth 4 while returning the **exact same minimax value** as unpruned Minimax, cutting decision latency from **22.89 ms down to 1.56 ms** (**14.7$\times$ speedup**).
- **Tournament Performance ($d = 3$, 16 games per agent with side-swapping):**
  - **4. Heuristic Minimax + Alpha-Beta:** **87.5% win rate** (`13W-2D-1L`), **2.94 ms/move**, **71.7 states/move**.
  - **3. Heuristic Minimax Search:** **62.5% win rate** (`9W-2D-5L`), 7.66 ms/move, 255.3 states/move.
  - **2. Alpha-Beta Search:** **50.0% win rate** (`7W-2D-7L`), **1.33 ms/move**, **102.8 states/move**.
  - **1. Minimax Search:** **50.0% win rate** (`7W-2D-7L`), 3.13 ms/move, 254.6 states/move.
- Full details: [`task2_tank_battle/README.md`](task2_tank_battle/README.md) and [`task2_tank_battle/docs/formulation.md`](task2_tank_battle/docs/formulation.md).

---

## 4. Task 3: Kakuro — Constraint Satisfaction Problem (`task3_kakuro/`)

### CSP Formulation & Deliverables
| Component | Implementation & Deliverables |
| :--- | :--- |
| **Puzzle data** | $9 \times 9$ grid with **48 white cells** and **28 clue groups** (14 horizontal + 14 vertical) in `task3_kakuro/kakuro/board.py`. `validate_puzzle_definition()` checks that every group only contains white cells, that each sum is feasible for the group size, and that every white cell belongs to exactly one horizontal and one vertical group. |
| **Variables & Domains** | Each white cell is a variable with initial domain $\{1, \dots, 9\}$ (`task3_kakuro/kakuro/csp.py`). |
| **Constraints** | For every group: the values **sum to the clue** and are **all different**. Group support is computed by `group_supports`, which prunes partial assignments with min/max sum bounds. |
| **Backtracking Search** | `KakuroSolver` (`task3_kakuro/kakuro/solver.py`) with `nodes` / `backtracks` counters and an event callback that feeds the GUI. |
| **Variable & Value Ordering** | `task3_kakuro/kakuro/heuristics.py`: **MRV** (smallest remaining domain), **Degree Heuristic** as tie-breaker (most unassigned neighbours sharing a group), and **LCV** (least constraining value first). |
| **Constraint Propagation & Forward Checking** | `task3_kakuro/kakuro/propagation.py`: group-wise domain filtering repeated until a fixed point (run once before the search and again after every assignment). Forward Checking assigns a value on a copy of the domains, propagates, and rejects the value on any empty domain. |
| **Independent Validator** | `task3_kakuro/kakuro/validator.py` re-checks all 48 cells (range $1..9$) and all 28 groups (sum and uniqueness) without using any solver code, and prints a per-group report. |
| **Tkinter GUI** | `task3_kakuro/ui/app.py`: board view plus a live log of the algorithm (variable selection, domain reductions, tries, backtracks, contradictions), with *Solve* and *Reset* buttons. The solver runs in a worker thread and communicates with the UI through a queue. |

### Quick Start Commands (Task 3)
```powershell
# Solve in the terminal (prints the grid, validation result and statistics)
.\.venv\Scripts\python task3_kakuro/main.py

# Also print the 28-group verification report
.\.venv\Scripts\python task3_kakuro/main.py --groups

# Launch the Tkinter GUI
.\.venv\Scripts\python task3_kakuro/main.py --ui

# Run the Task 3 unit tests (from inside task3_kakuro/)
cd task3_kakuro
..\.venv\Scripts\python -m unittest discover -s tests -v
```

### Task 3 Experimental Highlights
- **Solved & verified:** the solver returns a complete assignment for all **48 cells**, and the validator confirms the sum and uniqueness of **all 28 groups** (`PASS`).
- **Search effort:** **48 nodes**, **0 backtracks**, **159 propagation steps** — Constraint Propagation + Forward Checking + MRV/Degree/LCV solve this puzzle without any backtracking.
- **Tests:** 3 `unittest` tests (puzzle definition is consistent, solver output is valid, validator rejects a corrupted solution).
- Full details: [`task3_kakuro/README.md`](task3_kakuro/README.md).

---

## 5. Repository Directory Structure

```text
source/
├── README.md                            # Unified guide for Task 1, Task 2 & Task 3
├── requirements.txt                     # Shared dependencies (python-sat, pyside6, pygame, numpy, pandas, matplotlib, pytest)
├── pytest.ini                           # Pytest configuration (134 tests for Task 1 & Task 2)
├── task1_nqueens/                       # Task 1: N-Queens (Propositional Logic & Min-Conflicts)
│   ├── main.py                          # Task 1 CLI
│   ├── gui_main.py                      # Task 1 PySide6 GUI
│   ├── README.md                        # Task 1 detailed guide
│   ├── docs/formulation.md              # Task 1 formal CNF & Min-Conflicts report
│   ├── results/                         # Task 1 CSVs & Matplotlib charts
│   ├── nqueens/                         # Task 1 core & solvers
│   ├── nqueens_gui/                     # Task 1 PySide6 GUI components
│   └── tests/                           # 116 Task 1 unit tests
├── task2_tank_battle/                   # Task 2: Tank Battle Game (Adversarial Search)
│   ├── main.py                          # Task 2 CLI (demo, benchmark, tournament)
│   ├── gui_main.py                      # Task 2 PyGame GUI
│   ├── README.md                        # Task 2 detailed guide
│   ├── docs/formulation.md              # Task 2 formal Zero-Sum Game & experimental report
│   ├── external_agents/                 # External student group plugin directory & guide
│   ├── results/                         # Task 2 CSVs & Matplotlib charts
│   ├── tank_battle/                     # Task 2 core, search, agents, experiments, gui
│   └── tests/                           # 18 Task 2 unit & GUI tests
└── task3_kakuro/                        # Task 3: Kakuro (Constraint Satisfaction Problem)
    ├── main.py                          # Task 3 CLI (solve, --groups, --ui)
    ├── README.md                        # Task 3 detailed guide
    ├── kakuro/                          # Task 3 core: board, csp, solver, heuristics, propagation, validator
    ├── ui/app.py                        # Task 3 Tkinter GUI
    └── tests/                           # 3 Task 3 unittest tests
```