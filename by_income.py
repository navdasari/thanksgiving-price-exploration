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
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

# ---------- Chart 5: one week of spending, with Thanksgiving dinner carved out ----------
# Each bar is a typical week (annual spending / 52), drawn to scale in dollars and split
# into essentials, the dinner for 10, and everything else (essentials + non-essential = total).
ESS_C, DIN_C, OTH_C = "#A8927C", cs.RED, "#E6DAC4"
cpi = pd.read_csv(ROOT / "data" / "CPIAUCSL.csv", parse_dates=["observation_date"], na_values=".")
cpi = cpi.set_index("observation_date").iloc[:, 0].dropna().groupby(lambda d: d.year).mean()
LATEST = int(panel.year.max())
week = panel.assign(week_total=panel.total_spending / 52, week_ess=panel.essentials / 52)
week["week_other"] = week.week_total - week.week_ess - week.dinner_cost
week["dinner_pct_of_week"] = 100 * week.dinner_cost / week.week_total
week["dinner_pct_of_nonessential"] = 100 * week.dinner_cost / (week.week_total - week.week_ess)
week.round(3).to_csv(OUT / "week_of_spending.csv", index=False)

fig, axes = cs.figure(1, 2, width=13, height=6.9, gridspec_kw={"width_ratios": [1.7, 1]})
fig.subplots_adjust(left=0.1, right=0.97, wspace=0.32, top=0.72)


def week_bars(ax, rows, labels, scale=1.0):
    ys = list(range(len(rows)))[::-1]
    for y, (_, r) in zip(ys, rows.iterrows()):
        e, d, o = r.week_ess * scale, r.dinner_cost * scale, r.week_other * scale
        ax.barh(y, e, color=ESS_C, height=0.62, edgecolor=cs.BG, lw=1)
        ax.barh(y, d, left=e, color=DIN_C, height=0.62, edgecolor=cs.BG, lw=1)
        ax.barh(y, o, left=e + d, color=OTH_C, height=0.62, edgecolor=cs.BG, lw=1)
        ax.text(e / 2, y, f"${e:,.0f}", color="white", ha="center", va="center", fontsize=9.5, fontweight="semibold")
        ax.text(e + d + o + 25, y + 0.12, f"${e + d + o:,.0f} a week", color=cs.TEXT, va="center",
                fontsize=10, fontweight="semibold")
        ax.text(e + d + o + 25, y - 0.17, f"dinner = {r.dinner_pct_of_week:.1f}%", color=DIN_C, va="center",
                fontsize=9.5, fontweight="semibold")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.axvline(0, color="#B9A68E", lw=1.2)


now = week[week.year == LATEST].set_index("quintile").loc[list(QUINTILES.values())]
week_bars(axes[0], now, list(now.index))
axes[0].set_xlim(0, now.week_total.max() * 1.22)
axes[0].set_title(f"A typical week in {LATEST}, by income fifth")

YEARS = [1995, 2007, 2019, LATEST]
low = week[(week.quintile == "Lowest 20%") & (week.year.isin(YEARS))].set_index("year").loc[YEARS]
real = low.copy()
for c in ["week_ess", "dinner_cost", "week_other", "week_total"]:
    real[c] = low[c] * cpi[LATEST] / cpi.reindex(low.index)
week_bars(axes[1], real, [str(y) for y in YEARS])
axes[1].set_xlim(0, real.week_total.max() * 1.45)
axes[1].set_title(f"Lowest fifth over time ({LATEST} dollars)")

fig.legend(handles=[Patch(color=ESS_C, label="Essentials (shelter, utilities, groceries, health care)"),
                    Patch(color=DIN_C, label="Thanksgiving dinner for 10"),
                    Patch(color=OTH_C, label="Everything else")],
           loc="upper left", bbox_to_anchor=(0.1, 0.83), ncol=3, handlelength=1.2, columnspacing=1.8)
