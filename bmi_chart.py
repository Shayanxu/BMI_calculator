"""BMI trend chart (needs matplotlib, which is an optional dependency)."""

import math

from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

import bmi_core as core

BG = "#1f1f1f"
TEXT = "white"
MUTED = "#aaaaaa"
GRID = "#333333"


def build_figure(history):
    """Return a matplotlib Figure showing the BMI of each history record over time.

    Coloured bands mark the BMI categories. The figure is returned without being
    shown, so it can be embedded in tkinter or saved to an image file.
    """
    values = [record["bmi"] for record in history]
    positions = list(range(1, len(values) + 1))

    low = min(10, math.floor(min(values)) - 1)
    high = max(40, math.ceil(max(values)) + 1)

    figure = Figure(figsize=(6.4, 4.2), dpi=100, facecolor=BG)
    axes = figure.add_subplot(111)
    axes.set_facecolor(BG)

    # Category bands with their names on the right
    edges = [low] + [category.upper for category in core.CATEGORIES[:-1]] + [high]
    for start, end, category in zip(edges[:-1], edges[1:], core.CATEGORIES):
        axes.axhspan(start, end, color=category.color, alpha=0.16, linewidth=0)
        axes.text(0.99, (start + end) / 2, category.name, transform=axes.get_yaxis_transform(),
                  ha="right", va="center", fontsize=9, color=category.color)

    # The BMI line, with each point coloured by its category
    axes.plot(positions, values, color=TEXT, linewidth=1.5, zorder=3)
    axes.scatter(positions, values, c=[core.classify(v).color for v in values], s=60,
                 edgecolors=TEXT, linewidths=0.8, zorder=4)
    axes.annotate(f"{values[-1]:.1f}", (positions[-1], values[-1]), textcoords="offset points",
                  xytext=(0, 10), ha="center", color=TEXT, fontsize=10, fontweight="bold")

    axes.set_xlim(0.5, len(values) + 0.5)
    axes.set_ylim(low, high)
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes.set_title("BMI trend", color=TEXT, fontsize=14, fontweight="bold", pad=12)
    axes.set_xlabel("Measurement", color=MUTED)
    axes.set_ylabel("BMI", color=MUTED)
    axes.tick_params(colors=MUTED)
    axes.grid(axis="y", color=GRID, linewidth=0.6)
    axes.set_axisbelow(True)
    for spine in axes.spines.values():
        spine.set_color(GRID)

    figure.tight_layout()
    return figure
