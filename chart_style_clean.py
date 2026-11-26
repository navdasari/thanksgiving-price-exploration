"""Earlier clean chart style, kept for the item-contributions chart (chart 3): white background, faint horizontal gridlines, a semibold
left-aligned headline with a subtitle, direct line labels, a muted palette and a
small source line at the bottom."""
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

BG = "#FFFFFF"
GRID = "#E8E8E8"
TEXT = "#1F1F1F"
MUTED = "#6B6B6B"
SHADE = "#F3F3F3"

# Muted, colorblind-friendlier palette
BLUE, RED, GOLD, GREEN, GRAY, PURPLE = "#2F6690", "#C8553D", "#E0A030", "#3A8F7E", "#9A9A9A", "#7A5C99"
DARK = "#333333"
LIGHT_GOLD, DARK_GOLD, LIGHT_BLUE = "#F0CF8E", "#A0701A", "#9EC1DB"
PALETTE = [BLUE, RED, GOLD, GREEN, GRAY, PURPLE]


def _font(preferred, fallback):
    names = {f.name for f in font_manager.fontManager.ttflist}
    return next((p for p in preferred if p in names), fallback)


SANS = _font(["Inter", "Helvetica Neue", "Helvetica", "Arial", "Liberation Sans"], "DejaVu Sans")


def apply():
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "figure.dpi": 150, "font.family": SANS, "font.size": 11, "text.color": TEXT,
        "axes.edgecolor": BG, "axes.linewidth": 0, "axes.grid": True, "axes.grid.axis": "y",
        "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.9,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 10, "ytick.labelsize": 10,
        "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 6, "ytick.major.pad": 4,
        "axes.prop_cycle": plt.cycler(color=PALETTE), "lines.linewidth": 2.4,
        "lines.solid_capstyle": "round", "legend.frameon": False, "legend.fontsize": 10,
        "axes.titlesize": 11.5, "axes.titleweight": "semibold", "axes.titlelocation": "left",
        "axes.titlepad": 10, "axes.titlecolor": TEXT,
    })


def figure(nrows=1, ncols=1, width=10, height=6.2, **kw):
    """Figure with room reserved for the headline, subtitle and source line."""
    apply()
    fig, axes = plt.subplots(nrows, ncols, figsize=(width, height), **kw)
    fig.subplots_adjust(left=0.07, right=0.88, top=0.78, bottom=0.12, wspace=0.28)
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
    ax.axhline(y, color="#8A8A8A", lw=1.1, zorder=2)


def label_end(ax, x, y, text, color, dy=0, dx=0.4, size=10, weight="semibold"):
    """Direct label at the right end of a line."""
    ax.annotate(text, (x, y), xytext=(x + dx, y + dy), textcoords="data", color=color,
                fontsize=size, fontweight=weight, va="center", ha="left", annotation_clip=False)


def finish(fig, title, subtitle, source, path, note=None):
    fig.text(0.07, 0.945, title, fontsize=17, fontweight="semibold", ha="left", va="top", color=TEXT)
    fig.text(0.07, 0.88, subtitle, fontsize=11.5, ha="left", va="top", color=MUTED)
    if note:
        fig.subplots_adjust(bottom=0.17)
        fig.text(0.07, 0.055, note, fontsize=8.5, color=MUTED, ha="left", va="bottom")
    fig.text(0.07, 0.025, f"Source: {source}", fontsize=8.5, color=MUTED, ha="left", va="bottom")
    fig.savefig(path)
    plt.close(fig)
