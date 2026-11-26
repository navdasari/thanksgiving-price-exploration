# Thanksgiving Dinner Price Index

The cost of a fixed Thanksgiving dinner for 10, priced every October from 1995 to 2026
using BLS average retail prices (downloaded from FRED), set against prices, wages and
household budgets. The turkey price BLS stopped publishing in 2020 is rebuilt with
backtested time-series and machine-learning models.

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
- **The dinner's price has kept pace with inflation, not beaten it.** It costs $61.31 in
  2026, up 31% from 2019, the same as prices overall (+31%) and a little less than
  groceries (+33%). In 2026 dollars it is back at its 2019 level, 6th-cheapest of 32 years.
  It fell $1.30 from 2025, mostly because eggs and butter got cheaper.
- **After essentials, the dinner takes a bigger bite than in 2019 for every income
  fifth.** For the lowest fifth it costs 19.3% of a week's non-essential spending, vs
  18.0% in 2019; for the second fifth, 13.4% vs 11.7%. Against total income it looks
  cheaper, because incomes grew; what is left after essentials did not keep up.
- **Minimum-wage workers have lost ground.** The federal minimum has been $7.25 since July
  2009 and now buys 64% of what it did then. The dinner takes 8.5 hours of minimum-wage
  work in 2026, vs 6.4 in 2019, the 3rd-highest in 32 years. Workers at the 10th
  percentile of full-time pay did better: wages outpaced prices since 2021 (+30.5% vs
  +28.5%), and the dinner takes 9.7% of their weekly pay vs 10.1% in 2019.
- **Not visible in annual averages:** in November 2025 the government shutdown delayed or
  cut SNAP benefits for millions of households in the weeks before Thanksgiving.

## Running it

    pip install -r requirements.txt
    python run_all.py

`run_all.py` runs the scripts in order (turkey model, then the index, then the analyses)
and saves each console report to `output/`. A full run takes under a minute and gives
identical results each time. Charts share one style from `chart_style.py` (uses the Inter
font if installed, otherwise system fonts).

| Script | What it does | Main outputs |
|---|---|---|
| `turkey_model.py` | Rebuilds the retail turkey price after Feb 2020 | `turkey_reconstruction.csv`, `turkey_model_metrics.csv`, charts 9-10 |
| `build_index.py` | Prices the dinner each October, index numbers, item contributions | `index_summary.csv`, `item_costs.csv`, charts 1-3 |
| `affordability.py` | Dinner vs national wages and income | `affordability.csv` |
| `by_income.py` | Dinner and essentials by income fifth and by half | `by_income.csv`, `essentials_by_half.csv`, charts 4 and 6 |
| `deep_dive.py` | 14 household groups, low-wage workers, robustness checks | `deep_dive_*.csv`, charts 7-8 |

## Rebuilding the turkey price (`turkey_model.py`)
Turkey is over half the basket's cost, and BLS stopped publishing its average retail price
(whole frozen turkey, per lb) after February 2020. The script estimates it for March 2020
to October 2026 from series that are still published, and tests that approach first.

- **Predictors** (monthly, adjusted for grocery inflation): wholesale turkey prices
  (producer price indexes for processed and live turkeys, with 3-, 6- and 12-month
  averages and a 12-month lag, because shelf prices follow wholesale slowly), retail
  chicken, retail eggs (a bird-flu signal), corn and soybean meal (feed), and calendar
  month (holiday discounting).
- **Models:** chicken ratio, wholesale ratio, linear regression, elastic net, gradient
  boosting, regression with AR(1) errors, and an equal-weight combination of all six.
- **Backtests that mimic the real gap:** train through Feb 2004, 2007, 2010 or 2013,
  then predict up to 80 months ahead from predictors only, and score against the actual
  BLS prices.
- **Results:** the combination is best on both measures (8.5% error across all months,
  8.3% in Octobers). Diebold-Mariano tests show it beats the chicken ratio (p = 0.016)
  and regression with AR(1) errors (p = 0.038); no single model beats it. The combination
  is the main estimate, with an 80% band from the backtest errors at each horizon.
  (A first version picked the single best model by October error; that edge was within
  noise, so the combination was added. It also wins under the original rule.)
