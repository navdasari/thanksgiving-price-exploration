"""Shared Thanksgiving chart theme: warm cream canvas and an autumn harvest palette, with
FiveThirtyEight-style type: a bold grotesk headline and labels (Inter) and monospaced tick
labels and source line (JetBrains Mono). Dots mark line ends; a small project mark sits in
the footer.

The fonts ship in fonts/ (Inter: SIL Open Font License; JetBrains Mono: Apache 2.0) so the
charts look the same anywhere."""
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

FONT_DIR = Path(__file__).parent / "fonts"
for f in sorted(FONT_DIR.glob("*.ttf")) + sorted(FONT_DIR.glob("*.otf")):
    font_manager.fontManager.addfont(str(f))


def _font(preferred, fallback):
    names = {f.name for f in font_manager.fontManager.ttflist}
    return next((p for p in preferred if p in names), fallback)


SANS = _font(["Inter", "Helvetica Neue", "Helvetica", "Arial", "Liberation Sans"], "DejaVu Sans")
MONO = _font(["JetBrains Mono", "DejaVu Sans Mono", "Liberation Mono"], "monospace")

# Canvas and text
BG = "#FBF6EC"          # cream
TEXT = "#2E1F16"        # espresso
MUTED = "#7D6A5A"       # warm brown-gray
GRID = "#EADFCB"
SHADE = "#F2E7D3"

# Harvest palette (names kept from the earlier theme so chart code stays readable)
RED = "#A3243B"         # cranberry
PUMPKIN = "#D9692A"     # pumpkin
GOLD = "#E0A33A"        # harvest gold
GREEN = "#8AA37B"       # sage
BLUE = "#3F5E4A"        # pine
PURPLE = "#6E3B5C"      # plum
GRAY = "#B3A493"        # oat
DARK = "#4A3426"        # roasted chestnut
LIGHT_GOLD, DARK_GOLD, LIGHT_BLUE = "#F0D08E", "#A8701F", "#9DB5A3"
PALETTE = [RED, PUMPKIN, GOLD, GREEN, BLUE, PURPLE]


def apply():
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "figure.dpi": 150, "font.family": SANS, "font.size": 11.5, "text.color": TEXT,
        "axes.edgecolor": BG, "axes.linewidth": 0, "axes.grid": True, "axes.grid.axis": "y",
        "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
        "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 7, "ytick.major.pad": 5,
        "axes.prop_cycle": plt.cycler(color=PALETTE), "lines.linewidth": 2.8,
        "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
        "legend.frameon": False, "legend.fontsize": 10.5,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlepad": 12, "axes.titlecolor": TEXT,
    })


def figure(nrows=1, ncols=1, width=10, height=6.4, **kw):
    """Figure with room reserved for the stripe, headline, subtitle and footer."""
    apply()
    fig, axes = plt.subplots(nrows, ncols, figsize=(width, height), **kw)
    fig.subplots_adjust(left=0.075, right=0.87, top=0.76, bottom=0.13, wspace=0.28)
    for ax in (axes.flat if hasattr(axes, "flat") else [axes]):
        style_ticks(ax)
    return fig, axes


def style_ticks(ax):
    ax.tick_params(axis="both", which="both", length=0)


def unit_on_top(ax, fmt=lambda v: f"{v:g}", prefix="", suffix=""):
    """Put the unit only on the top tick label ('$60', '50%')."""
    ax.figure.canvas.draw()
    ticks = [t for t in ax.get_yticks() if ax.get_ylim()[0] <= t <= ax.get_ylim()[1]]
    top = max(ticks) if ticks else None
    ax.yaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{prefix}{fmt(v)}{suffix}" if top is not None and abs(v - top) < 1e-9 else fmt(v)))


def baseline(ax, y=0):
    ax.axhline(y, color="#B9A68E", lw=1.2, zorder=2)


def soft_fill(ax, x, y, color, floor=None, alpha=0.10):
    """A soft wash under a line, for the main series."""
    lo = ax.get_ylim()[0] if floor is None else floor
    ax.fill_between(x, y, lo, color=color, alpha=alpha, lw=0, zorder=1)


def end_dot(ax, x, y, color, size=46):
    ax.scatter([x], [y], s=size, color=color, edgecolor=BG, linewidth=1.6, zorder=6, clip_on=False)


def label_end(ax, x, y, text, color, dy=0, dx=0.4, size=10.5, weight="semibold", dot=True):
    """Direct label at the right end of a line, with a dot on the end point."""
    if dot:
        end_dot(ax, x, y, color)
    ax.annotate(text, (x, y), xytext=(x + dx, y + dy), textcoords="data", color=color,
                fontsize=size, fontweight=weight, va="center", ha="left", annotation_clip=False)


def mono_ticks(fig):
    """Monospaced tick labels, as in FiveThirtyEight charts."""
    fig.canvas.draw()
    for ax in fig.axes:
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontfamily(MONO)
            lab.set_fontsize(10)


def finish(fig, title, subtitle, source, path, note=None):
    fig.text(0.075, 0.95, title, fontsize=19.5, fontweight="bold", ha="left", va="top", color=TEXT)
    fig.text(0.075, 0.875, subtitle, fontsize=12.5, ha="left", va="top", color=MUTED)
    src = fig.text(0.075, 0.026, f"SOURCE: {source}".upper(), fontsize=8.5, color=MUTED, ha="left",
                   va="bottom", fontfamily=MONO)
    mark = fig.text(0.975, 0.026, "THANKSGIVING DINNER PRICE INDEX", fontsize=8.5, color=RED,
                    fontweight="bold", ha="right", va="bottom", fontfamily=MONO)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    fig_h = fig.bbox.height

    def fit(txt, right_px):
        """Wrap a text object so it ends before right_px."""
        ext = txt.get_window_extent(r)
        room = right_px - ext.x0
        if ext.width > room:
            chars = max(20, int(len(txt.get_text()) * room / ext.width))
            txt.set_text(textwrap.fill(txt.get_text(), chars))
            fig.canvas.draw()

    # Source line: wrap if it would run into the project mark
    fit(src, mark.get_window_extent(r).x0 - 20)
    top = src.get_window_extent(r).y1 / fig_h
    # Optional note: stacked above the source, wrapped to the full width
    if note:
        note_txt = fig.text(0.075, top + 0.012, note, fontsize=9.5, color=MUTED, ha="left", va="bottom",
                            style="italic")
        fig.canvas.draw()
        fit(note_txt, 0.975 * fig.bbox.width)
        top = note_txt.get_window_extent(r).y1 / fig_h
    # Leave room above the footer for the x-axis tick labels
    fig.subplots_adjust(bottom=max(fig.subplotpars.bottom, top + 0.075))
    mono_ticks(fig)
    fig.savefig(path)
    plt.close(fig)