d = now.loc["Lowest 20%"]
cs.finish(fig, f"For the poorest fifth, Thanksgiving dinner takes {d.dinner_pct_of_nonessential:.0f}% of what's left after essentials",
          f"A week of household spending, to scale. The same ${d.dinner_cost:.0f} dinner is {d.dinner_pct_of_week:.1f}% of the lowest fifth's week "
          f"and {now.loc['Highest 20%'].dinner_pct_of_week:.1f}% of the top fifth's.",
          "BLS Consumer Expenditure Survey and average prices via FRED", OUT / "5_week_of_spending.png",
          note="Weekly spending = annual spending / 52. Households in the lowest fifth average about 1.5 people, so a dinner for 10 is a hosting cost.")

# ---------- Chart 4: essentials as a share of income, bottom vs top half ----------
# Bottom 50% = lowest two fifths + half of the middle fifth; top 50% = the rest.
# Shares are aggregate: total spending on each category / total before-tax income.
HALVES = {"Bottom 50%": {"02": 1, "03": 1, "04": 0.5}, "Top 50%": {"04": 0.5, "05": 1, "06": 1}}
CATS = {"Housing": (["SHELTER", "UTILS"], cs.BLUE),
        "Health care": (["HEALTH"], cs.RED),
        "Groceries": (["FOODHOME"], cs.GOLD)}
halves = {}
for half, w in HALVES.items():
    inc = sum(load("INCBFTAX", q) * k for q, k in w.items())
    halves[half] = pd.DataFrame({c: 100 * sum(load(x, q) * k for x in xs for q, k in w.items()) / inc
                                 for c, (xs, _) in CATS.items()}).loc[1995:]
pd.concat(halves, axis=1).round(2).to_csv(OUT / "essentials_by_half.csv")
print("\n== Essentials as % of before-tax income, bottom vs top half ==")
for half, d in halves.items():
    t = d.sum(axis=1)
    print(f"{half}: 1995 {t[1995]:.1f}%, 2019 {t[2019]:.1f}%, 2022 {t[2022]:.1f}%, 2025 {t[2025]:.1f}% "
          f"(2025 rank, 1 = highest: {int(t.rank(ascending=False)[2025])}/{len(t)})")

fig, axes = cs.figure(1, 2, width=12, height=6.4, sharey=True)
for ax, (half, d) in zip(axes, halves.items()):
    ax.stackplot(d.index, *[d[c] for c in CATS], colors=[c for _, c in CATS.values()], alpha=1, lw=0, zorder=2)
    total = d.sum(axis=1)
    ax.plot(total.index, total, color=cs.TEXT, lw=1.2)
    ax.set_title(f"{half} of households by income")
    ax.set_ylim(0, 78); ax.set_xlim(1995, 2025)
    cs.baseline(ax, 0)
    ax.annotate(f"{total[2025]:.0f}%", (2025, total[2025]), xytext=(2025.3, total[2025]),
                fontsize=11, fontweight="semibold", color=cs.TEXT, va="center", annotation_clip=False)
# label the bands once, on the left panel, at their 2010 midpoints
d = halves["Bottom 50%"]; base = 0
for c, (_, col) in CATS.items():
    mid = base + d.loc[2010, c] / 2; base += d.loc[2010, c]
    axes[0].text(2010, mid, c, color="white", fontsize=10, fontweight="semibold", ha="center", va="center")
axes[0].annotate("2004: survey starts\nestimating missing income", (2004, halves["Bottom 50%"].sum(axis=1)[2004]),
                 xytext=(2000.5, 71), fontsize=8.5, color=cs.MUTED, ha="center",
                 arrowprops=dict(arrowstyle="-", color=cs.MUTED, lw=0.8))
for ax in axes:
    cs.unit_on_top(ax, suffix="%")
fig.subplots_adjust(right=0.95, wspace=0.12)
cs.finish(fig, "The bottom half spends about 62% of its income on essentials; the top half, 25%",
          "Housing (rent or mortgage, property costs, utilities), health care and groceries, % of before-tax income, 1995-2025",
          "BLS Consumer Expenditure Survey via FRED", OUT / "4_essentials_by_half.png",
          note="The bottom half reports spending about 120% of its income (under-reported income, benefits, retirees using savings), so its shares are approximate.")
