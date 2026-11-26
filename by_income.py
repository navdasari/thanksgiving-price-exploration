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
import chart_style as cs

colors = {"Lowest 20%": cs.RED, "Second 20%": cs.GOLD, "Middle 20%": cs.GRAY,
          "Fourth 20%": cs.GREEN, "Highest 20%": cs.BLUE}
fig, axes = cs.figure(1, 2, width=12, height=6.4)
offsets_l = {"Lowest 20%": 1.5, "Second 20%": -0.8}
for name, g in panel.groupby("quintile", sort=False):
    c = colors[name]
    axes[0].plot(g.year, g.essentials_pct_of_spending, color=c, lw=3 if name == "Lowest 20%" else 2.2)
    axes[1].plot(g.year, g.dinner_pct_of_week_nonessential, color=c, lw=3 if name == "Lowest 20%" else 2.2)
    last = g.iloc[-1]
    cs.label_end(axes[1], last.year, last.dinner_pct_of_week_nonessential, name, c, dx=0.6, size=9.5,
                 dy={"Fourth 20%": 0.4, "Highest 20%": -0.6}.get(name, 0))
axes[0].set_title("Essentials, % of total spending")
axes[1].set_title("Dinner for 10, % of a week's non-essential spending")
axes[0].set_ylim(30, 65); cs.baseline(axes[0], 30)
axes[1].set_ylim(0, 27); cs.baseline(axes[1], 0)
cs.unit_on_top(axes[0], suffix="%"); cs.unit_on_top(axes[1], suffix="%")
fig.subplots_adjust(right=0.87)
cs.finish(fig, "Essentials take more of every budget, leaving less room for the dinner",
          "By income fifth, 1995-2025. Essentials: shelter, utilities, groceries, health care.",
          "BLS Consumer Expenditure Survey via FRED", OUT / "6_by_income.png")
