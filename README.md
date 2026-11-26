# Thanksgiving Dinner Price Index

The cost of a fixed Thanksgiving dinner for 10, priced every October from 1995 to 2026
using BLS average retail prices (downloaded from FRED), compared with the American Farm
Bureau's annual survey and with CPI.

Run it with:

    pip install pandas numpy matplotlib
    python build_index.py
    python affordability.py   # run after build_index.py
    python by_income.py       # run after build_index.py

Outputs go to `output/`: summary tables (CSV), three charts, and a text report.

## Data notes
- **Turkey:** BLS stopped publishing whole frozen turkey prices in Feb 2020. From 2020 on,
  the 2019 BLS price is carried forward with the Farm Bureau's year-to-year turkey price
  changes. A version using whole-chicken prices instead is kept for comparison.
- **October 2025:** not published (government shutdown); the Sep/Nov average is used.
- **Butter, 2012–2018:** no BLS price exists; the gap is filled with the dairy CPI.
- Raw FRED downloads are in `data/`.

## Affordability (`affordability.py`)
Compares the dinner's cost with income: hours of work at the average hourly wage of
production and nonsupervisory workers, share of a week's median household income, and
per-guest cost as a share of a day's disposable and "discretionary" income per person.
Discretionary income is disposable income minus spending on housing and utilities, food at
home, health care, and gasoline and other energy goods (BEA, Q3 of each year).

Finding: by every one of these measures, 2025-26 is the most affordable Thanksgiving dinner
since 1995, even though it costs about 20% more at the register than in 2019. Spending on
those essentials has stayed at about 40-41% of disposable income since 2015.

## By income quintile (`by_income.py`)
Uses the BLS Consumer Expenditure Survey by quintile of pre-tax income (annual, 1995-2025).
Total spending is the budget measure, because the lowest quintile reports spending about
twice its after-tax income. Essentials = shelter, utilities, food at home and health care
(gasoline is left out: FRED's quintile series is broken from 2023).

Findings:
- Essentials take a near-record share of household spending in every quintile (2025:
  55% for the lowest 20%, 53% for the second, 47% for the middle). This squeeze does not
  show up in the national-accounts version in `affordability.py`, which counts health
  care paid by employers and government.
- The dinner itself still takes a smaller share of a week's spending than in any year
  since 1995, for every quintile, mainly because turkey was cheap in 2025.
- The gap between groups is large: for the lowest 20%, the dinner for 10 costs about 17%
  of a week's non-essential spending, compared with about 3% for the highest 20%.
