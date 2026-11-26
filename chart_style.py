"""Shared chart theme: FiveThirtyEight-style layout (gray canvas, full grid, heavy
baseline, thick lines, dark source bar) with an autumn Thanksgiving palette. Type follows
FiveThirtyEight too: a bold grotesk for headlines and labels (Inter) and monospaced tick
labels and source line (JetBrains Mono).

The fonts ship in fonts/ (Inter: SIL Open Font License; JetBrains Mono: Apache 2.0) so the
charts look the same anywhere."""
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
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
BG = "#F0F0F0"          # FiveThirtyEight gray canvas
TEXT = "#222222"
MUTED = "#5A5A5A"
GRID = "#CBCBCB"
SHADE = "#E2E2E2"
FOOTER = "#5B5B5B"      # dark source bar

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
        "axes.edgecolor": BG, "axes.linewidth": 0, "axes.grid": True, "axes.grid.axis": "both",
        "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
        "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 7, "ytick.major.pad": 5,
        "axes.prop_cycle": plt.cycler(color=PALETTE), "lines.linewidth": 3.2,
        "lines.solid_capstyle": "butt", "lines.solid_joinstyle": "round",
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
    ax.axhline(y, color=TEXT, lw=2, zorder=2)


def soft_fill(ax, x, y, color, floor=None, alpha=0.10):
    """No-op in the FiveThirtyEight style (kept so chart code needs no changes)."""
    return None


def end_dot(ax, x, y, color, size=46):
    """No-op in the FiveThirtyEight style (kept so chart code needs no changes)."""
    return None


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


GEO_LABELS = {
    "nyc": ("NEW YORK CITY", RED),
    "nyc+us": ("NEW YORK CITY  |  U.S. AVERAGE FOR COMPARISON", RED),
    "us": ("NATIONAL (U.S.)", BLUE),
}


def finish(fig, title, subtitle, source, path, note=None, geo=None):
    """geo: "nyc", "nyc+us" or "us" adds a label above the headline saying which geography
    the chart covers."""
    if geo:
        label, color = GEO_LABELS[geo]
        fig.text(0.075, 0.988, label, fontsize=9.5, fontweight="bold", color=color, ha="left",
                 va="top", fontfamily=MONO)
    ttl = fig.text(0.075, 0.95, title, fontsize=20, fontweight="bold", ha="left", va="top", color=TEXT)
    sub = fig.text(0.075, 0.875, subtitle, fontsize=13, ha="left", va="top", color=MUTED)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    # Shrink a headline or subtitle that would run past the right edge
    for txt, size, limit in ((ttl, 20, 0.88), (sub, 13, 0.9)):
        w = txt.get_window_extent(r).width
        if w > limit * W:
            txt.set_fontsize(size * limit * W / w)
    mark = fig.text(0.015, 0, "THANKSGIVING DINNER PRICE INDEX", fontsize=9, color="white",
                    fontweight="bold", ha="left", va="center", fontfamily=MONO, zorder=11)
    src = fig.text(0.985, 0, f"SOURCE: {source}".upper(), fontsize=8.5, color="white",
                   ha="right", va="center", fontfamily=MONO, zorder=11, multialignment="right")
    fig.canvas.draw()
    # Wrap the source if it would run into the project mark
    room = 0.985 * W - mark.get_window_extent(r).x1 - 30
    ext = src.get_window_extent(r)
    if ext.width > room:
        chars = max(20, int(len(src.get_text()) * room / ext.width))
        src.set_text(textwrap.fill(src.get_text(), chars))
        fig.canvas.draw()
    # Dark footer bar sized to the source text
    bar_h = max(0.055, src.get_window_extent(r).height / H + 0.025)
    fig.patches.append(Rectangle((0, 0), 1, bar_h, transform=fig.transFigure, color=FOOTER,
                                 figure=fig, zorder=10))
    mark.set_y(bar_h / 2); src.set_y(bar_h / 2)
    top = bar_h
    if note:
        note_txt = fig.text(0.075, bar_h + 0.014, note, fontsize=9.5, color=MUTED, ha="left",
                            va="bottom", style="italic")
        fig.canvas.draw()
        ext = note_txt.get_window_extent(r)
        if ext.width > 0.91 * W:
            chars = max(20, int(len(note) * 0.91 * W / ext.width))
            note_txt.set_text(textwrap.fill(note, chars))
            fig.canvas.draw()
        top = note_txt.get_window_extent(r).y1 / H
    # Leave room above the footer for the x-axis tick labels
    fig.subplots_adjust(bottom=max(fig.subplotpars.bottom, top + 0.075))
    mono_ticks(fig)
    fig.savefig(path)
    plt.close(fig)


def finish_geo(geo, fig, *args, **kwargs):
    """finish() with a geography label ("nyc", "nyc+us" or "us") above the headline."""
    finish(fig, *args, geo=geo, **kwargs)
