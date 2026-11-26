"""Shared chart style, modeled on the classic FiveThirtyEight look: light gray canvas,
bold left-aligned headline with subtitle, monospaced tick labels, thick lines,
direct labels, a heavy baseline and a dark source bar along the bottom."""
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

BG = "#F0F0F0"
GRID = "#CBCBCB"
TEXT = "#222222"
MUTED = "#555555"
FOOTER = "#5B5B5B"

BLUE, RED, GOLD, GREEN, GRAY, PURPLE = "#008FD5", "#FC4F30", "#E5AE38", "#6D904F", "#8B8B8B", "#810F7C"
DARK = "#3C3C3C"
PALETTE = [BLUE, RED, GOLD, GREEN, GRAY, PURPLE]


def _font(preferred, fallback):
    names = {f.name for f in font_manager.fontManager.ttflist}
    return next((p for p in preferred if p in names), fallback)


SANS = _font(["Inter", "Helvetica Neue", "Helvetica", "Arial", "Liberation Sans"], "DejaVu Sans")
MONO = _font(["JetBrains Mono", "DejaVu Sans Mono", "Liberation Mono"], "monospace")


def apply():
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "figure.dpi": 150, "font.family": SANS, "font.size": 11, "text.color": TEXT,
        "axes.edgecolor": BG, "axes.linewidth": 0, "axes.grid": True, "axes.axisbelow": True,
        "grid.color": GRID, "grid.linewidth": 1.0, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 10, "ytick.labelsize": 10,
        "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 6, "ytick.major.pad": 6,
        "axes.prop_cycle": plt.cycler(color=PALETTE), "lines.linewidth": 3,
        "lines.solid_capstyle": "butt", "legend.frameon": False, "legend.fontsize": 10,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 10,
    })


def figure(nrows=1, ncols=1, width=10, height=6.2, **kw):
    """Figure with room reserved for the headline, subtitle and source bar."""
    apply()
    fig, axes = plt.subplots(nrows, ncols, figsize=(width, height), **kw)
    fig.subplots_adjust(left=0.07, right=0.88, top=0.78, bottom=0.14, wspace=0.28)
    for ax in (axes.flat if hasattr(axes, "flat") else [axes]):
        style_ticks(ax)
    return fig, axes


def style_ticks(ax):
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontfamily(MONO)
    ax.tick_params(axis="both", which="both", length=0)


def unit_on_top(ax, fmt=lambda v: f"{v:g}", prefix="", suffix=""):
    """Put the unit only on the top tick label, as FiveThirtyEight did ('$60', '50%')."""
    ax.figure.canvas.draw()
    ticks = [t for t in ax.get_yticks() if ax.get_ylim()[0] <= t <= ax.get_ylim()[1]]
    top = max(ticks) if ticks else None
    ax.yaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{prefix}{fmt(v)}{suffix}" if top is not None and abs(v - top) < 1e-9 else fmt(v)))
    style_ticks(ax)


def baseline(ax, y=0):
    ax.axhline(y, color=TEXT, lw=1.8, zorder=2)


def label_end(ax, x, y, text, color, dy=0, dx=0.4, size=10.5, weight="bold"):
    """Direct label at the right end of a line."""
    ax.annotate(text, (x, y), xytext=(x + dx, y + dy), textcoords="data", color=color,
                fontsize=size, fontweight=weight, va="center", ha="left", annotation_clip=False)


def finish(fig, title, subtitle, source, path, note=None):
    fig.text(0.07, 0.945, title, fontsize=19, fontweight="bold", ha="left", va="top", color=TEXT)
    fig.text(0.07, 0.875, subtitle, fontsize=12.5, ha="left", va="top", color=MUTED)
    fig.patches.append(plt.Rectangle((0, 0), 1, 0.055, transform=fig.transFigure,
                                     color=FOOTER, zorder=-1, figure=fig))
    fig.text(0.985, 0.0275, f"SOURCE: {source}".upper(), fontsize=8.5, color="white",
             ha="right", va="center", fontfamily=MONO)
    if note:
        fig.text(0.07, 0.075, note, fontsize=9, color=MUTED, ha="left", va="center")
    for ax in fig.axes:
        style_ticks(ax)
    fig.savefig(path)
    plt.close(fig)
