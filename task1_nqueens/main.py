"""CLI entry point: argument parsing and wiring only (no algorithm logic)."""
from __future__ import annotations

import argparse
import os

from nqueens.amo import AMO_ENCODERS
from nqueens.experiments import (MinConflictsExperiment, Plotter, SATExperiment,
                                 config_variant, optimization_variants,
                                 sat_variants, selector_variants)
from nqueens.factory import MinConflictsConfig, build_min_conflicts, build_sat
from nqueens.solvers import INITIALIZERS, SELECTORS

OUT = "results"


# ----------------------------------------------------------------- helpers
def _config_from_args(a) -> MinConflictsConfig:
    """Min-Conflicts config from CLI flags (defaults = baseline)."""
    return MinConflictsConfig(
        selector=getattr(a, "selector", "random"),
        initializer=a.init,
        max_steps_factor=a.max_steps_factor,
        restart_steps_factor=a.restart_factor if a.restarts else None)


def _run_min_conflicts(a, variants, tag, baseline_of=None):
    """Run variants, print + save summary (and baseline comparison if given)."""
    exp = MinConflictsExperiment(variants, a.ns, a.runs)
    df = exp.run()
    summary = exp.summarize(df)
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(f"{OUT}/{tag}_results.csv", index=False)
    summary.to_csv(f"{OUT}/{tag}_summary.csv", index=False)
    Plotter(OUT).plot_compare(summary, tag)
    print(summary.round(4).to_string(index=False))
    if baseline_of:
        cmp_df = exp.compare_to_baseline(summary, baseline_of)
        cmp_df.to_csv(f"{OUT}/{tag}_vs_baseline.csv", index=False)
        print("\nRatios vs. baseline (<1.0 = cheaper than baseline):")
        print(cmp_df.round(3).to_string(index=False))


# ---------------------------------------------------------------- commands
def cmd_demo(a):
    n = a.n
    sat = build_sat(a.encoding).solve(n)
    print(f"[SAT/Glucose3/{a.encoding}] N={n} solved={sat.solved} "
          f"clauses={sat.num_clauses} time={sat.time_s:.5f}s")
    if n <= 40:
        print(sat.board)
    cfg = _config_from_args(a)
    mc = build_min_conflicts(cfg, seed=a.seed).solve(n)
    print(f"[Min-Conflicts/{cfg}] N={n} solved={mc.solved} steps={mc.steps} "
          f"restarts={mc.extra['restarts']} time={mc.time_s:.5f}s")
    if n <= 40:
        print(mc.board)


def cmd_sat(a):
    exp = SATExperiment(sat_variants(a.encodings, a.column_alo, a.time_limit),
                        a.ns, a.repeats)
    df = exp.run()
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(f"{OUT}/{a.tag}_results.csv", index=False)
    Plotter(OUT).plot_sat(df, a.tag)
    print(df.round(6).to_string(index=False))


def cmd_minconf(a):
    cfg = _config_from_args(a)
    _run_min_conflicts(a, {str(cfg): config_variant(cfg)}, a.tag)


def cmd_compare(a):
    """Compare variable-selection heuristics (R3)."""
    variants = selector_variants(list(SELECTORS), _config_from_args(a))
    _run_min_conflicts(a, variants, a.tag)


def cmd_optimize(a):
    """Compare the baseline with greedy init / restarts (the optimisations)."""
    variants, baseline_of = optimization_variants(
        a.selectors, a.max_steps_factor, a.restart_factor)
    _run_min_conflicts(a, variants, a.tag, baseline_of)


# --------------------------------------------------------------------- CLI
def _add_min_conflicts_args(p):
    p.add_argument("--max-steps-factor", type=int, default=100,
                   help="total step budget = factor * N (default 100)")
    p.add_argument("--init", choices=list(INITIALIZERS), default="random",
                   help="initial state strategy (default random = baseline)")
    p.add_argument("--restarts", action="store_true",
                   help="enable random restarts (off = baseline)")
    p.add_argument("--restart-factor", type=int, default=10,
                   help="restart an attempt after factor * N steps (default 10)")


def _add_experiment_args(p, tag):
    p.add_argument("--ns", type=int, nargs="+")
    p.add_argument("--runs", type=int, default=30)
    p.add_argument("--tag", default=tag, help="output file name prefix")


def main():
    p = argparse.ArgumentParser(description="N-Queens: SAT and Min-Conflicts")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="solve one board with both solvers")
    d.add_argument("--n", type=int, default=8)
    d.add_argument("--seed", type=int, default=0)
    d.add_argument("--selector", choices=list(SELECTORS), default="random")
    d.add_argument("--encoding", choices=list(AMO_ENCODERS), default="pairwise")
    _add_min_conflicts_args(d)
    d.set_defaults(f=cmd_demo)

    s = sub.add_parser("sat", help="Glucose3 experiment (clauses + time per N)")
    s.add_argument("--ns", type=int, nargs="+")
    s.add_argument("--repeats", type=int, default=5)
    s.add_argument("--time-limit", type=float, default=60.0,
                   help="per-solve limit in seconds; on timeout larger N are "
                        "skipped for that encoding (default 60)")
    s.add_argument("--column-alo", action="store_true")
    s.add_argument("--encodings", nargs="+", choices=list(AMO_ENCODERS),
                   default=["pairwise"],
                   help="AMO encodings to run; give several to compare them")
    s.add_argument("--tag", default="sat", help="output file name prefix")
    s.set_defaults(f=cmd_sat)

    m = sub.add_parser("minconf", help="one Min-Conflicts configuration")
    _add_experiment_args(m, "minconf_single")
    m.add_argument("--selector", choices=list(SELECTORS), default="random")
    _add_min_conflicts_args(m)
    m.set_defaults(f=cmd_minconf)

    c = sub.add_parser("compare", help="compare selection heuristics")
    _add_experiment_args(c, "minconf")
    _add_min_conflicts_args(c)
    c.set_defaults(f=cmd_compare)

    o = sub.add_parser("optimize",
                       help="baseline vs greedy-init / restarts / both")
    _add_experiment_args(o, "opt")
    o.add_argument("--selectors", nargs="+", choices=list(SELECTORS),
                   default=["random", "max"])
    o.add_argument("--max-steps-factor", type=int, default=100)
    o.add_argument("--restart-factor", type=int, default=10)
    o.set_defaults(f=cmd_optimize)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
