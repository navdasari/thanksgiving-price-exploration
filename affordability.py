"""How affordable is Thanksgiving dinner relative to income?

Run build_index.py first. This compares the dinner's cost with:
  1. Hours of work at the average hourly wage of production and nonsupervisory
     workers (AHETPI, October).
  2. Share of a week's median household income (Census, annual; latest is 2025).
  3. Per-guest cost as a share of a day's disposable income per person (A229RC0, October).
  4. Per-guest cost as a share of a day's "discretionary" income per person:
     disposable income minus spending on housing and utilities, food at home,
     health care, and gasoline and other energy goods (BEA PCE, Q3 of each year).
"""
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "output"
GUESTS = 10


def load(sid, month=None):
    s = pd.read_csv(DATA / f"{sid}.csv", parse_dates=["observation_date"], na_values=".")
    s = s.set_index("observation_date")[sid].astype(float).dropna()
    if month:
        s = s[s.index.month == month]
    s.index = s.index.year
    return s


summary = pd.read_csv(OUT / "index_summary.csv", index_col="year")
dinner = summary["basket_cost"]
afbf = summary["afbf_survey"]
years = dinner.index

wage = load("AHETPI", 10).reindex(years)
median_hh = load("MEHOINUSA646N").reindex(years)
dpi_pc = load("A229RC0", 10).reindex(years)  # $ per person per year (annual rate)

# Essentials from quarterly PCE (billions, annual rate), Q3 = the quarter before Thanksgiving
ESSENTIALS = {"Housing & utilities": "DHUTRC1Q027SBEA", "Food at home": "DFXARC1Q027SBEA",
              "Health care": "DHLCRC1Q027SBEA", "Gasoline & energy goods": "DGOERC1Q027SBEA"}
pop_q3 = load("POPTHM", 8)  # thousands, mid-Q3
dpi_q3 = load("A229RC0", 8)
ess_pc = pd.DataFrame({k: load(v, 7) * 1e9 / (pop_q3 * 1e3) for k, v in ESSENTIALS.items()})
discretionary_pc = (dpi_q3 - ess_pc.sum(axis=1)).reindex(years)
ess_share = (ess_pc.sum(axis=1) / dpi_q3).reindex(years)

out = pd.DataFrame({
    "dinner_cost": dinner,
    "hours_of_work": dinner / wage,
    "pct_of_median_hh_week": 100 * dinner / (median_hh / 52),
    "per_guest_pct_of_daily_dpi": 100 * (dinner / GUESTS) / (dpi_pc / 365),
    "per_guest_pct_of_daily_discretionary": 100 * (dinner / GUESTS) / (discretionary_pc / 365),
    "essentials_share_of_dpi": 100 * ess_share,
    "afbf_hours_of_work": afbf / wage,
})
out.round(3).to_csv(OUT / "affordability.csv")

pd.set_option("display.width", 160)
print(out.loc[2015:].round(2).to_string())
print("\nRank of 2026 among years with data (1 = most affordable):")
for col in ["hours_of_work", "pct_of_median_hh_week", "per_guest_pct_of_daily_dpi",
            "per_guest_pct_of_daily_discretionary", "afbf_hours_of_work"]:
    x = out[col].dropna()
    yr = 2026 if 2026 in x.index else x.index.max()
    print(f"  {col:40s} {yr}: rank {int(x.rank().loc[yr])}/{len(x)} ({x.index.min()}-{x.index.max()}); "
          f"best year {x.idxmin()}")
print("\nEssentials per person, Q3 ($/yr):")
print(ess_pc.loc[[2019, 2022, 2025, 2026]].round(0).to_string())

# ---------- Charts ----------
plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.3, "font.size": 10})
cpi = summary["cpi_all_items_2019=100"]
real = dinner / cpi * 100
fig, ax = plt.subplots(figsize=(9, 5))
for s, lab, c, ls in [(real, "Inflation-adjusted cost", "#b5541c", "-"),
                      (out.hours_of_work, "Hours of work (avg wage)", "#2f7d4f", "-"),
                      (out.per_guest_pct_of_daily_dpi, "Share of disposable income", "#5b6c8f", "--"),
                      (out.per_guest_pct_of_daily_discretionary, "Share of discretionary income", "#e0a458", "-")]:
    s = s.dropna()
    ax.plot(s.index, 100 * s / s.loc[2019], lw=2, color=c, ls=ls, label=lab)
ax.axhline(100, color="black", lw=0.6)
ax.set(title="Thanksgiving dinner affordability, 2019 = 100 (lower = more affordable)", xlabel="")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "4_affordability.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.5))
e = out.essentials_share_of_dpi.dropna()
ax.plot(e.index, e, lw=2.2, color="#5b6c8f")
ax.set(title="Spending on housing, groceries, health care and energy, % of disposable income",
       ylabel="%", xlabel="")
fig.tight_layout(); fig.savefig(OUT / "5_essentials_share.png"); plt.close(fig)