- **Independent check:** the model never sees Farm Bureau data, yet its turkey price
  changes since 2019 match the Farm Bureau's for 2021-2023 (e.g. +38% vs +39% in 2022).
  They split in 2025-26: wholesale turkey jumped with bird flu and the model passes that
  through to shelf prices (+33% and +35% vs 2019), while the Farm Bureau's holiday sale
  prices stayed low (+3% and +14%). The basket uses regular October shelf prices for every
  item, so the model is the consistent choice; the Farm Bureau version is kept as a
  comparison.

## Comparing with other prices vs. with income
Comparing the dinner's price with overall prices (CPI) shows whether it rose faster or
slower than everything else. It is not circular: removing food from CPI changes the result
by under a percentage point. But it does not measure affordability, because other prices
rising faster (rent, insurance) is itself the squeeze. Affordability is measured against
income: hours of work, share of income, and income left after essentials.

## Data notes
- **Turkey:** model estimate from March 2020 (see above). Two comparison versions are in
  `index_summary.csv`: the Farm Bureau holiday turkey price and a chicken ratio.
- **October 2013 (turkey) and October 2025 (all items):** not published because of
  government shutdowns; the Sep/Nov average is used.
- **Butter, 2012-2018:** no BLS price exists; the gap is filled with the dairy CPI.
- Raw FRED downloads are in `data/`.

## Affordability (`affordability.py`)
Compares the dinner's cost with national income measures: hours of work at the average
hourly wage of production and nonsupervisory workers, share of a week's median household
income, and per-guest cost as a share of a day's disposable and "discretionary" income per
person (disposable income minus housing and utilities, food at home, health care, and
gasoline and other energy goods; BEA, Q3 of each year).

Finding: against average wages and per-person income, 2026 is the most affordable year
since 1995 (1.87 hours of work vs 1.96 in 2019), because incomes grew faster than prices.
Against median household income it is not: 3.7% of a week's income in 2025 vs 3.5% in
2019. In these national accounts, essentials stay at about 40-41% of disposable income,
but that total includes health care paid by employers and government; the household
results below show the squeeze in what households pay themselves.

## By income quintile (`by_income.py`)
Uses the BLS Consumer Expenditure Survey by quintile of pre-tax income (annual, 1995-2025).
Total spending is the budget measure, because the lowest quintile reports spending about
twice its after-tax income. Essentials = shelter, utilities, food at home and health care
(gasoline is left out: FRED's quintile series is broken from 2023).

Findings:
- **Bottom vs top half (chart 4).** Housing (rent or mortgage, property costs, utilities),
  health care and groceries take about 62% of the bottom half's before-tax income in 2025,
  vs 25% for the top half. As a share of *income*, neither has risen much: the bottom
  half was at 64% in 2019 and peaked at 66% in 2022. The bottom half reports spending
  about 120% of its income, so its shares are approximate, and the 2004 drop reflects
  a change in how the survey measures income. (Bottom half = lowest two fifths plus half
  of the middle fifth.)
- Essentials take a near-record share of household *spending* in every quintile (2025:
  55% for the lowest 20%, 53% for the second, 47% for the middle). Incomes in the survey
  kept up with essential costs, but households are devoting more of what they spend to
  essentials, leaving less for everything else.
- After essentials, the dinner takes more of what is left than in 2019 for every
  quintile. As a share of total spending it is near its low for the lowest fifth.
- The gap between groups is large: for the lowest 20%, the dinner for 10 costs about 19%
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
- **The turkey estimate.** Dinner measures are rerun with all three turkey versions. The
  minimum-wage result holds in all of them (3rd- or 4th-most hours in 32 years). The
  lowest fifth's dinner-to-income share is lowest on record with the model or Farm Bureau
  turkey, and 4th-lowest with the chicken ratio.

Limitations: group averages still hide variation within groups; the survey misses people
without stable housing; gasoline is left out of essentials; everyone is assumed to pay
national average prices; and the lowest fifth reports spending more than its income, so
its income-based measures are rough.

Financial-stress context: the personal saving rate is 4.1% (Oct 2026) vs 7.3% in 2019;
credit card delinquency is 2.85%, above 2019 (2.58%) but below its 1995-2019 average (3.86%).
