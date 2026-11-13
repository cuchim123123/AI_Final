import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from kakuro.board import ROWS, HORIZONTAL_GROUPS, VERTICAL_GROUPS
from kakuro.solver import KakuroSolver

sol = KakuroSolver().solve()
hclue, vclue = {}, {}
for total, cells in HORIZONTAL_GROUPS:
    r, c = cells[0]
    hclue[(r, c - 1)] = total
for total, cells in VERTICAL_GROUPS:
    r, c = cells[0]
    vclue[(r - 1, c)] = total

fig, ax = plt.subplots(figsize=(3.3, 3.3))
ax.set_xlim(0, 9); ax.set_ylim(9, 0); ax.axis("off"); ax.set_aspect("equal")
for r in range(1, 10):
    for c in range(1, 10):
        x, y = c - 1, r - 1
        if ROWS[r - 1][c - 1] == ".":
            ax.add_patch(Rectangle((x, y), 1, 1, fc="white", ec="black", lw=0.8))
            ax.text(x + .5, y + .55, str(sol[(r, c)]), ha="center", va="center", fontsize=10)
        else:
            ax.add_patch(Rectangle((x, y), 1, 1, fc="#bdbdbd", ec="black", lw=0.8))
            h, v = hclue.get((r, c)), vclue.get((r, c))
            if h or v:
                ax.plot([x, x + 1], [y, y + 1], "k", lw=0.6)
            if h:
                ax.text(x + .72, y + .3, str(h), ha="center", va="center", fontsize=6)
            if v:
                ax.text(x + .28, y + .72, str(v), ha="center", va="center", fontsize=6)
os.makedirs("figures", exist_ok=True)
fig.savefig("figures/task3_solution.png", dpi=250, bbox_inches="tight", pad_inches=0.02)
print("saved figures/task3_solution.png")