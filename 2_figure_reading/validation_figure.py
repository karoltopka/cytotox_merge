"""Validation plot of the figure reading (not part of the Supplementary Materials): values read from the figures of Zhang et al. 2012 against the values the Nanopharos source gives
for the four toxic oxides of the same figures (left panels). Only these numbers are drawn; nothing of the published figure is reproduced.

Input:  results/Zhang2012_validation_toxic_oxides.csv (Zhang2012_values_and_validation.py)
Output: results/validation_of_figure_reading.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import OUT

d = pd.read_csv(OUT / "Zhang2012_validation_toxic_oxides.csv")
colours = {"CoO": "#7570b3", "CuO": "#1b9e77", "Mn2O3": "#e7298a", "ZnO": "#d95f02"}
fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharex=True, sharey=True)
for ax, (line, g) in zip(axes, d.groupby("cell_line")):
    for mat, gm in g.groupby("material"):
        ax.scatter(gm.value_in_Nanopharos, gm.read_from_figure, s=22, color=colours[mat], label=mat, alpha=0.85)
    ax.plot([0, 130], [0, 130], color="black", linewidth=0.8)
    how = "Fig. 2B/2C, raster" if line == "BEAS-2B" else "SI Fig. S2B/S2C, vector"
    ax.set_title(f"{line} ({how})", fontweight="bold")
    ax.text(0.04, 0.95, f"n = {len(g)}\nmean |difference| = {g.difference_pp.abs().mean():.2f} pp\nmax |difference| = {g.difference_pp.abs().max():.2f} pp",
            transform=ax.transAxes, va="top", fontsize=9)
    ax.set_xlim(0, 130); ax.set_ylim(0, 130); ax.set_aspect("equal")
    ax.set_xlabel("Viability in the Nanopharos source (%)", fontweight="bold")
axes[0].set_ylabel("Viability read from the figure (%)", fontweight="bold")
axes[1].legend(title="Material", loc="lower right", fontsize=9, title_fontproperties={"weight": "bold"})
fig.tight_layout()
fig.savefig(OUT / "validation_of_figure_reading.png", dpi=300, facecolor="white")
print(d.groupby("cell_line").difference_pp.agg(n="size", mean_abs=lambda s: round(s.abs().mean(), 2), max_abs=lambda s: round(s.abs().max(), 2)).to_string())
