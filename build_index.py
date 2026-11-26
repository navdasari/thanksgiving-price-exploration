"""Thanksgiving Dinner Price Index, built from BLS average retail prices (via FRED).

Prices are taken in October of each year, the last month BLS publishes before
Thanksgiving (November data comes out in mid-December).

Data patches (flagged in the output):
  * Turkey: BLS stopped publishing APU0000706311 after Feb 2020. After Oct 2019 the
    price follows the Farm Bureau turkey price (chicken-based proxy kept for comparison).
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
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "output"
OUT.mkdir(exist_ok=True)
MONTH = 10  # October


def load(sid):
    df = pd.read_csv(DATA / f"{sid}.csv", parse_dates=["observation_date"], na_values=".")
    return df.set_index("observation_date")[sid].astype(float)


# ---------------- Basket: classic dinner for 10 ----------------
# item: (FRED id, quantity, unit)
BASKET = {
    "Turkey":          ("TURKEY",        16.0, "lb"),
    "Potatoes":        ("APU0000712112",  5.0, "lb"),
    "Bread (stuffing)": ("APU0000702111", 1.0, "lb"),
    "Flour (rolls, crust)": ("APU0000701111", 3.0, "lb"),
    "Butter":          ("BUTTER",         1.0, "lb"),
    "Eggs":            ("APU0000708111",  1.0, "doz"),
    "Milk":            ("APU0000709112",  1.0, "gal"),
    "Sugar":           ("APU0000715211",  2.0, "lb"),
    "Ice cream (pie)": ("APU0000710411",  1.0, "half gal"),
}

# ---------------- Patch turkey ----------------
# Main version: carry the last BLS October turkey price (2019) forward with the
# year-to-year change in the Farm Bureau's 16-lb turkey price.
# Comparison version: whole-chicken price times the Feb 2020 turkey/chicken ratio.
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
turkey_flag = pd.Series(turkey_afbf.index > last, index=turkey_afbf.index)

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


def build_prices(turkey_series):
    series = {"TURKEY": turkey_series, "BUTTER": butter}
    df = pd.DataFrame({item: fill_oct_2025(series[sid]) if sid in series else fill_oct_2025(load(sid))
                       for item, (sid, _, _) in BASKET.items()})
    df = df[df.index.month == MONTH]
    df.index = df.index.year
    return df.dropna()  # milk starts in 1995, so the index starts in 1995


prices = build_prices(turkey_afbf)
prices_chicken = build_prices(turkey_chicken)

qty = pd.Series({k: v[1] for k, v in BASKET.items()})
cost = prices * qty                 # dollars per item
total = cost.sum(axis=1)
total_chicken = (prices_chicken * qty).sum(axis=1)

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
plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.3, "font.size": 10})

# 1. Nominal vs real cost, with the Farm Bureau benchmark
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(total.index, total, color="#b5541c", lw=2.2, label="Our basket (nominal)")
ax.plot(real_total.index, real_total, color="#5b6c8f", lw=2.2, ls="--",
        label=f"Our basket (in {latest} dollars)")
ax.plot(total_chicken.loc[2019:].index, total_chicken.loc[2019:], color="#b5541c", lw=1, ls=":",
        label="Our basket, turkey proxied by chicken")
ax.plot(afbf.index, afbf, "o-", color="#2f7d4f", ms=4, lw=1.4, label="Farm Bureau survey (nominal)")
ax.axvspan(2019.5, latest + 0.5, color="grey", alpha=0.08)
ax.text(2019.7, ax.get_ylim()[0] + 1, "turkey price from Farm Bureau survey", fontsize=8, color="grey")
ax.set(title="Cost of a Thanksgiving dinner for 10 (October prices)", ylabel="$", xlabel="")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "1_dinner_cost.png"); plt.close(fig)

# 2. Indexes
fig, ax = plt.subplots(figsize=(9, 5))
for s, lab, c, ls in [(laspeyres, "Dinner, fixed basket (Laspeyres)", "#b5541c", "-"),
                      (geometric, "Dinner, Cobb-Douglas (geometric)", "#e0a458", "-"),
                      (cpi_food_idx, "CPI: food at home", "#2f7d4f", "--"),
                      (cpi_all_idx, "CPI: all items", "#5b6c8f", ":")]:
    ax.plot(s.index, s, lw=2, color=c, ls=ls, label=lab)
ax.axhline(100, color="black", lw=0.6)
ax.set(title="Price indexes, October 2019 = 100", xlabel="")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "2_indexes.png"); plt.close(fig)

# 3. YoY contributions, recent years
recent = contrib.loc[2015:]
fig, ax = plt.subplots(figsize=(10, 5.5))
colors = plt.cm.tab10(np.arange(len(recent.columns)))
pos_bottom = np.zeros(len(recent)); neg_bottom = np.zeros(len(recent))
for col, c in zip(recent.columns, colors):
    v = recent[col].values
    b = np.where(v >= 0, pos_bottom, neg_bottom)
    ax.bar(recent.index, v, bottom=b, color=c, label=col, width=0.75)
    pos_bottom += np.where(v >= 0, v, 0); neg_bottom += np.where(v < 0, v, 0)
ax.plot(recent.index, recent.sum(axis=1), "kD", ms=5, label="Net change")
ax.axhline(0, color="black", lw=0.8)
ax.set(title="What drove the year-over-year change in dinner cost?", ylabel="$ change vs prior October")
ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
fig.tight_layout(); fig.savefig(OUT / "3_contributions.png"); plt.close(fig)

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
