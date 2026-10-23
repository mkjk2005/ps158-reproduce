"""Plot the net worth gap between families whose reference person has a college
degree and those with a high school education or less, 1989-2025.

Reads data/networth_by_education.csv (made by get_data.py) and writes
figures/networth_gap_by_education.png.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

IN_FILE = Path("data/networth_by_education.csv")
OUT_FILE = Path("figures/networth_gap_by_education.png")

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
COLORS = {"College degree": "#2a78d6", "High school or less": "#eb6834"}
RATIO_COLOR = "#52514e"


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(TEXT_SECONDARY)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=0)
    ax.set_xticks(range(1989, 2026, 6))
    ax.set_xlim(1987, 2027)


def main():
    df = pd.read_csv(IN_FILE)
    medians = df.pivot(index="year", columns="group", values="median_networth") / 1000
    ratio = medians["College degree"] / medians["High school or less"]

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.6), facecolor=SURFACE,
                                      gridspec_kw={"width_ratios": [1.25, 1]})

    # Left: median net worth of each group
    for group, color in COLORS.items():
        s = medians[group]
        left.plot(s.index, s.values, color=color, linewidth=2, marker="o",
                  markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.2)
        left.annotate(f"{group}\n${s.iloc[-1]:,.0f}k in 2025", (s.index[-1], s.iloc[-1]),
                      xytext=(-4, 12), textcoords="offset points", ha="right",
                      fontsize=9, color=TEXT_PRIMARY)
        left.annotate(f"${s.iloc[0]:,.0f}k", (s.index[0], s.iloc[0]), xytext=(0, 9),
                      textcoords="offset points", ha="center", fontsize=9,
                      color=TEXT_SECONDARY)
    style_axes(left)
    left.set_ylim(0, 600)
    left.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}k"))
    left.set_title("Median family net worth, thousands of 2025 dollars",
                   loc="left", fontsize=10.5, color=TEXT_PRIMARY)

    # Right: how many times larger the college group's median is
    right.plot(ratio.index, ratio.values, color=RATIO_COLOR, linewidth=2, marker="o",
               markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.2)
    for year in [1989, ratio.idxmax(), 2025]:
        right.annotate(f"{ratio[year]:.1f}×", (year, ratio[year]), xytext=(0, 9),
                       textcoords="offset points", ha="center", fontsize=9,
                       color=TEXT_PRIMARY)
    style_axes(right)
    right.set_ylim(0, 8)
    right.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:.0f}×"))
    right.set_title("College median as a multiple of high-school-or-less median",
                    loc="left", fontsize=10.5, color=TEXT_PRIMARY)

    fig.suptitle("The wealth gap by education has widened since 1989",
                 x=0.012, ha="left", fontsize=14, fontweight="bold", color=TEXT_PRIMARY)
    fig.text(0.012, 0.015,
             "Education of the survey's reference person. College = bachelor's degree or "
             "more; high school or less = diploma, GED, or no diploma. All families.\n"
             "Source: Federal Reserve Board, Survey of Consumer Finances 1989–2025, "
             "summary extract files.",
             fontsize=8, color=TEXT_SECONDARY, va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 0.97))

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FILE, dpi=200, facecolor=SURFACE)
    print(f"wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
