# Thanksgiving Dinner Price Index

The cost of a full Thanksgiving dinner for 10, priced every October from 1995 to 2026
using BLS average retail prices (downloaded from FRED), set against prices, wages and
household budgets. The menu builds on the American Farm Bureau Federation's
Thanksgiving menus: turkey, potatoes, sweet potatoes, stuffing, rolls, cranberries, peas,
green beans, a veggie tray, pumpkin pie with whipped cream, apple cider, milk and baking
staples. The turkey price BLS stopped publishing in 2020 is rebuilt with
backtested time-series and machine-learning models.

## Summary
- **The cost-of-living squeeze is real and hits the bottom hardest.** From 2017-19 to
  2023-25, essentials (housing, utilities, groceries, health care, child care, vehicle
  insurance) rose as a share of spending for every household group: +3.7 points for the
  lowest income fifth and +4.0 for the second, vs +0.7 for the top. For renters, under-35s
  and the middle three fifths, 2025 is the highest share since at least 1995.
- **The poorest gained nothing.** Before-tax income left after essentials stayed at about
  -$5,000 a year for the lowest fifth (2025 dollars); the top fifth gained about $14,500.
- **In New York City the dinner costs $168 (charts 1 and 3).** Pricing 11 of the 18 items
  from the New York Post's survey of NYC supermarkets puts the dinner for 10 at $167.77 in
  2026, about 1.9 times the U.S. average. It was $141.28 in 2025; the 19% one-year jump
  comes from the Post's store prices (milk +50%, cider +75%, pumpkin +43%, turkey +18%),
  which rose much faster than BLS price indexes for the same items.
- **Nationally the dinner costs $87 and rose in step with inflation.** The full dinner for 10 is
  $87.39 in 2026 (about $8.74 a person), up 31% from 2019, the same as overall prices
  (+31%) and a little less than groceries (+33%). It rose $0.18 from 2025: turkey added
  $0.49 while cheaper eggs and butter took off $1.42.
- **After essentials, the dinner takes a bigger bite for every income fifth.** For the
  lowest fifth it is 26.9% of a week's non-essential spending, vs 25.7% in 2019; for the
  second, 18.6% vs 16.7%; for the top fifth, 4.5% vs 4.4%.
- **In NYC the dinner takes 9.9 hours of minimum-wage work (chart 7).** At New York City's
  $17 minimum (employers with 11+ workers), the NYC-priced dinner takes 9.9 hours in 2026,
  up from 7.3 in 2019 and 8.6 in 2025, but below the 12-16 hours of the years before the
  city's raises began in 2017. At the federal $7.25, unchanged since 2009, the U.S.-priced
  dinner takes 12.1 hours, the most in 32 years.
- **Not in annual data:** the November 2025 shutdown delayed or cut SNAP benefits for
  millions of households just before Thanksgiving.

## Running it

    pip install -r requirements.txt
    python run_all.py

`run_all.py` runs the scripts in order (turkey model, then the index, then the analyses)
and saves each console report to `output/`. A full run takes under a minute and gives
identical results each time. Charts share a FiveThirtyEight-style theme from
`chart_style.py` (gray canvas, full grid, heavy baseline, dark source bar, Inter headlines
and JetBrains Mono tick labels) with an autumn Thanksgiving palette. The fonts are bundled
in `fonts/` (Inter under the SIL Open Font License, JetBrains Mono under Apache 2.0), so
charts look the same on any machine.

| Script | What it does | Main outputs |
|---|---|---|
| `turkey_price_ml_modeling.py` | Nowcasts the discontinued retail turkey price (ML and time-series ensemble, backtested) | `turkey_price_nowcast.csv`, `turkey_price_model_metrics.csv`, charts 8-9 |
| `build_index.py` | Prices the dinner each October (U.S. and NYC), index numbers, item contributions | `index_summary.csv`, `item_costs.csv`, `item_costs_nyc.csv`, `nyc_item_sources.csv`, charts 1-3 |
| `affordability.py` | Dinner vs national wages and income | `affordability.csv` |
| `by_income.py` | Dinner and essentials by income fifth and by half | `by_income.csv`, `essentials_by_half.csv`, `week_of_spending.csv`, charts 4-5 |
| `deep_dive.py` | 14 household groups, low-wage workers, robustness checks | `deep_dive_*.csv`, charts 6-7 |

