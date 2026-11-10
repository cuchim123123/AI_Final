# N-Queens Problem: Propositional Logic (PySAT) & Local Search (Min-Conflicts)

An end-to-end Object-Oriented implementation and empirical study of the **$N$-Queens Problem** using:
1. **Propositional Logic & SAT Solving** via `Glucose3` from the `python-sat` (PySAT) library.
2. **Local Search & Min-Conflicts** (Lecture 08) with proposed variable-selection heuristics, greedy initialization, and random restarts.
3. **Interactive PySide6 Desktop GUI** with live chessboard rendering, step-by-step search animation, real-time convergence graphing, experiment runner, and results browser.

---

## Table of Contents
1. [Requirements Mapping](#requirements-mapping)
2. [Installation & Setup](#installation--setup)
3. [Quick Start](#quick-start)
4. [Graphical User Interface (GUI) Guide](#graphical-user-interface-gui-guide)
5. [Command Line Interface (CLI) Guide & All Configurations](#command-line-interface-cli-guide--all-configurations)
6. [Experimental Results Summary](#experimental-results-summary)
7. [Verification & Testing](#verification--testing)
8. [Architecture & OOP Design](#architecture--oop-design)

---

## Requirements Mapping

| Assignment Requirement | Implementation & Deliverables | Points |
|---|---|:---:|
| **1. Propositional Formulation & CNF** | Variables $X(r, c)$, $O(N^2)$ constraint discovery (`nqueens/constraints.py`), De Morgan CNF conversion (`nqueens/cnf.py`), closed-form clause proofs in [`docs/formulation.md`](docs/formulation.md). | **1.0 pt** |
| **2. PySAT Glucose3 Solver & Experiments** | `SATSolver` (`nqueens/solvers/sat_solver.py`), benchmark runner over $N \ge 4$, clause counts $\Theta(N^3)$, runtime logging, [`results/sat_results.csv`](results/sat_results.csv), and plots. | **1.0 pt** |
| **3. Min-Conflicts & Proposed Heuristics** | One-queen-per-column representation (`nqueens/solvers/conflict_tracker.py`), baseline random selector vs. proposed $H_1$ Max-Conflict and $H_2$ Weighted-Conflict selectors, 30 paired seeded runs up to $N=1000$. | **1.0 pt** |
| **Notice: OOP Principles** | Fully modular architecture using Strategy, Factory, and Dependency Injection patterns. Complete unit test suite (116 tests). | **Required** |

---

## Installation & Setup

### Environment Requirements
* Python 3.10 or 3.11 (Note: `python-sat` wheels on Windows currently require Python $\le$ 3.12).
* OS: Windows, macOS, or Linux.

### Setup (Windows / PowerShell)
```powershell
# Create a Python 3.11 virtual environment
py -3.11 -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install all project dependencies (PySAT, PySide6, NumPy, Matplotlib, Pandas, Pytest)
pip install -r requirements.txt
```

---

## Quick Start

```powershell
# 1. Run all unit tests (116 tests must pass)
python -m pytest -q

# 2. Launch the Graphical User Interface (PySide6)
python gui_main.py

# 3. Run a quick CLI demo (N=8)
python main.py demo --n 8
```

---

## Graphical User Interface (GUI) Guide

Launch the desktop application via:
```powershell
python gui_main.py
```

The GUI is fully themed with an adaptive, high-contrast **Dark Theme (Default)** and an optional **Light Theme** (switchable via `View -> Theme` in the menu bar).

### Tab 1: 🎯 Solve & Inspect
Allows interactive solving and visualization of individual $N$-Queens boards.
* **Controls:**
  * **Queens ($N$):** Integer spinner from $N=4$ up to $500$.
  * **Algorithm Family:**
    * **PySAT (Glucose3):** Choose At-Most-One encoding (`pairwise` [Baseline] vs `sequential` [Optimized]), toggle redundant Column ALO clauses, and configure the per-solve timeout in seconds.
    * **Min-Conflicts:** Choose variable selection heuristic (`random` [Baseline], `max` [Proposed $H_1$], `weighted` [Proposed $H_2$]), start state (`random` vs `greedy`), toggle random restarts, set restart step factor, and optional random seed.
  * **⚡ Solve Board:** Solves the problem in a background worker thread (GUI never freezes).
  * **✖ Cancel:** Immediately interrupts the solver.
  * **📋 Copy Equivalent CLI Command:** Generates the exact `main.py` CLI command matching your GUI settings and copies it to your clipboard.
* **Visualization & Metrics:**
  * **Chessboard Canvas:** Checkered wood tiles, unicode queen glyphs (`♛`), soft-red highlighted tiles for attacking queens, and blue highlights for the last moved queen. Tooltips show square coordinates and conflict counts on hover.
  * **Stat Cards:** Execution wall time, search steps / clause count, attacking pairs, and independent validation status.

### Tab 2: 🎬 Local Search Visualizer
An interactive animator that renders the internal execution of the Min-Conflicts algorithm step-by-step.
* **Controls:**
  * Configure $N$, heuristic ($H_1$ Max-Conflict, $H_2$ Weighted, or Random), start state, restarts, and seed.
  * **Animation Speed Slider:** Adjust delay from $5\text{ ms}$ (super fast) to $500\text{ ms}$ per step.
  * **Playback Buttons:**
    * **▶ Start:** Begins the search animation.
    * **⏸ Pause / Resume:** Pauses execution at any intermediate step.
    * **⏭ Step Once:** Manually advances the algorithm by exactly one repair step while paused.
    * **⏹ Reset:** Stops and clears the animation.
* **Live Telemetry:**
  * Displays current step number, remaining attacking pairs, conflicted queen count, and restart count.
  * **Live Convergence Curve:** Dynamically plots Total Conflicts vs Steps in real time using an embedded Matplotlib canvas.

### Tab 3: 📊 Experiment Runner
Run batch experiments and benchmarks directly from the GUI.
* **Experiment Modes:**
  * **R2: SAT Glucose3 Benchmark:** Evaluates clause counts and solve times over increasing $N$.
  * **R3: Min-Conflicts Heuristics:** Runs paired comparisons across Random, Max-Conflict, and Weighted-Conflict selectors.
  * **Optimizations vs Baseline:** Evaluates baseline vs. greedy initialization and random restarts.
* **Inputs & Presets:**
  * Custom comma-separated $N$ list (or click **⚡ Quick** / **📊 Full Range** presets).
  * Runs / repeats spinner and per-solve timeout limits.
* **Features:**
  * Non-blocking background worker with a live progress bar and status text.
  * Sortable summary table of all metrics.
  * Comparison ratios table with color-coded badges ($< 1.0$ in green = improved/cheaper, $> 1.0$ in red = costlier).
  * Embedded Matplotlib charts tab.
  * **💾 Export:** Saves CSV tables and PNG charts directly to the `results/` folder with custom filename tags.

### Tab 4: 📂 Results Browser
Browse and present previous experimental outputs without re-running long benchmarks.
* Lists all generated CSV datasets in `results/` and `results/baseline_snapshot/`.
* Displays table contents in a clean, sortable view.
* Automatically locates and renders matching PNG plot figures in an embedded gallery.

---

## Command Line Interface (CLI) Guide & All Configurations

All CLI commands are executed via `main.py`.

### 1. `demo` Command (Single Board Execution)
Solves a single board using both SAT (Glucose3) and Min-Conflicts, prints metrics, and prints board representations for $N \le 40$.

```powershell
python main.py demo [OPTIONS]
```
| Argument | Type | Default | Description |
|---|:---:|:---:|---|
| `--n` | int | `8` | Board dimension $N$ (number of queens). |
| `--seed` | int | `0` | Random seed for reproducible search. |
| `--encoding` | `pairwise` \| `sequential` | `pairwise` | At-Most-One CNF encoding for SAT (`pairwise` = baseline, `sequential` = optimized). |
| `--selector` | `random` \| `max` \| `weighted` | `random` | Min-Conflicts variable heuristic (`random` = baseline, `max` = $H_1$, `weighted` = $H_2$). |
| `--init` | `random` \| `greedy` | `random` | Min-Conflicts initial state (`random` = baseline, `greedy` = optimized). |
| `--restarts` | flag | `False` | Enable random restarts when local search stalls. |
| `--restart-factor` | int | `10` | Step budget before restarting an attempt ($K \cdot N$ steps). |
| `--max-steps-factor` | int | `100` | Total step budget ($M \cdot N$ steps). |

**Examples:**
```powershell
# Run baseline demo for N=8
python main.py demo --n 8

# Run demo with all optimizations (N=16, Max-Conflict, Greedy start, Restarts, Sequential SAT)
python main.py demo --n 16 --selector max --init greedy --restarts --encoding sequential
```

---

### 2. `sat` Command (Requirement 2 Experiments)
Runs PySAT `Glucose3` across increasing values of $N \ge 4$, logs clause counts and pure solve times, exports `results/sat_results.csv`, and generates PNG plots.

```powershell
python main.py sat [OPTIONS]
```
| Argument | Type | Default | Description |
|---|:---:|:---:|---|
| `--ns` | int... | `4 5 6 8 10 12 16 20 24 32 40 50 64 80 100` | List of $N$ values to benchmark. |
| `--repeats` | int | `5` | Repetitions per $N$ to compute mean and std dev. |
| `--time-limit` | float | `60.0` | Timeout in seconds per solve. Times out gracefully and skips larger $N$. |
| `--column-alo` | flag | `False` | Add redundant at-least-one clauses per column. |
| `--encodings` | str... | `pairwise` | Encodings to evaluate: `pairwise`, `sequential`, or both. |
| `--tag` | str | `sat` | Filename prefix for exported CSV and PNG files. |

**Examples:**
```powershell
# Run full R2 baseline benchmark (N=4 to 100)
python main.py sat

# Fast test run with 3 repeats
python main.py sat --ns 4 8 16 32 --repeats 3

# Compare Pairwise vs. Sequential Counter encodings
python main.py sat --encodings pairwise sequential --time-limit 30 --tag sat_cmp
```

---

### 3. `compare` Command (Requirement 3 Experiments)
Conducts paired comparison experiments evaluating standard Min-Conflicts (`random`) against the proposed heuristics (`max` and `weighted`) with identical seeds across all variants.

```powershell
python main.py compare [OPTIONS]
```
| Argument | Type | Default | Description |
|---|:---:|:---:|---|
| `--ns` | int... | `8 16 32 64 128 256 512 1000` | Board sizes to benchmark. |
| `--runs` | int | `30` | Number of paired runs per cell (seeds $0$ to $\text{runs}-1$). |
| `--init` | `random` \| `greedy` | `random` | Initial state strategy. |
| `--restarts` | flag | `False` | Toggle random restarts. |
| `--restart-factor` | int | `10` | Steps per restart attempt ($K \cdot N$). |
| `--max-steps-factor` | int | `100` | Maximum step budget ($M \cdot N$). |
| `--tag` | str | `minconf` | Output filename prefix. |

**Examples:**
```powershell
# Run full R3 benchmark (N=8 to 1000, 30 runs per cell)
python main.py compare

# Quick comparison (N=8, 16, 32 with 10 runs)
python main.py compare --ns 8 16 32 --runs 10
```

---

### 4. `optimize` Command (Ablation Study)
Benchmarks the baseline configuration against greedy initialization, random restarts, and both combined across the heuristics. Outputs ratio tables where values $< 1.0$ indicate improvement over the baseline.

```powershell
python main.py optimize [OPTIONS]
```
| Argument | Type | Default | Description |
|---|:---:|:---:|---|
| `--ns` | int... | `8 16 32 64 128 256 512 1000` | Board sizes. |
| `--runs` | int | `30` | Paired runs per configuration. |
| `--selectors` | str... | `random max` | Heuristics to test under optimization. |
| `--max-steps-factor` | int | `100` | Total step budget factor. |
| `--restart-factor` | int | `10` | Restart cutoff factor. |
| `--tag` | str | `opt` | Output prefix (writes `opt_summary.csv` and `opt_vs_baseline.csv`). |

**Example:**
```powershell
python main.py optimize --ns 8 16 32 64 --runs 10
```

---

### 5. `minconf` Command (Single Variant Benchmark)
Runs batch experiments for one specific Min-Conflicts configuration.

```powershell
python main.py minconf --selector max --init greedy --restarts --ns 64 128 --runs 20
```

---

## Experimental Results Summary

### R2: PySAT Glucose3 Results (Mean of 5 runs)
* **Theoretical Closed Form:** Total Clauses $= N + 2N\binom{N}{2} + 4\binom{N}{3} + 2\binom{N}{2} = \Theta(N^3)$.
* The pairwise formula generates **80 clauses** at $N=4$, **736 clauses** at $N=8$, and **1,646,800 clauses** at $N=100$.

| $N$ | Variables | Clauses | Build Time (s) | Solve Time (s) | Valid |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **4** | 16 | 80 | 0.00010 | 0.00001 | **True** |
| **8** | 64 | 736 | 0.00578 | 0.00017 | **True** |
| **16** | 256 | 6,336 | 0.00300 | 0.00232 | **True** |
| **32** | 1,024 | 52,608 | 0.05332 | 0.01978 | **True** |
| **64** | 4,096 | 428,800 | 0.43368 | 0.19836 | **True** |
| **100** | 10,000 | 1,646,800 | 1.52487 | 7.39450 | **True** |

* **Analysis:** Solve time is non-monotonic due to CDCL heuristic branching (e.g., $N=64$ solved faster than $N=50$). The sequential counter encoding cuts clauses from $\Theta(N^3)$ to $\Theta(N^2)$, but weakens unit propagation in Glucose3, making it slower for finding single satisfying assignments.

---

### R3: Min-Conflicts Heuristics Comparison (30 paired runs per cell)

| $N$ | `random` (Baseline): Success / Steps | `max` ($H_1$ Proposed): Success / Steps | `weighted` ($H_2$ Proposed): Success / Steps |
|:---:|:---:|:---:|:---:|
| **8** | 93.3% / 36.7 | 83.3% / 52.6 | 93.3% / 45.6 |
| **16** | 100.0% / 99.2 | 86.7% / 76.3 | 100.0% / **64.5** |
| **32** | 100.0% / 95.5 | 100.0% / **77.1** | 100.0% / 87.6 |
| **64** | 100.0% / 104.3 | 100.0% / 105.2 | 100.0% / 108.3 |
| **128** | 100.0% / 154.5 | 100.0% / **139.0** | 100.0% / 149.1 |
| **256** | 100.0% / 238.5 | 100.0% / **204.9** | 100.0% / 232.7 |
| **512** | 100.0% / 406.0 | 100.0% / **339.0** | 100.0% / 375.4 |
| **1000** | 100.0% / 702.7 | 100.0% / **565.4** | 100.0% / 658.0 |

* **Analysis:**
  * At large $N$ ($N \ge 128$), the proposed **Max-Conflict heuristic ($H_1$) outperforms the baseline by $\approx 19.5\%$ in search steps** and $\approx 17\%$ in wall-clock time.
  * On small boards ($N \le 16$), pure greedy selection can oscillate in local plateaus without restarts.
  * **Optimizations:** Adding **Random Restarts** completely resolves this, raising the success rate to **100% across all $N$**. Adding a **Greedy Initial State** reduces steps at $N=1000$ down to only **$53.2$ steps** ($\approx 13\times$ reduction).

---

## Verification & Testing

The project includes an automated test suite of **116 unit tests** covering mathematical formulas, solver correctness, heuristic mechanics, and headless GUI components:

```powershell
python -m pytest -q
```

### Key Invariant Checks in the Test Suite:
1. `test_clause_count_formula`: Validates that `CNFEncoder` matches the closed-form equation for $N=4$ to $10$.
2. `test_sat_solves`: Ensures every solution returned by Glucose3 passes independent verification (`Board.is_valid() == True`).
3. `test_sat_unsat_small`: Confirms $N=2$ and $N=3$ return `UNSAT`.
4. `test_baseline_is_unchanged`: Regression test locking in 9 exact pinned step counts to prove refactoring did not alter baseline mechanics.
5. `test_reproducible`: Confirms identical seeds yield identical search trajectories.
6. `test_gui_headless`: Validates that all PySide6 views, widgets, and worker threads instantiate and execute cleanly in offscreen mode.

---

## Architecture & OOP Design

The codebase strictly adheres to Object-Oriented Programming and clean software design:

```
AI_Final/
├── main.py                     # CLI entry point (argument parsing and dispatch only)
├── gui_main.py                 # Desktop GUI launcher
├── requirements.txt            # Dependency manifest
├── docs/
│   ├── formulation.md          # Formal Propositional Logic discussion (R1)
│   ├── gui_analysis.md         # GUI architecture & design document
│   └── GUI_PROMPT.md           # Specification prompt
├── nqueens/                    # Core library (pure Python, zero GUI coupling)
│   ├── board.py                # Board: coordinates, validation, attacking pair counting
│   ├── constraints.py          # Line, ConstraintGenerator: O(N^2) constraint discovery
│   ├── amo.py                  # AtMostOneEncoder (ABC): PairwiseAMO vs SequentialCounterAMO
│   ├── cnf.py                  # CNFEncoder: variable mapping and clause compilation
│   ├── result.py               # SolveResult dataclass
│   ├── factory.py              # Centralized factory (build_sat, build_min_conflicts)
│   ├── solvers/
│   │   ├── base.py             # Solver (ABC)
│   │   ├── sat_solver.py       # SATSolver: Glucose3 wrapper with timeouts & cancellation
│   │   ├── conflict_tracker.py # ConflictTracker: incremental O(1) conflict counters
│   │   ├── selectors.py        # VariableSelector (ABC): Random, MaxConflict, WeightedConflict
│   │   ├── initializers.py     # Initializer (ABC): RandomInitializer, GreedyInitializer
│   │   └── min_conflicts.py    # MinConflictsSolver: local search engine
│   └── experiments/
│       ├── runner.py           # SATExperiment, MinConflictsExperiment
│       ├── variants.py         # Declarative benchmark variant builders
│       └── plotting.py         # Plotter: Matplotlib chart generation
├── nqueens_gui/                # PySide6 desktop application
│   ├── app.py                  # MainWindow container, menubar, statusbar
│   ├── styles.py               # Complete dark and light stylesheets (QSS)
│   ├── workers.py              # QThread background execution workers
│   ├── widgets/
│   │   ├── board_view.py       # Custom-painted chessboard widget
│   │   ├── chart_widget.py     # Embedded Matplotlib canvas & real-time convergence plot
│   │   └── stat_card.py        # Metric summary card
│   └── views/
│       ├── solve_view.py       # Tab 1: Single run solver & board viewer
│       ├── visualizer_view.py  # Tab 2: Min-Conflicts step-by-step animator
│       ├── experiment_view.py  # Tab 3: Interactive experiment runner
│       └── results_view.py     # Tab 4: Results file browser
├── results/                    # Exported CSV data tables and PNG figures
│   └── baseline_snapshot/      # Preserved baseline CSV snapshot
└── tests/                      # Automated test suite (116 tests)
    ├── test_board_constraints.py
    ├── test_encoding_sat.py
    ├── test_min_conflicts.py
    ├── test_sat_time_limit.py
    ├── test_gui_hooks.py
    └── test_gui.py
```
