"""Experiment runners returning pandas DataFrames.

Runners know nothing about concrete solver classes: they receive *variants*,
i.e. a mapping `name -> factory`, so any configuration (baseline or
optimised) can be benchmarked with the same code.
"""
from __future__ import annotations

import statistics as st
import threading
from typing import Callable, Dict, List, Optional, Sequence

import pandas as pd

from ..solvers.base import Solver

# SAT variants build a solver without arguments; local-search variants take a seed.
SATFactory = Callable[[], Solver]
SeededFactory = Callable[[int], Solver]


class SATExperiment:
    """Glucose3 runs over increasing N: clause count and solve time per encoding.

    The per-solve time limit lives in the injected solvers (see `sat_variants`).
    When a solve times out, that N is recorded (`timed_out=True`, the time is
    the limit, i.e. a lower bound) and larger N are skipped for that variant.
    """

    DEFAULT_NS = [4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 50, 64, 80, 100]

    def __init__(self, variants: Dict[str, SATFactory],
                 ns: Optional[Sequence[int]] = None, repeats: int = 5) -> None:
        self.variants = variants
        self.ns = list(ns or self.DEFAULT_NS)
        self.repeats = repeats

    def run(self, verbose: bool = True,
            progress_callback: Optional[Callable[[int, int, str], None]] = None,
            cancel_event: Optional[threading.Event] = None) -> pd.DataFrame:
        rows: List[Dict] = []
        total_steps = len(self.variants) * len(self.ns)
        completed_steps = 0

        for name, factory in self.variants.items():
            solver = factory()
            for n in self.ns:
                if cancel_event and cancel_event.is_set():
                    break
                if progress_callback:
                    progress_callback(completed_steps, total_steps, f"{name} (N={n})")
                results = []
                for _ in range(self.repeats):
                    if cancel_event and cancel_event.is_set():
                        break
                    r = solver.solve(n)
                    results.append(r)
                    if r.extra.get("timed_out", False) or r.extra.get("cancelled", False):
                        break                       # no point repeating a timeout/cancel

                if not results or (cancel_event and cancel_event.is_set()):
                    break

                times = [r.time_s for r in results]
                timed_out = any(r.extra.get("timed_out", False) for r in results)
                row = {
                    "encoding": name,
                    "N": n,
                    "variables": results[0].extra["variables"],
                    "clauses": results[0].num_clauses,
                    "build_time_s": st.mean(r.extra["build_time_s"] for r in results),
                    "solve_time_mean_s": st.mean(times),
                    "solve_time_std_s": st.pstdev(times) if len(times) > 1 else 0.0,
                    "valid": all(r.solved for r in results),
                    "timed_out": timed_out,
                }
                rows.append(row)
                completed_steps += 1
                if progress_callback:
                    progress_callback(completed_steps, total_steps, f"{name} (N={n}) done")
                if verbose:
                    flag = " TIMED OUT" if timed_out else ""
                    print(f"{name:10s} N={n:4d} clauses={row['clauses']:9d} "
                          f"solve={row['solve_time_mean_s']:.5f}s "
                          f"valid={row['valid']}{flag}", flush=True)
                if timed_out:
                    break                           # skip larger N for this variant
            if cancel_event and cancel_event.is_set():
                break
        return pd.DataFrame(rows)


