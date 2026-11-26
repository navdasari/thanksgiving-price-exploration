"""Who is squeezed? Testing the averages behind the Thanksgiving affordability story.

Run build_index.py first. Questions:
  A. Do essentials take a record share for specific household types, not just income
     quintiles (renters, single parents, young families, young adults, retirees)?
  B. Does it matter how "essentials" is defined? Narrow = shelter, utilities, food at
     home, health care. Broad = narrow + household operations (which includes child
     care and babysitting) + vehicle insurance.
  C. Does it matter whether the budget is spending or before-tax income?
  D. How much is left after broad essentials, in real dollars, and how has that changed?
  E. Low-wage workers: dinner cost in hours at the federal minimum wage and as a share
     of first-decile full-time weekly earnings.
  F. Price level vs low-wage pay since January 2021 (prices never come back down).
  G. Rent vs overall prices; household financial stress (saving rate, card delinquency).

All Consumer Expenditure Survey (CE) data are annual group averages, 1995-2025, via FRED.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
DATA, CEX, OUT = ROOT / "data", ROOT / "data" / "cex", ROOT / "output"

GROUPS = {
    "LB0102": "Income: lowest 20%", "LB0103": "Income: second 20%", "LB0104": "Income: middle 20%",
    "LB0105": "Income: fourth 20%", "LB0106": "Income: highest 20%",
    "LB1705": "Renters", "LB1702": "Homeowners",
    "LB0609": "Single parents", "LB0605": "Married, oldest child under 6",
    "LB0606": "Married, oldest child 6-17",
    "LB0402": "Age under 25", "LB0403": "Age 25-34", "LB0408": "Age 65-74", "LB0409": "Age 75+",
}
NARROW = ["SHELTER", "UTILS", "FOODHOME", "HEALTH"]
BROAD = NARROW + ["HHOPER", "500110"]


def cex(code, g):
    sid = f"CXU{code}{g}M"
    s = pd.read_csv(CEX / f"{sid}.csv", parse_dates=["observation_date"], na_values=".")
    s = s.set_index("observation_date")[sid].astype(float).dropna()
    s.index = s.index.year
    return s


def fred(sid, month=None):
    s = pd.read_csv(DATA / f"{sid}.csv", parse_dates=["observation_date"], na_values=".")
    s = s.set_index("observation_date")[sid].astype(float).dropna()
    if month is not None:
        s = s[s.index.month == month]
        s.index = s.index.year
    return s


summary = pd.read_csv(OUT / "index_summary.csv", index_col="year")
dinner = summary["basket_cost"]
cpi_annual = fred("CPIAUCSL").groupby(lambda d: d.year).mean()

# ---------------- A-D: household groups ----------------
rows = []
for g, name in GROUPS.items():
    df = pd.DataFrame({
        "spending": cex("TOTALEXP", g),
        "income_pretax": cex("INCBFTAX", g),
        "ess_narrow": sum(cex(c, g) for c in NARROW),
        "ess_broad": sum(cex(c, g) for c in BROAD),
        "childcare_hhops": cex("HHOPER", g),
    }).loc[1995:]
    df = df.join(dinner.rename("dinner"), how="inner")
    df["narrow_pct_spending"] = 100 * df.ess_narrow / df.spending
    df["broad_pct_spending"] = 100 * df.ess_broad / df.spending
    df["broad_pct_income"] = 100 * df.ess_broad / df.income_pretax
    df["left_after_broad_income_real2025"] = (df.income_pretax - df.ess_broad) * cpi_annual[2025] / cpi_annual.reindex(df.index)
    df["left_after_broad_spending_real2025"] = (df.spending - df.ess_broad) * cpi_annual[2025] / cpi_annual.reindex(df.index)
    df["dinner_pct_week_income"] = 100 * df.dinner / (df.income_pretax / 52)
    df["dinner_pct_week_left_after_broad_spending"] = 100 * df.dinner / ((df.spending - df.ess_broad) / 52)
    df["group"] = name
    rows.append(df)
panel = pd.concat(rows).reset_index(names="year")
panel.round(3).to_csv(OUT / "deep_dive_groups.csv", index=False)


def rank_last(s):
    """Rank of 2025 from the top (1 = highest value in 1995-2025)."""
    s = s.dropna()
    return int(s.rank(ascending=False).loc[2025]), len(s)


rec = []
for name, g in panel.groupby("group", sort=False):
    g = g.set_index("year")
    r = {"group": name}
    for col, short in [("narrow_pct_spending", "narrow%spend"), ("broad_pct_spending", "broad%spend"),
                       ("broad_pct_income", "broad%income")]:
        r[f"{short} 2019"] = g.loc[2019, col]
        r[f"{short} 2025"] = g.loc[2025, col]
        r[f"{short} rank"] = "{}/{}".format(*rank_last(g[col]))
    # 3-year averages: single CE years are noisy for small groups (e.g. young families in 2019)
    r["left$ 2017-19"] = g.loc[2017:2019, "left_after_broad_income_real2025"].mean()
    r["left$ 2023-25"] = g.loc[2023:2025, "left_after_broad_income_real2025"].mean()
    r["broad%spend 2017-19"] = g.loc[2017:2019, "broad_pct_spending"].mean()
    r["broad%spend 2023-25"] = g.loc[2023:2025, "broad_pct_spending"].mean()
    r["dinner%wk_inc 2019"] = g.loc[2019, "dinner_pct_week_income"]
    r["dinner%wk_inc 2022"] = g.loc[2022, "dinner_pct_week_income"]
    r["dinner%wk_inc 2025"] = g.loc[2025, "dinner_pct_week_income"]
    r["dinner%wk_inc rank_low"] = int(g.dinner_pct_week_income.rank().loc[2025])
    rec.append(r)
table = pd.DataFrame(rec).set_index("group")
table.round(1).to_csv(OUT / "deep_dive_table.csv")

pd.set_option("display.width", 250, "display.max_columns", 30)
print("== A-C. Essentials share, 2019 vs 2025; rank of 2025 among 1995-2025 (1 = highest burden) ==")
print(table[[c for c in table.columns if "%" in c and "dinner" not in c and "-" not in c]].round(1).to_string())
print("\n== D. Before-tax income left after broad essentials, 2025 dollars, 3-year averages ==")
print(table[["left$ 2017-19", "left$ 2023-25"]].assign(change=lambda t: t["left$ 2023-25"] - t["left$ 2017-19"]).round(0).to_string())
print("\n== Essentials incl. child care, % of spending, 3-year averages ==")
print(table[["broad%spend 2017-19", "broad%spend 2023-25"]].assign(change=lambda t: t["broad%spend 2023-25"] - t["broad%spend 2017-19"]).round(1).to_string())
print("\n== Dinner as % of a week's before-tax income (rank_low: 1 = most affordable of 31 years) ==")
print(table[[c for c in table.columns if c.startswith("dinner")]].round(1).to_string())

# ---------------- E. Low-wage workers ----------------
minwage = fred("FEDMINNFRWG", 10)
decile1 = fred("LEU0252911200Q", 7)  # Q3, full-time weekly earnings, 10th percentile
wage = pd.DataFrame({"dinner": dinner, "federal_min_wage": minwage.reindex(dinner.index),
                     "decile1_weekly": decile1.reindex(dinner.index)})
wage["hours_at_federal_min"] = wage.dinner / wage.federal_min_wage
wage["pct_of_decile1_week"] = 100 * wage.dinner / wage.decile1_weekly
wage.round(2).to_csv(OUT / "deep_dive_wages.csv")
print("\n== E. Low-wage workers ==")
print(wage.loc[[1995, 2000, 2005, 2009, 2010, 2015, 2019, 2021, 2022, 2023, 2024, 2025, 2026]].round(2).to_string())
print("hours at federal minimum, 2026 rank (1 = most hours):",
      int(wage.hours_at_federal_min.rank(ascending=False).loc[2026]), "of", wage.hours_at_federal_min.notna().sum())

# ---------------- F. Price level vs low-wage pay ----------------
cpi_m = fred("CPIAUCSL")
dec_q = fred("LEU0252911200Q")
rent = fred("CUUR0000SEHA")
base_p, base_w = cpi_m.loc["2021-01-01"], dec_q.loc["2021-01-01"]
print("\n== F. Since Jan 2021 ==")
print(f"  CPI all items:              {100*(cpi_m.iloc[-1]/base_p-1):+.1f}%  (to {cpi_m.index[-1]:%b %Y})")
print(f"  Rent of primary residence:  {100*(rent.iloc[-1]/rent.loc['2021-01-01']-1):+.1f}%")
print(f"  10th-pct full-time pay:     {100*(dec_q.iloc[-1]/base_w-1):+.1f}%  (to {dec_q.index[-1]:%b %Y})")
print(f"  Federal minimum wage:       +0.0%  ($7.25 since July 2009)")
print(f"  Since July 2009, CPI is up {100*(cpi_m.iloc[-1]/cpi_m.loc['2009-07-01']-1):.0f}%, "
      f"so $7.25 buys {100*(cpi_m.loc['2009-07-01']/cpi_m.iloc[-1]):.0f}% of what it did")

# ---------------- G. Financial stress ----------------
sav, dq = fred("PSAVERT"), fred("DRCCLACBS")
print("\n== G. Financial stress ==")
print(f"  Personal saving rate: 2019 avg {sav.loc['2019'].mean():.1f}%, latest {sav.iloc[-1]:.1f}% ({sav.index[-1]:%b %Y}), "
      f"1995-2019 avg {sav.loc['1995':'2019'].mean():.1f}%")
print(f"  Credit card delinquency: 2019 avg {dq.loc['2019'].mean():.2f}%, latest {dq.iloc[-1]:.2f}% ({dq.index[-1]:%b %Y}), "
      f"1995-2019 avg {dq.loc['1995':'2019'].mean():.2f}%, 2021 low {dq.loc['2021'].min():.2f}%")


# ---------------- H. Robustness ----------------
# H1: CE income methods changed in 2004 (imputation of missing income) and 2013 (new
#     income questions), so income-based ranks are only compared within 2004-2025 and 2013-2025.
print("\n== H1. Rank of 2025 (1 = highest burden) for essentials as % of before-tax income, by window ==")
out = {}
for name, g in panel.groupby("group", sort=False):
    g = g.set_index("year").broad_pct_income
    out[name] = {f"{lo}-2025": "{}/{}".format(int(g.loc[lo:].rank(ascending=False).loc[2025]), len(g.loc[lo:]))
                 for lo in (1995, 2004, 2013)}
    out[name]["2013"] = round(g.loc[2013], 1); out[name]["2019"] = round(g.loc[2019], 1); out[name]["2025"] = round(g.loc[2025], 1)
print(pd.DataFrame(out).T.to_string())

# H2: turkey after 2019 is estimated. Re-run the dinner measures with the chicken-based proxy.
alt = summary["basket_cost_chicken_proxy"]
print("\n== H2. Dinner measures with turkey proxied by chicken instead of Farm Bureau turkey prices ==")
low = panel[panel.group == "Income: lowest 20%"].set_index("year")
d_alt = 100 * alt.reindex(low.index) / (low.income_pretax / 52)
print(f"  Lowest 20%, dinner % of week's income: 2019 {d_alt[2019]:.1f}, 2022 {d_alt[2022]:.1f}, 2025 {d_alt[2025]:.1f}; "
      f"2025 rank (1 = most affordable) {int(d_alt.rank().loc[2025])}/{len(d_alt)}")
h_alt = alt / minwage.reindex(alt.index)
print(f"  Hours at federal minimum: 2019 {h_alt[2019]:.2f}, 2026 {h_alt[2026]:.2f}; "
      f"2026 rank (1 = most hours) {int(h_alt.rank(ascending=False).loc[2026])}/{h_alt.notna().sum()}")
p_alt = 100 * alt / wage.decile1_weekly
print(f"  % of 10th-pct weekly pay: 2019 {p_alt[2019]:.1f}, 2026 {p_alt[2026]:.1f}; "
      f"2026 rank (1 = most affordable) {int(p_alt.rank().loc[2026])}/{p_alt.notna().sum()}")

# ---------------- Charts ----------------
plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.3, "font.size": 9})
show = ["Income: lowest 20%", "Income: second 20%", "Renters", "Single parents",
        "Married, oldest child under 6", "Age under 25", "Income: highest 20%"]
colors = ["#b5541c", "#e0a458", "#2f7d4f", "#8e44ad", "#c0392b", "#7f93b8", "#5b6c8f"]
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for name, c in zip(show, colors):
    g = panel[panel.group == name]
    axes[0].plot(g.year, g.broad_pct_spending, color=c, lw=2 if "lowest" in name or name == "Single parents" else 1.3, label=name)
    if name != "Income: highest 20%":
        axes[1].plot(g.year, g.left_after_broad_income_real2025 / 1000, color=c, lw=2 if "lowest" in name or name == "Single parents" else 1.3)
axes[0].set(title="Essentials incl. child care, % of spending", ylabel="%")
axes[1].axhline(0, color="black", lw=0.7)
axes[1].set(title="Before-tax income left after essentials (2025 $, thousands; top 20% omitted)", ylabel="$k")
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(OUT / "7_who_is_squeezed.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.5))
w = wage.dropna(subset=["hours_at_federal_min"])
ax.plot(w.index, w.hours_at_federal_min, color="#b5541c", lw=2.2, label="Hours at federal minimum wage")
ax2 = ax.twinx()
ax2.plot(w.index, w.pct_of_decile1_week, color="#5b6c8f", lw=1.6, ls="--", label="% of 10th-percentile weekly pay (right)")
ax2.spines["top"].set_visible(False)
ax.set(title="Thanksgiving dinner for 10, for low-wage workers", ylabel="hours")
ax2.set_ylabel("%")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(OUT / "8_low_wage.png"); plt.close(fig)
