"""Is Thanksgiving dinner less affordable for lower-income households?

Run build_index.py first. Uses the BLS Consumer Expenditure Survey by quintile of
pre-tax income (annual, via FRED). The budget measure is total annual spending, not
income: in the survey the lowest quintile reports spending about twice its after-tax
income (under-reported income, transfers, retirees drawing on savings), so income-based
shares would be misleading for that group. After-tax income is shown as a cross-check
through 2023, the last year FRED has it.

Essentials = shelter + utilities + food at home + health care. Gasoline is left out
because FRED's quintile gasoline series is broken from 2023 (it reports $1).
Dinner cost = the October basket for that year, compared with that year's spending.
"""
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
CEX, OUT = ROOT / "data" / "cex", ROOT / "output"
QUINTILES = {"02": "Lowest 20%", "03": "Second 20%", "04": "Middle 20%",
             "05": "Fourth 20%", "06": "Highest 20%"}
ESSENTIALS = ["SHELTER", "UTILS", "FOODHOME", "HEALTH"]


def load(code, q):
    sid = f"CXU{code}LB01{q}M"
    s = pd.read_csv(CEX / f"{sid}.csv", parse_dates=["observation_date"], na_values=".")
    s = s.set_index("observation_date")[sid].astype(float).dropna()
    s.index = s.index.year
    return s


dinner = pd.read_csv(OUT / "index_summary.csv", index_col="year")["basket_cost"]

rows = []
for q, name in QUINTILES.items():
    total = load("TOTALEXP", q)
    ess = sum(load(c, q) for c in ESSENTIALS)
    inc = load("INCAFTTX", q)
    df = pd.DataFrame({"total_spending": total, "essentials": ess, "income_after_tax": inc})
    df = df.join(dinner.rename("dinner_cost"), how="inner")
    df["essentials_pct_of_spending"] = 100 * df.essentials / df.total_spending
    df["dinner_pct_of_week_spending"] = 100 * df.dinner_cost / (df.total_spending / 52)
    df["dinner_pct_of_week_nonessential"] = 100 * df.dinner_cost / ((df.total_spending - df.essentials) / 52)
    df["dinner_pct_of_week_income"] = 100 * df.dinner_cost / (df.income_after_tax / 52)
    df["quintile"] = name
    rows.append(df)

panel = pd.concat(rows).reset_index(names="year")
panel.round(3).to_csv(OUT / "by_income.csv", index=False)

pd.set_option("display.width", 160)
for col, label in [("essentials_pct_of_spending", "Essentials, % of total spending"),
                   ("dinner_pct_of_week_spending", "Dinner, % of a week's spending"),
                   ("dinner_pct_of_week_nonessential", "Dinner, % of a week's non-essential spending"),
                   ("dinner_pct_of_week_income", "Dinner, % of a week's after-tax income (to 2023)")]:
    t = panel.pivot(index="year", columns="quintile", values=col)[list(QUINTILES.values())]
    print(f"\n== {label} ==")
    print(t.loc[[y for y in [1995, 2000, 2005, 2010, 2015, 2019, 2021, 2022, 2023, 2024, 2025] if y in t.index]]
          .round(2).to_string())
    last = t.dropna().index.max()
    print("  rank of", last, "(1 = most affordable / lowest share):",
          {k: int(t[k].dropna().rank().loc[last]) for k in t.columns}, f"of {len(t[t.columns[0]].dropna())} years")

# ---------- Charts ----------
plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.3, "font.size": 10})
colors = ["#b5541c", "#e0a458", "#8a8a8a", "#7f93b8", "#5b6c8f"]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
for (name, g), c in zip(panel.groupby("quintile", sort=False), colors):
    lw = 2.6 if name == "Lowest 20%" else 1.4
    axes[0].plot(g.year, g.essentials_pct_of_spending, color=c, lw=lw, label=name)
    axes[1].plot(g.year, g.dinner_pct_of_week_nonessential, color=c, lw=lw, label=name)
axes[0].set(title="Essentials, % of total spending", ylabel="%")
axes[1].set(title="Dinner for 10, % of a week's non-essential spending", ylabel="%")
axes[0].legend(frameon=False, fontsize=8)
fig.suptitle("By income quintile (Consumer Expenditure Survey)", fontsize=11)
fig.tight_layout(); fig.savefig(OUT / "6_by_income.png"); plt.close(fig)