## Nowcasting the turkey price: ML and time-series ensemble (`turkey_price_ml_modeling.py`)
Turkey is the basket's largest item (about 39% of its cost), and BLS stopped publishing its average retail price
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
- **Menu and prices:** items BLS prices directly use BLS October average prices (turkey
  until 2020, russet potatoes, milk, butter, eggs, flour, sugar). Items BLS does not
  price (sweet potatoes, stuffing mix, rolls, cranberries, peas, green beans, veggie tray,
  pumpkin pie mix, pie crusts, whipping cream) start from the Farm Bureau's 2026 survey
  price and move back in time with the closest CPI component on FRED: cereals and bakery,
  fruits and vegetables, or dairy. FRED only has these broad components, so this misses
  item-specific swings. The Farm Bureau does not publish its green bean price; the
  frozen-pea price is used. Apple cider (1 gallon) starts from $6.99, the median of
  November 2026 grocery listings (Costco $6.99 and $5.51, Meijer $7.49, Price Chopper
  $6.99), and moves with the CPI for nonalcoholic beverages.
- **New York City prices (charts 1 and 3):** 11 items use the New York Post's November 2025
  and 2026 prices from six NYC supermarkets (`data/nyc_post_prices.csv`, total $160.30 and
  $184.43), scaled to this menu's quantities: turkey (Bell & Evans, per lb x 16), yams (x 3
  lb), Stove Top (x 14/6 for 14 oz), crescent rolls (x 1.5 for a dozen), cranberry sauce,
  baby carrots (veggie tray), Libby's pumpkin (x 2 for 30 oz), apple cider (x 2 for a
  gallon), whole milk (x 2 for a gallon), butter and flour (x 1/5). 2026 uses the Post's
  2026 prices; earlier years start from the Post's 2025 prices and move back with the
  item's own BLS price history (turkey, milk, butter, flour) or its CPI group. The other 7
  items (russet potatoes, peas, green beans, pie crusts, whipping cream, eggs, sugar) are
  national prices x an NYC factor (BEA's 2024 Regional Price Parity for goods in the New
  York metro, 110.3, moved with the New York vs U.S. food-at-home CPI). Post items not on
  this menu (apples, mushrooms, onion, instant mashed potatoes, bakery pies, ice cream) are
  not used. `nyc_item_sources.csv` shows each item's source and compares the Post's
  2025-2026 change with the BLS index change: the Post's are far larger (e.g. milk +50% vs
  +1%), so treat the one-year jump with care. The Post's turkey is a premium brand ($3.99/lb).
  Chart 7 uses NYC's minimum wage: the higher of the federal and New York State rates
  (FRED), with NYC's 2017-2023 rates for employers with 11+ workers from NY Labor Law 652
  ($11, $13, then $15). The other affordability charts (4-6) stay on national prices and
  incomes.
- **Why the full menu:** an earlier nine-item basket came to $61 in 2026, in line with the
  Farm Bureau's $58.63 "classic" menu, but both are spare (one dozen rolls and one pound of
  peas for ten people). The full menu ($87 in 2026) is closer to what a real Thanksgiving
  costs. It still leaves out alcohol, appetizers and non-food items.
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
since 1995 (2.7 hours of work vs 2.8 in 2019), because incomes grew faster than prices.
Against median household income it is not: 5.2% of a week's income in 2025 vs 5.1% in
2019. In these national accounts, essentials stay at about 40-41% of disposable income,
but that total includes health care paid by employers and government; the household
results below show the squeeze in what households pay themselves.

## By income quintile (`by_income.py`)
Uses the BLS Consumer Expenditure Survey by quintile of pre-tax income (annual, 1995-2025).
Total spending is the budget measure, because the lowest quintile reports spending about
twice its after-tax income. Essentials = shelter, utilities, food at home and health care
(gasoline is left out: FRED's quintile series is broken from 2023).

Findings:
- **A week of spending (chart 5).** In 2025 the lowest fifth spends about $730 a week:
  $405 on essentials, leaving $325, of which the $87 dinner for 10 takes 27%. The same
  dinner is 12.0% of the lowest fifth's whole week vs 2.8% of the top fifth's ($3,068).
  Since 1995, in 2025 dollars, the lowest fifth's week grew from $594 to $730, and $99 of
  that $136 increase went to essentials.
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
  quintile. As a share of total spending it is
  near its low for the lowest fifth.
- The gap between groups is large: for the lowest 20%, the dinner for 10 costs about 27%
  of a week's non-essential spending, compared with about 5% for the highest 20%.

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
  minimum-wage result holds in all of them (1st- to 4th-most hours in 32 years). The
  lowest fifth's dinner-to-income share is the lowest on record in all three.

Limitations: group averages still hide variation within groups; the survey misses people
without stable housing; gasoline is left out of essentials; everyone is assumed to pay
national average prices; and the lowest fifth reports spending more than its income, so
its income-based measures are rough.

Financial-stress context: the personal saving rate is 4.1% (Oct 2026) vs 7.3% in 2019;
credit card delinquency is 2.85%, above 2019 (2.58%) but below its 1995-2019 average (3.86%).
