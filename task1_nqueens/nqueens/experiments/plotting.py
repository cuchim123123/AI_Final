"""Charts for the experiment results."""
from __future__ import annotations

import os
from typing import List, Tuple

import matplotlib
matplotlib.use("Agg")  # file output only; no display needed
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


class Plotter:
    """Draws charts into `out_dir`; file names start with the given `tag`."""

    def __init__(self, out_dir: str = "results") -> None:
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

    def _save(self, fig, name: str) -> str:
        path = os.path.join(self.out_dir, name)
        fig.tight_layout()
        fig.savefig(path, dpi=130)
        plt.close(fig)
        return path

    def create_sat_figures(self, df: pd.DataFrame) -> List[Tuple[str, plt.Figure]]:
        """Generate (name, Figure) for clauses vs N and solve time vs N."""
        figs = []
        fig1, ax1 = plt.subplots(figsize=(6.5, 4.5))
        for enc, g in df.groupby("encoding", sort=False):
            ax1.plot(g["N"], g["clauses"], "o-", label=enc)
        ax1.set(xlabel="N", ylabel="# CNF clauses", title="Clauses vs N", yscale="log")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        figs.append(("clauses_vs_n", fig1))

        fig2, ax2 = plt.subplots(figsize=(6.5, 4.5))
        for enc, g in df.groupby("encoding", sort=False):
            ax2.errorbar(g["N"], g["solve_time_mean_s"], g["solve_time_std_s"],
                         fmt="o-", label=enc)
        ax2.set(xlabel="N", ylabel="Glucose3 solve time (s)",
                title="Solve time vs N", yscale="log")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        figs.append(("time_vs_n", fig2))
        return figs

    def plot_sat(self, df: pd.DataFrame, tag: str = "sat") -> list:
        """Clauses vs N and solve time vs N, one line per encoding."""
        paths = []
        for name, fig in self.create_sat_figures(df):
            paths.append(self._save(fig, f"{tag}_{name}.png"))
        return paths

    def create_compare_figures(self, summary: pd.DataFrame) -> List[Tuple[str, plt.Figure]]:
        """Generate (name, Figure) for steps, time, and success rate vs N."""
        charts = (
            ("steps_all_mean", "mean steps per run (all runs)", "steps_vs_n", True),
            ("time_all_mean_s", "mean time per run, s (all runs)", "time_vs_n", True),
            ("success_rate", "success rate", "success_vs_n", False))
        figs = []
        for col, label, suffix, log in charts:
            fig, ax = plt.subplots(figsize=(7, 4.5))
            for variant, g in summary.groupby("variant", sort=False):
                ax.plot(g["N"], g[col], "o-", label=variant)
            ax.set(xlabel="N", ylabel=label, xscale="log", title=f"{label} vs N")
            if log:
                ax.set_yscale("log")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            figs.append((suffix, fig))
        return figs

    def plot_compare(self, summary: pd.DataFrame, tag: str = "minconf") -> list:
        """Steps / time / success rate vs N, one line per variant."""
        paths = []
        for name, fig in self.create_compare_figures(summary):
            paths.append(self._save(fig, f"{tag}_{name}.png"))
        return paths
