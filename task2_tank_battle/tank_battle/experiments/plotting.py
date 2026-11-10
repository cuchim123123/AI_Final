"""Matplotlib visualization helpers for Requirement 2 experimental results."""
from __future__ import annotations

import os
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CONFIG_COLORS: Dict[str, str] = {
    "minimax": "#ef4444",            # Red
    "alphabeta": "#f59e0b",          # Amber
    "heuristic_minimax": "#3b82f6",  # Blue
    "heuristic_alphabeta": "#10b981",# Emerald
}

CONFIG_MARKERS: Dict[str, str] = {
    "minimax": "o",
    "alphabeta": "s",
    "heuristic_minimax": "^",
    "heuristic_alphabeta": "D",
}


def plot_search_benchmarks(df: pd.DataFrame, out_dir: str) -> Dict[str, str]:
    """Generate explored states, runtime, and pruning ratio plots for R2."""
    os.makedirs(out_dir, exist_ok=True)
    saved: Dict[str, str] = {}

    # Aggregate across scenarios by (config_key, config_name, depth)
    agg = (
        df.groupby(["config_key", "config_name", "depth"], as_index=False)
        .agg(
            nodes_mean=("nodes_explored", "mean"),
            time_ms_mean=("time_mean_ms", "mean"),
            reduction_mean=("state_reduction_vs_minimax", "mean"),
        )
    )

    # 1. Explored States vs Depth (Log Scale)
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=140)
    for cfg_key in ["minimax", "alphabeta", "heuristic_minimax", "heuristic_alphabeta"]:
        sub = agg[agg["config_key"] == cfg_key].sort_values("depth")
        if sub.empty:
            continue
        label = str(sub["config_name"].iloc[0])
        ax.plot(
            sub["depth"],
            sub["nodes_mean"],
            marker=CONFIG_MARKERS.get(cfg_key, "o"),
            color=CONFIG_COLORS.get(cfg_key, "#333333"),
            linewidth=2.3,
            markersize=7,
            label=label,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Search Depth (ply)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Mean Explored Game States (log scale)", fontsize=11, fontweight="bold")
    ax.set_title("Explored Game States vs. Search Depth (4 Configurations)", fontsize=13, fontweight="bold")
    ax.set_xticks(sorted(df["depth"].unique()))
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend(frameon=True, fontsize=10)
    fig.tight_layout()
    states_path = os.path.join(out_dir, "states_vs_depth.png")
    fig.savefig(states_path)
    plt.close(fig)
    saved["states_vs_depth"] = states_path

    # 2. Execution Time (ms) vs Depth (Log Scale)
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=140)
    for cfg_key in ["minimax", "alphabeta", "heuristic_minimax", "heuristic_alphabeta"]:
        sub = agg[agg["config_key"] == cfg_key].sort_values("depth")
        if sub.empty:
            continue
        label = str(sub["config_name"].iloc[0])
        ax.plot(
            sub["depth"],
            sub["time_ms_mean"],
            marker=CONFIG_MARKERS.get(cfg_key, "o"),
            color=CONFIG_COLORS.get(cfg_key, "#333333"),
            linewidth=2.3,
            markersize=7,
            label=label,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Search Depth (ply)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Mean Execution Time per Decision (ms, log scale)", fontsize=11, fontweight="bold")
    ax.set_title("Execution Time vs. Search Depth (4 Configurations)", fontsize=13, fontweight="bold")
    ax.set_xticks(sorted(df["depth"].unique()))
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend(frameon=True, fontsize=10)
    fig.tight_layout()
    time_path = os.path.join(out_dir, "time_vs_depth.png")
    fig.savefig(time_path)
    plt.close(fig)
    saved["time_vs_depth"] = time_path

    # 3. Alpha-Beta State Reduction Ratio (%) vs Depth
    fig, ax = plt.subplots(figsize=(8.5, 5.0), dpi=140)
    ab_configs = ["alphabeta", "heuristic_alphabeta"]
    depths = sorted(df["depth"].unique())
    x = np.arange(len(depths))
    width = 0.34

    for idx, cfg_key in enumerate(ab_configs):
        sub = agg[agg["config_key"] == cfg_key].sort_values("depth")
        if sub.empty:
            continue
        label = str(sub["config_name"].iloc[0])
        vals = sub["reduction_mean"].to_numpy() * 100.0
        offset = (idx - 0.5) * width
        bars = ax.bar(
            x + offset,
            vals,
            width=width,
            color=CONFIG_COLORS.get(cfg_key, "#10b981"),
            label=label,
             alpha=0.9,
        )
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 1.2,
                f"{v:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels([f"Depth {d}" for d in depths])
    ax.set_ylim(0, 105)
    ax.set_ylabel("State Space Reduction vs. Unpruned Minimax (%)", fontsize=11, fontweight="bold")
    ax.set_title("Alpha-Beta Pruning Efficiency Across Search Depths", fontsize=13, fontweight="bold")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    ax.legend(frameon=True, fontsize=10)
    fig.tight_layout()
    prune_path = os.path.join(out_dir, "pruning_ratio.png")
    fig.savefig(prune_path)
    plt.close(fig)
    saved["pruning_ratio"] = prune_path

    return saved


def plot_tournament_summary(summary_df: pd.DataFrame, out_dir: str) -> str:
    """Plot tournament win rates and average decision times."""
    os.makedirs(out_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=140)

    labels = summary_df["display_name"].tolist()
    specs = summary_df["agent_spec"].tolist()
    colors = [CONFIG_COLORS.get(s, "#6366f1") for s in specs]
    win_rates = summary_df["win_rate_pct"].to_numpy()
    move_times = summary_df["mean_move_time_ms"].to_numpy()

    y = np.arange(len(labels))
    bars1 = ax1.barh(y, win_rates, color=colors, alpha=0.9)
    ax1.set_yticks(y)
    ax1.set_yticklabels(labels, fontsize=9, fontweight="bold")
    ax1.invert_yaxis()
    ax1.set_xlim(0, 110)
    ax1.set_xlabel("Tournament Score / Win Rate (%)", fontsize=10, fontweight="bold")
    ax1.set_title("Head-to-Head Tournament Win Rate", fontsize=12, fontweight="bold")
    ax1.grid(True, axis="x", linestyle="--", alpha=0.4)
    for bar, v in zip(bars1, win_rates):
        ax1.text(v + 1.5, bar.get_y() + bar.get_height() / 2.0, f"{v:.1f}%", va="center", fontsize=9, fontweight="bold")

    bars2 = ax2.barh(y, move_times, color=colors, alpha=0.9)
    ax2.set_yticks(y)
    ax2.set_yticklabels(["" for _ in labels])
    ax2.invert_yaxis()
    ax2.set_xlabel("Mean Decision Time per Turn (ms)", fontsize=10, fontweight="bold")
    ax2.set_title("Real-Time Speed (Lower is Faster)", fontsize=12, fontweight="bold")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.4)
    max_t = max(float(np.max(move_times)), 1.0)
    ax2.set_xlim(0, max_t * 1.22)
    for bar, v in zip(bars2, move_times):
        ax2.text(v + max_t * 0.02, bar.get_y() + bar.get_height() / 2.0, f"{v:.1f} ms", va="center", fontsize=9)

    fig.tight_layout()
    out_path = os.path.join(out_dir, "tournament_winrates.png")
    fig.savefig(out_path)
    plt.close(fig)
    return out_path