class MinConflictsExperiment:
    """Paired comparison of Min-Conflicts variants.

    Every variant is run with the *same seeds* (base_seed .. base_seed+runs-1)
    for each N, so differences are not due to luck of the draw.
    """

    DEFAULT_NS = [8, 16, 32, 64, 128, 256, 512, 1000]

    def __init__(self, variants: Dict[str, SeededFactory],
                 ns: Optional[Sequence[int]] = None, runs: int = 30,
                 base_seed: int = 0) -> None:
        self.variants = variants
        self.ns = list(ns or self.DEFAULT_NS)
        self.runs = runs
        self.base_seed = base_seed

    def run(self, verbose: bool = True,
            progress_callback: Optional[Callable[[int, int, str], None]] = None,
            cancel_event: Optional[threading.Event] = None) -> pd.DataFrame:
        """One row per (N, variant, seed)."""
        rows: List[Dict] = []
        total_runs = len(self.ns) * len(self.variants) * self.runs
        completed_runs = 0

        for n in self.ns:
            if cancel_event and cancel_event.is_set():
                break
            for name, factory in self.variants.items():
                if cancel_event and cancel_event.is_set():
                    break
                first = len(rows)
                for i in range(self.runs):
                    if cancel_event and cancel_event.is_set():
                        break
                    seed = self.base_seed + i
                    r = factory(seed).solve(n)
                    rows.append({"N": n, "variant": name, "seed": seed,
                                 "solved": r.solved, "steps": r.steps,
                                 "time_s": r.time_s,
                                 "restarts": r.extra.get("restarts", 0)})
                    completed_runs += 1
                    if progress_callback and completed_runs % 5 == 0:
                        progress_callback(completed_runs, total_runs, f"{name} (N={n})")
                if verbose and len(rows) > first:
                    sub = rows[first:]
                    print(f"N={n:5d} {name:24s} success="
                          f"{sum(x['solved'] for x in sub)}/{len(sub)} "
                          f"mean_steps={st.mean(x['steps'] for x in sub):.1f}",
                          flush=True)
        if progress_callback:
            progress_callback(completed_runs, total_runs, "Complete")
        return pd.DataFrame(rows)

    @staticmethod
    def summarize(df: pd.DataFrame) -> pd.DataFrame:
        """Per (N, variant) statistics.

        `*_mean` / `*_median` use solved runs only. `steps_all_mean` /
        `time_all_mean_s` average over *all* runs (a failed run costs its full
        budget), which is the fair cost measure when success rates differ.
        """
        if df.empty:
            return pd.DataFrame()
        out = []
        for (n, variant), g in df.groupby(["N", "variant"], sort=False):
            ok = g[g["solved"]]
            out.append({
                "N": n, "variant": variant, "runs": len(g),
                "success_rate": g["solved"].mean(),
                "steps_mean": ok["steps"].mean() if not ok.empty else float("nan"),
                "steps_median": ok["steps"].median() if not ok.empty else float("nan"),
                "steps_std": ok["steps"].std(ddof=0) if len(ok) > 1 else 0.0,
                "time_mean_s": ok["time_s"].mean() if not ok.empty else float("nan"),
                "time_median_s": ok["time_s"].median() if not ok.empty else float("nan"),
                "steps_all_mean": g["steps"].mean(),
                "time_all_mean_s": g["time_s"].mean(),
                "restarts_mean": g["restarts"].mean(),
            })
        return pd.DataFrame(out)

    @staticmethod
    def compare_to_baseline(summary: pd.DataFrame,
                            baseline_of: Dict[str, str]) -> pd.DataFrame:
        """Relative effect of each variant against its baseline.

        Ratios are `variant / baseline` over all runs, so a value below 1.0 means
        the variant is cheaper (fewer steps / less time).
        `baseline_of` maps variant name -> baseline variant name.
        """
        if summary.empty:
            return pd.DataFrame()
        by_key = summary.set_index(["N", "variant"])
        rows = []
        for (n, variant), row in by_key.iterrows():
            base_name = baseline_of.get(variant)
            if base_name is None or base_name == variant:
                continue
            if (n, base_name) not in by_key.index:
                continue
            base = by_key.loc[(n, base_name)]
            base_steps = base["steps_all_mean"] if base["steps_all_mean"] > 0 else 1.0
            base_time = base["time_all_mean_s"] if base["time_all_mean_s"] > 0 else 1.0
            rows.append({
                "N": n, "variant": variant, "baseline": base_name,
                "success_rate": row["success_rate"],
                "success_delta": row["success_rate"] - base["success_rate"],
                "steps_ratio": row["steps_all_mean"] / base_steps,
                "time_ratio": row["time_all_mean_s"] / base_time,
            })
        return pd.DataFrame(rows)
