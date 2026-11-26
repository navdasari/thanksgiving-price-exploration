# Thanksgiving Dinner Price Index

The cost of a fixed Thanksgiving dinner for 10, priced every October from 1995 to 2026
using BLS average retail prices (downloaded from FRED), compared with the American Farm
Bureau's annual survey and with CPI.

## Summary
- **The cost-of-living squeeze is real, and it falls hardest at the bottom.** Comparing
  2017-19 with 2023-25 averages, essentials (housing, utilities, groceries, health care,
  child care and other household services, vehicle insurance) rose as a share of spending
  for every household group: +3.7 points for the lowest income fifth and +4.0 for the
  second, vs +0.7 for the top fifth. For renters, under-35s and the middle three income
  fifths, 2025 is the highest share since at least 1995.
- **The poorest households gained nothing.** Before-tax income left after essentials is
  flat at about -$5,000 a year for the lowest fifth (in 2025 dollars), while the top
  fifth gained about $14,500. Households aged 65-74 lost about $2,100.
- **Minimum-wage workers have lost ground.** The federal minimum has been $7.25 since July
  2009 and now buys 64% of what it did then. The dinner takes 7.7 hours of minimum-wage
  work in 2026, vs 6.4 in 2019, the 4th-highest in 32 years (3rd-highest if turkey is
  estimated from chicken prices).
- **Thanksgiving dinner itself is not the driver.** The dinner costs 20% more than in
  2019, less than the 31% rise in prices overall, because essentials like rent rose
  faster. That comparison says the dinner rose less than other prices, not that it is
  cheap. Measured against income, it is at or near its most affordable since 1995 for
  almost every group, including the lowest fifth, mainly because turkey is cheaper than
  in 2022-24. Workers at the 10th percentile of
  full-time pay have seen wages outpace prices since 2021 (+30.5% vs +28.5%).
- **Not visible in annual averages:** in November 2025 the government shutdown delayed or
  cut SNAP benefits for millions of households in the weeks before Thanksgiving.

Run it with:

    pip install pandas numpy matplotlib
    python build_index.py
    python affordability.py   # run after build_index.py
    python by_income.py       # run after build_index.py
    python deep_dive.py       # run after build_index.py

Charts share one style, defined in `chart_style.py` (uses the Inter font if installed,
otherwise falls back to system fonts).

Outputs go to `output/`: summary tables (CSV), three charts, and a text report.

## Comparing with other prices vs. with income
Comparing the dinner's price with overall prices (CPI) shows whether it rose faster or
slower than everything else. It is not circular: removing food from CPI changes the result
by under a percentage point. But it does not measure affordability, because other prices
rising faster (rent, insurance) is itself the squeeze. Affordability is measured against
income: hours of work, share of income, and income left after essentials.

## Data notes
- **Turkey:** BLS stopped publishing whole frozen turkey prices in Feb 2020. From 2020 on,
  the 2019 BLS price is carried forward with the Farm Bureau's year-to-year turkey price
  changes. A version using whole-chicken prices instead is kept for comparison.
- **October 2013 (turkey) and October 2025 (all items):** not published because of
  government shutdowns; the Sep/Nov average is used.
- **Butter, 2012–2018:** no BLS price exists; the gap is filled with the dairy CPI.
- Raw FRED downloads are in `data/`.

## Affordability (`affordability.py`)
Compares the dinner's cost with income: hours of work at the average hourly wage of
production and nonsupervisory workers, share of a week's median household income, and
per-guest cost as a share of a day's disposable and "discretionary" income per person.
Discretionary income is disposable income minus spending on housing and utilities, food at
home, health care, and gasoline and other energy goods (BEA, Q3 of each year).

Finding: by every one of these measures, 2025-26 is the most affordable Thanksgiving dinner
relative to income since 1995, even though it costs about 20% more at the register than in
2019. In these national accounts, essentials stay at about 40-41% of disposable income
since 2015, but that total includes health care paid by employers and government. The
household-level results below show essentials taking a record share of what households pay
themselves.

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

## Who is squeezed? (`deep_dive.py`)
Tests the averages behind the story across 14 household groups (income fifths, renters vs
homeowners, single parents, married couples with young or school-age children, and four
age groups), using the Consumer Expenditure Survey, 1995-2025.

Assumptions tested:
- **Definition of essentials.** Narrow (shelter, utilities, food at home, health care) vs
  broad (adds household operations, which includes child care, and vehicle insurance).
  Rankings barely change.
- **Spending vs income as the budget.** Essentials hit record shares of *spending* for
  most groups, but not of *income*, except for under-25s. Income ranks are also checked
  within 2004-2025 and 2013-2025, because the survey changed how it measures income in
  2004 and 2013.
- **Single-year noise.** Changes use 3-year averages (2017-19 vs 2023-25); small groups
  have spikes in single years (e.g. young married families in 2019).
- **The turkey estimate.** Dinner measures are rerun with turkey estimated from chicken
  prices. The low-wage conclusions hold; the "most affordable ever" result for the lowest
  income fifth weakens to 4th-most-affordable of 31 years.

Limitations: group averages still hide variation within groups; the survey misses people
without stable housing; gasoline is left out of essentials (FRED's series is broken from
2023); everyone is assumed to pay national average prices; and the lowest fifth reports
spending more than its income, so its income-based measures are rough.

Financial-stress context: the personal saving rate is 4.1% (Oct 2026) vs 7.3% in 2019;
credit card delinquency is 2.85%, above 2019 (2.58%) but below its 1995-2019 average (3.86%).
