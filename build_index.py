"""Thanksgiving Dinner Price Index, built from BLS average retail prices (via FRED).

Prices are taken in October of each year, the last month BLS publishes before
Thanksgiving (November data comes out in mid-December).

Menu: the Farm Bureau's expanded Thanksgiving menu for 10 (see BASKET). Items BLS does
not price start from the Farm Bureau's 2026 survey price and move with a CPI component.

Data patches (flagged in the output):
  * Turkey: BLS stopped publishing APU0000706311 after Feb 2020. From March 2020 on,
    the price is the model reconstruction from turkey_price_ml_modeling.py (run it first). Two
    comparison versions are kept: the 2019 BLS price carried forward with the Farm
    Bureau's holiday turkey price, and the whole-chicken price times the Feb 2020
    turkey/chicken ratio.
  * October 2013 (turkey) and October 2025 (all items): not published because of
    government shutdowns; the Sep/Nov average is used.
  * Butter: no BLS butter average price exists from May 2012 to Mar 2018. The gap
    is filled with the dairy CPI, scaled so it matches both ends of the gap.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "output"
OUT.mkdir(exist_ok=True)
MONTH = 10  # October


def load(sid):
    df = pd.read_csv(DATA / f"{sid}.csv", parse_dates=["observation_date"], na_values=".")
    return df.set_index("observation_date")[sid].astype(float)


# ---------------- Basket: Thanksgiving dinner for 10 ----------------
# The menu follows the American Farm Bureau Federation's "expanded" Thanksgiving menu
# (its classic menu plus boneless ham, russet potatoes and frozen green beans).
# item: (source, quantity, unit). Source is a FRED id for a BLS average price, a patched
# series (TURKEY, BUTTER), or ANCHOR for items BLS does not price (see ANCHORS).
BASKET = {
    "Turkey":            ("TURKEY",        16.0, "lb"),
    "Ham":               ("APU0000704312",  3.0, "lb, boneless"),
    "Russet potatoes":   ("APU0000712112",  5.0, "lb"),
    "Sweet potatoes":    ("ANCHOR",         1.0, "3 lb"),
    "Stuffing mix":      ("ANCHOR",         1.0, "14 oz"),
    "Dinner rolls":      ("ANCHOR",         1.0, "dozen"),
    "Cranberries":       ("ANCHOR",         1.0, "12 oz bag"),
    "Frozen peas":       ("ANCHOR",         1.0, "1 lb"),
    "Green beans":       ("ANCHOR",         1.0, "1 lb frozen"),
    "Veggie tray":       ("ANCHOR",         1.0, "1 lb carrots & celery"),
    "Pumpkin pie mix":   ("ANCHOR",         1.0, "30 oz can"),
    "Pie crusts":        ("ANCHOR",         1.0, "2 frozen"),
    "Whipping cream":    ("ANCHOR",         1.0, "half pint"),
    "Milk":              ("APU0000709112",  1.0, "gal"),
    "Butter":            ("BUTTER",         1.0, "lb"),
    "Eggs":              ("APU0000708111",  1.0, "doz"),
    "Flour":             ("APU0000701111",  1.0, "lb"),
    "Sugar":             ("APU0000715211",  1.0, "lb"),
}
# Items BLS does not price: the Farm Bureau's 2026 survey price, moved back in time with
# the closest CPI component on FRED (October values). FRED only carries the broad
# components, so produce, frozen and canned items all follow "fruits and vegetables".
# Green beans: the Farm Bureau does not publish its price, so the frozen-pea price is used.
ANCHOR_YEAR = 2026
ANCHORS = {
    "Sweet potatoes":  (4.20, "CUUR0000SAF113"),
    "Stuffing mix":    (3.91, "CUUR0000SAF111"),
    "Dinner rolls":    (3.81, "CUUR0000SAF111"),
    "Cranberries":     (2.48, "CUUR0000SAF113"),
    "Frozen peas":     (1.99, "CUUR0000SAF113"),
    "Green beans":     (1.99, "CUUR0000SAF113"),
    "Veggie tray":     (1.31, "CUUR0000SAF113"),
    "Pumpkin pie mix": (4.24, "CUUR0000SAF113"),
    "Pie crusts":      (3.28, "CUUR0000SAF111"),
    "Whipping cream":  (1.84, "CUUR0000SEFJ"),
}

# ---------------- Patch turkey ----------------
# Main version: model reconstruction of the BLS series (turkey_price_ml_modeling.py).
# Comparison versions: (a) the last BLS October price (2019) carried forward with the
# year-to-year change in the Farm Bureau's 16-lb holiday turkey price; (b) whole-chicken
# price times the Feb 2020 turkey/chicken ratio.
AFBF_TURKEY = {2019: 20.80, 2020: 19.39, 2021: 23.99, 2022: 28.96, 2023: 27.35,
               2024: 25.67, 2025: 21.50, 2026: 23.68}
turkey, chicken = load("APU0000706311").dropna(), load("APU0000706111")
last = turkey.index.max()
ratio = turkey[last] / chicken[last]
turkey_chicken = pd.concat([turkey, (chicken[chicken.index > last] * ratio)])
bls_oct_2019 = turkey[pd.Timestamp("2019-10-01")]
turkey_afbf = pd.concat([turkey, pd.Series(
    {pd.Timestamp(f"{y}-10-01"): bls_oct_2019 * v / AFBF_TURKEY[2019]
     for y, v in AFBF_TURKEY.items() if y > 2019})])
rec = pd.read_csv(ROOT / "output" / "turkey_price_nowcast.csv", parse_dates=["month"], index_col="month")
turkey_model = pd.concat([turkey, rec.loc[rec.index > last, "main_estimate"]])
turkey_flag = pd.Series(turkey_model.index > last, index=turkey_model.index)

# ---------------- Patch butter ----------------
b_old, b_new, dairy = load("APU0000710111").dropna(), load("APU0000FS1101").dropna(), load("CUUR0000SEFJ")
g0, g1 = b_old.index.max(), b_new.index.min()
r0, r1 = b_old[g0] / dairy[g0], b_new[g1] / dairy[g1]
gap = dairy[(dairy.index > g0) & (dairy.index < g1)]
w = (gap.index - g0).days / (g1 - g0).days
butter = pd.concat([b_old, gap * np.exp((1 - w) * np.log(r0) + w * np.log(r1)), b_new]).sort_index()
butter_flag = pd.Series((butter.index > g0) & (butter.index < g1), index=butter.index)

def fill_oct_2025(s):
    """Fill Octobers BLS never published because of government shutdowns (2013, 2025)
    with the Sep/Nov average, or whichever of the two exists."""
    s = s.copy()
    for yr in (2013, 2025):
        oct_, sep_, nov_ = (pd.Timestamp(f"{yr}-{m}-01") for m in ("10", "09", "11"))
        neighbors = s.reindex([sep_, nov_]).dropna()
        if pd.isna(s.get(oct_)) and len(neighbors):
            s[oct_] = neighbors.mean()
    return s.sort_index()


def anchored(item):
    """Farm Bureau anchor price, moved through time with its CPI component."""
    price, cpi_id = ANCHORS[item]
    cpi_s = fill_oct_2025(load(cpi_id))
    return price * cpi_s / cpi_s[pd.Timestamp(f"{ANCHOR_YEAR}-10-01")]


def build_prices(turkey_series):
    series = {"TURKEY": turkey_series, "BUTTER": butter}
    def get(item, sid):
        if sid == "ANCHOR":
            return anchored(item)
        return fill_oct_2025(series[sid]) if sid in series else fill_oct_2025(load(sid))
    df = pd.DataFrame({item: get(item, sid) for item, (sid, _, _) in BASKET.items()})
    df = df[df.index.month == MONTH]
    df.index = df.index.year
    return df.dropna()  # milk starts in 1995, so the index starts in 1995


prices = build_prices(turkey_model)
prices_afbf = build_prices(turkey_afbf)
prices_chicken = build_prices(turkey_chicken)

qty = pd.Series({k: v[1] for k, v in BASKET.items()})
cost = prices * qty                 # dollars per item
total = cost.sum(axis=1)
total_chicken = (prices_chicken * qty).sum(axis=1)
total_afbf = (prices_afbf * qty).sum(axis=1)

# ---------------- Deflators ----------------
def oct_series(sid):
    s = fill_oct_2025(load(sid))
    s = s[s.index.month == MONTH]
    s.index = s.index.year
    return s.reindex(total.index)

cpi = oct_series("CPIAUCSL")
food_home = oct_series("CUUR0000SAF11")
latest = total.index.max()
real_total = total * cpi[latest] / cpi  # in latest-year dollars

# ---------------- Index numbers (base = 2019, pre-pandemic) ----------------
BASE = 2019
rel = prices / prices.loc[BASE]
shares = cost.loc[BASE] / cost.loc[BASE].sum()
laspeyres = 100 * total / total[BASE]                      # fixed basket
geometric = 100 * np.exp((np.log(rel) * shares).sum(axis=1))  # Cobb-Douglas: allows substitution
cpi_food_idx = 100 * food_home / food_home[BASE]
cpi_all_idx = 100 * cpi / cpi[BASE]

# ---------------- Year-over-year decomposition ($) ----------------
contrib = cost.diff().dropna()

# ---------------- Farm Bureau benchmark (classic dinner for 10) ----------------
AFBF = {2015: 50.11, 2016: 49.87, 2017: 49.12, 2018: 48.90, 2019: 48.91, 2020: 46.90,
        2021: 53.31, 2022: 64.05, 2023: 61.17, 2024: 58.08, 2025: 55.18, 2026: 58.63}
afbf = pd.Series(AFBF)

# ---------------- Save tables ----------------
summary = pd.DataFrame({
    "basket_cost": total.round(2),
    "basket_cost_afbf_turkey": total_afbf.round(2),
    "basket_cost_chicken_proxy": total_chicken.round(2),
    f"basket_cost_{latest}_dollars": real_total.round(2),
    "laspeyres_2019=100": laspeyres.round(1),
    "geometric_2019=100": geometric.round(1),
    "cpi_food_at_home_2019=100": cpi_food_idx.round(1),
    "cpi_all_items_2019=100": cpi_all_idx.round(1),
    "afbf_survey": afbf.reindex(total.index),
    "turkey_estimated": turkey_flag[turkey_flag.index.month == MONTH].set_axis(
        turkey_flag[turkey_flag.index.month == MONTH].index.year).reindex(total.index),
    "butter_estimated": butter_flag[butter_flag.index.month == MONTH].set_axis(
        butter_flag[butter_flag.index.month == MONTH].index.year).reindex(total.index),
})
summary.index.name = "year"
summary["butter_estimated"] = summary["butter_estimated"].astype("boolean").fillna(False)
summary.to_csv(OUT / "index_summary.csv")
cost.round(2).to_csv(OUT / "item_costs.csv")
contrib.round(2).to_csv(OUT / "yoy_contributions.csv")

# ---------------- Charts ----------------
import chart_style as cs

SRC_BLS = "BLS average prices via FRED, American Farm Bureau Federation"

# 1. Cost as paid, with the Farm Bureau benchmark (comparison with overall prices is chart 2)
FLOOR = 0
fig, ax = cs.figure()
ax.axvspan(2019.5, latest + 0.5, color=cs.SHADE, zorder=0, lw=0)
ax.text(2019.7, 8, "Turkey price\nestimated by model", fontsize=8.5, color=cs.MUTED, style="italic")
ax.set_ylim(FLOOR, 110)
cs.soft_fill(ax, total.index, total, cs.RED, floor=FLOOR)
ax.plot(total.index, total, color=cs.RED)
cs.end_dot(ax, latest, total[latest], cs.RED)
ax.plot(total_afbf.loc[2019:].index, total_afbf.loc[2019:], color=cs.RED, lw=1.5, ls=(0, (2, 2)))
ax.plot(afbf.index, afbf, color=cs.DARK, lw=1.8, marker="o", ms=4.5, markeredgecolor=cs.BG)
ax.set_xlim(1994, latest + 1)
cs.baseline(ax, FLOOR)
ax.text(2002, total[2002] - 10, "Our basket (full menu)", color=cs.RED, fontsize=11, fontweight="bold")
ax.text(2012.3, afbf[2015] - 15, "Farm Bureau\nclassic menu", color=cs.DARK, fontsize=10, fontweight="semibold")
cs.label_end(ax, latest, total[latest], f"${total[latest]:.0f}", cs.RED, dy=3, size=11, dot=False)
cs.label_end(ax, latest, total_afbf[latest], "With Farm Bureau\nturkey price", cs.RED, dy=-3, weight="normal", size=9.5, dot=False)
cs.label_end(ax, latest, afbf[latest], f"${afbf[latest]:.0f}", cs.DARK, dy=-6, dot=False)
cs.unit_on_top(ax, prefix="$")
pct19 = 100 * (total[latest] / total[2019] - 1)
cs.finish(fig, f"Thanksgiving dinner for 10 costs ${total[latest]:.0f}, {pct19:.0f}% more than in 2019",
          "Cost at October prices, as paid. Full menu: turkey, ham, sides, rolls, pumpkin pie and baking staples.",
          SRC_BLS + "; turkey since 2020 is a model estimate", OUT / "1_dinner_cost.png")

# 2. Indexes
fig, ax = cs.figure()
lines = [(cpi_food_idx, "Groceries", cs.GREEN, 8), (cpi_all_idx, "All prices", cs.BLUE, 3),
         (laspeyres, "Dinner", cs.RED, -2.5), (geometric, "Dinner, w/ subst.", cs.GOLD, -8.5)]
for s, lab, c, dy in lines:
    ax.plot(s.index, s, color=c, lw=2.2 if c == cs.GOLD else 3)
    cs.label_end(ax, latest, s[latest], lab, c, dy=dy, size=9.5)
ax.set_xlim(1994, latest + 1)
cs.baseline(ax, 100)
cs.unit_on_top(ax)
gap = laspeyres[latest] - cpi_all_idx[latest]
verdict = ("in step with" if abs(gap) < 1.5 else ("a bit less than" if gap < 0 else "a bit more than"))
cs.finish(fig, f"Since 2019, the dinner's price has risen {verdict} prices overall",
          "Price indexes, October 2019 = 100. Groceries and all prices are CPI.",
          "BLS via FRED, American Farm Bureau Federation", OUT / "2_indexes.png")

# 3. YoY contributions
# Recent years, all nine items
recent = contrib.loc[2015:]
# Every item, each colored to suggest the food itself (continuing items keep their colors)
FOOD_COLORS = {
    "Turkey": "#C8553D",          # roast-turkey red
    "Ham": "#E8A2A2",             # ham pink
    "Russet potatoes": "#7A5A3A", # russet skin
    "Sweet potatoes": "#8C4A2F",  # sweet-potato skin
    "Stuffing mix": "#A67B4F",    # toasted bread
    "Dinner rolls": "#D9A86C",    # golden crust
    "Cranberries": "#7B1E3A",     # deep cranberry
    "Frozen peas": "#7FA650",     # pea green
    "Green beans": "#4E7A3A",     # bean green
    "Veggie tray": "#B5C98E",     # celery
    "Pumpkin pie mix": "#E07A1F", # pumpkin
    "Pie crusts": "#EAD2A8",      # pastry
    "Whipping cream": "#CFC6B8",  # cream
    "Milk": "#BFD5E6",            # milk-carton blue
    "Butter": "#F2CC4E",          # butter yellow
    "Eggs": "#F39B2E",            # yolk orange
    "Flour": "#E4D8C0",           # off-white flour
    "Sugar": "#B4BAC2",           # granulated, cool gray
}
groups = {name: ([name], FOOD_COLORS[name]) for name in BASKET}
fig, ax = cs.figure(height=7.2)
fig.subplots_adjust(top=0.64)
pos = np.zeros(len(recent)); neg = np.zeros(len(recent))
for name, (cols, c) in groups.items():
    v = recent[cols].sum(axis=1).values
    ax.bar(recent.index, v, bottom=np.where(v >= 0, pos, neg), color=c, width=0.72, label=name, zorder=3,
           edgecolor=cs.BG, linewidth=0.8)
    pos += np.where(v >= 0, v, 0); neg += np.where(v < 0, v, 0)
ax.scatter(recent.index, recent.sum(axis=1), color=cs.TEXT, s=46, zorder=4, label="Net change",
           edgecolor=cs.BG, linewidth=1.4)
cs.baseline(ax, 0)
ax.legend(ncol=5, loc="lower left", bbox_to_anchor=(0, 1.0), handlelength=1.2, columnspacing=1.2, fontsize=9.5)
from matplotlib.ticker import FuncFormatter
ax.set_xticks(recent.index)
ax.set_xticklabels([f"'{y % 100:02d}" for y in recent.index])
ax.set_yticks([-5, 0, 5, 10])
ax.set_ylim(-7.5, 13.5)
ax.yaxis.set_major_formatter(FuncFormatter(
    lambda v, _: "+$10" if v == 10 else ("0" if v == 0 else f"{v:+g}")))
cs.finish(fig, "Turkey drives most swings in the dinner's cost",
          "Change in the cost of a dinner for 10 vs. the previous October",
          "BLS via FRED; turkey since 2020 is a model estimate", OUT / "3_contributions.png")

# ---------------- Console report ----------------
pd.set_option("display.width", 160)
print(summary.loc[2015:].to_string())
print(f"\nLatest ({latest}) item costs:\n{cost.loc[latest].round(2).to_string()}")
print(f"\n{latest} vs prior year contributions ($):\n{contrib.loc[latest].round(2).sort_values().to_string()}")
print(f"\nBase-{BASE} expenditure shares:\n{shares.round(3).to_string()}")
c = pd.concat([total, afbf], axis=1, keys=["ours", "afbf"]).dropna().pct_change().dropna()
print("\nNote: from 2020 on, turkey follows the Farm Bureau's own turkey price, so the "
      "correlation below is partly built in.")
print(f"\nCorrelation of YoY % changes, ours vs Farm Bureau ({c.index.min()}-{c.index.max()}): "
      f"{c.corr().iloc[0,1]:.2f}")
