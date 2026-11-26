"""Thanksgiving Dinner Price Index, built from BLS average retail prices (via FRED).

Prices are taken in October of each year, the last month BLS publishes before
Thanksgiving (November data comes out in mid-December).

Menu: a Thanksgiving dinner for 10 built on the Farm Bureau's menus (see BASKET). Items BLS does
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
# (its classic menu plus russet potatoes and frozen green beans), without the ham, plus
# a gallon of apple cider.
# item: (source, quantity, unit). Source is a FRED id for a BLS average price, a patched
# series (TURKEY, BUTTER), or ANCHOR for items BLS does not price (see ANCHORS).
BASKET = {
    "Turkey":            ("TURKEY",        16.0, "lb"),
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
    "Apple cider":       ("ANCHOR",         1.0, "gallon"),
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
    # Apple cider: median of Nov 2026 grocery listings for a gallon (Costco $6.99 and $5.51,
    # Meijer $7.49, Price Chopper $6.99), moved with the nonalcoholic beverages CPI.
    "Apple cider":     (6.99, "CUUR0000SAF114"),
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

# ---------------- New York City prices ----------------
# Items on the New York Post's 2025/2026 NYC Thanksgiving price survey (data/nyc_post_prices.csv)
# use those NYC shelf prices, scaled to our quantities. 2026 = the Post's 2026 price. Earlier
# years start from the Post's 2025 price and move back with the item's own BLS price history
# (turkey, milk, butter, flour) or its CPI item group, using October values.
# Items not on the Post's list = national price x an NYC factor: BEA's Regional Price Parity
# for goods in the New York-Newark-Jersey City metro (2024), moved over time with the ratio of
# the New York metro to U.S. food-at-home CPI.
post = pd.read_csv(DATA / "nyc_post_prices.csv").set_index("post_item")
POST_MAP = {  # our item: (Post item, Post units needed for our quantity, index used to go back in time)
    "Turkey":          ("Bell & Evans Turkey (20 lbs)", 16 / 20, "TURKEY"),
    "Sweet potatoes":  ("Yams (per lb)", 3, "CUUR0000SAF113"),
    "Stuffing mix":    ("Stove Top Stuffing", 14 / 6, "CUUR0000SAF111"),
    "Dinner rolls":    ("Pillsbury Crescent Rolls", 12 / 8, "CUUR0000SAF111"),
    "Cranberries":     ("Cranberry Sauce (can)", 1, "CUUR0000SAF113"),
    "Veggie tray":     ("Baby Peeled Carrots (1 lb)", 1, "CUUR0000SAF113"),
    "Pumpkin pie mix": ("Libby's 100% Pure Pumpkin", 2, "CUUR0000SAF113"),
    "Apple cider":     ("Apple Cider (64 fl oz)", 2, "CUUR0000SAF114"),
    "Milk":            ("Whole Milk (half gal Farmland)", 2, "APU0000709112"),
    "Butter":          ("Land O'Lakes Butter (lb)", 1, "BUTTER"),
    "Flour":           ("Hecker's Flour (5 lb)", 1 / 5, "APU0000701111"),
}
POST_BASE, POST_LATEST = 2025, 2026


def october_index(sid):
    series = {"TURKEY": turkey_model, "BUTTER": butter}
    s_ = fill_oct_2025(series[sid] if sid in series else load(sid))
    s_ = s_[s_.index.month == MONTH]
    s_.index = s_.index.year
    return s_.reindex(total.index)


NYC_ANCHOR_YEAR = 2024
rpp_goods = load("RPPGOOD35620")
rpp_goods.index = rpp_goods.index.year
ny_us = (load("CUURA101SAF11") / load("CUUR0000SAF11")).dropna()
ny_us = ny_us.groupby(ny_us.index.year).mean()
nyc_factor = (ny_us / ny_us[NYC_ANCHOR_YEAR] * rpp_goods[NYC_ANCHOR_YEAR] / 100).reindex(total.index)

cost_nyc = cost.mul(nyc_factor, axis=0)          # default: national x NYC factor
post_check = []
for item, (post_item, units, sid) in POST_MAP.items():
    idx = october_index(sid)
    base = post.loc[post_item, "price_2025"] * units
    series_ = base * idx / idx[POST_BASE]
    series_[POST_LATEST] = post.loc[post_item, "price_2026"] * units
    cost_nyc[item] = series_
    post_check.append({"item": item, "post_item": post_item, "units": round(units, 3),
                       "nyc_2025": round(base, 2), "nyc_2026": round(series_[POST_LATEST], 2),
                       "post_change_%": round(100 * (post.loc[post_item, "price_2026"] / post.loc[post_item, "price_2025"] - 1), 1),
                       "index_change_%": round(100 * (idx[POST_LATEST] / idx[POST_BASE] - 1), 1),
                       "national_2026": round(cost.loc[POST_LATEST, item], 2)})
for item in BASKET:
    if item not in POST_MAP:
        post_check.append({"item": item, "post_item": "(not on Post list: national x NYC factor)", "units": None,
                           "nyc_2025": round(cost_nyc.loc[POST_BASE, item], 2), "nyc_2026": round(cost_nyc.loc[POST_LATEST, item], 2),
                           "post_change_%": None, "index_change_%": None,
                           "national_2026": round(cost.loc[POST_LATEST, item], 2)})
total_nyc = cost_nyc.sum(axis=1)
contrib_nyc = cost_nyc.diff().dropna()

# ---------------- Save tables ----------------
summary = pd.DataFrame({
    "basket_cost": total.round(2),
    "basket_cost_nyc": total_nyc.round(2),
    "nyc_price_factor": nyc_factor.round(4),
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
cost_nyc.round(2).to_csv(OUT / "item_costs_nyc.csv")
pd.DataFrame(post_check).to_csv(OUT / "nyc_item_sources.csv", index=False)

# ---------------- Charts ----------------
import chart_style as cs

SRC_BLS = "BLS average prices via FRED, American Farm Bureau Federation"

# 1. NYC cost as paid, with the U.S. average and the Farm Bureau benchmark
FLOOR = 0
fig, ax = cs.figure()
fig.subplots_adjust(right=0.82)
ax.axvspan(2019.5, latest + 0.5, color=cs.SHADE, zorder=0, lw=0)
ax.text(2019.7, 8, "Turkey price\nestimated by model", fontsize=8.5, color=cs.MUTED, style="italic")
ax.set_ylim(FLOOR, 20 * np.ceil(total_nyc.max() * 1.12 / 20))
ax.plot(total_nyc.index, total_nyc, color=cs.RED)
ax.plot(total.index, total, color=cs.GOLD, lw=2.4)
ax.plot(afbf.index, afbf, color=cs.DARK, lw=1.8, marker="o", ms=4.5, markeredgecolor=cs.BG)
ax.set_xlim(1994, latest + 1)
cs.baseline(ax, FLOOR)
ax.text(2012.3, afbf[2015] - 20, "Farm Bureau\nclassic menu", color=cs.DARK, fontsize=10, fontweight="semibold")
cs.label_end(ax, latest, total_nyc[latest], f"Typical Thanksgiving\ndinner, NYC: ${total_nyc[latest]:.0f}", cs.RED, dy=0, size=11, weight="bold", dot=False)
cs.label_end(ax, latest, total[latest], f"U.S. average: ${total[latest]:.0f}", cs.GOLD, dy=4, size=10.5, dot=False)
cs.label_end(ax, latest, afbf[latest], f"${afbf[latest]:.0f}", cs.DARK, dy=-6, dot=False)
cs.unit_on_top(ax, prefix="$")
pct19 = 100 * (total_nyc[latest] / total_nyc[2019] - 1)
cs.finish_geo("nyc+us", fig, f"Thanksgiving dinner for 10 in NYC costs ${total_nyc[latest]:.0f}, {pct19:.0f}% more than in 2019",
          "Cost at Thanksgiving prices, as paid. Full menu: turkey, sides, rolls, pumpkin pie, apple cider and baking staples.",
          "New York Post NYC price survey; BLS and BEA via FRED; American Farm Bureau Federation", OUT / "1_dinner_cost.png",
          note=("NYC prices: 11 of 18 items use the New York Post's 2025 and 2026 NYC supermarket prices, scaled to "
                "this menu; earlier years move back from 2025 with each item's BLS price history or CPI group. "
                "Other items are U.S. average prices x BEA's New York metro price parity. The 2025-2026 jump "
                "reflects the Post's store prices, which rose much faster than BLS indexes for the same items. "
                "U.S. line: BLS national average prices; turkey since 2020 from a backtested machine-learning model."))

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
cs.finish_geo("us", fig, f"Since 2019, the dinner's price has risen {verdict} prices overall",
          "Price indexes, October 2019 = 100. Dinner at U.S. average prices; groceries and all prices are CPI.",
          "BLS via FRED, American Farm Bureau Federation", OUT / "2_indexes.png")

# 3. YoY contributions
# Recent years, all nine items
recent = contrib.loc[2015:]
# Every item, each colored to suggest the food itself (continuing items keep their colors)
FOOD_COLORS = {
    "Turkey": "#C8553D",          # roast-turkey red
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
    "Apple cider": "#C9822B",     # cider amber
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
lo, hi = min(-7.5, neg.min() * 1.1), max(13.5, pos.max() * 1.08)
step = 5 if hi < 25 else 10
ticks = [t for t in range(-100, 101, step) if lo <= t <= hi]
ax.set_yticks(ticks)
ax.set_ylim(lo, hi)
ax.yaxis.set_major_formatter(FuncFormatter(
    lambda v, _: f"+${v:g}" if v == max(ticks) else ("0" if v == 0 else f"{v:+g}")))
cs.finish_geo("us", fig, "Turkey drives most swings in the dinner's cost",
          "Change in the cost of a dinner for 10 at U.S. average prices vs. the previous October",
          "BLS via FRED; turkey since 2020 is a model estimate", OUT / "3_contributions.png")

# ---------------- Console report ----------------
pd.set_option("display.width", 160)
print(summary.loc[2015:].to_string())
print(f"\nLatest ({latest}) item costs:\n{cost.loc[latest].round(2).to_string()}")
print(f"\n{latest} vs prior year contributions ($):\n{contrib.loc[latest].round(2).sort_values().to_string()}")
print(f"\nBase-{BASE} expenditure shares:\n{shares.round(3).to_string()}")
c = pd.concat([total, afbf], axis=1, keys=["ours", "afbf"]).dropna().pct_change().dropna()
print("\nNote: from 2020 on, turkey is a model estimate built without Farm Bureau data, so the "
      "correlation below is an independent check.")
print(f"\nCorrelation of YoY % changes, ours vs Farm Bureau ({c.index.min()}-{c.index.max()}): "
      f"{c.corr().iloc[0,1]:.2f}")
