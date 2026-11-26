# Thanksgiving Dinner Price Exploration

Estimating the cost of a full Thanksgiving dinner for 10, priced every October from 1995 to 2026 with
BLS average retail prices (via FRED) and compared with prices, wages and household budgets.
The menu builds on the American Farm Bureau Federation's: turkey, potatoes, sweet potatoes,
stuffing, rolls, cranberries, peas, green beans, a veggie tray, pumpkin pie with whipped
cream, apple cider, milk and baking staples. The turkey price BLS stopped publishing in 2020
is rebuilt with back-tested time-series and machine learning models. Full methods and
limitations are in the [technical appendix](docs/technical_appendix.pdf).

## Summary
- **The cost-of-living squeeze hits the bottom hardest.** From 2017-19 to 2023-25,
  essentials (housing, utilities, groceries, health care, child care, vehicle insurance)
  rose as a share of spending for every group: +3.7 points for the lowest income fifth,
  +4.0 for the second, +0.7 for the top. For renters, under-35s and the middle three
  fifths, 2025 is the highest share since 1995.
- **The poorest gained nothing.** Income left after essentials stayed at about -$5,000 a
  year for the lowest fifth (2025 dollars); the top fifth gained about $14,500.
- **In New York City the dinner costs $168 (chart 1).** With 11 of 18 items priced from the
  New York Post's survey of NYC supermarkets, the dinner is $167.77 in 2026, about 1.9 times
  the U.S. average, up from $141.28 in 2025. That 19% jump comes from the Post's store
  prices (milk +50%, cider +75%, pumpkin +43%, turkey +18%), which rose much faster than
  BLS indexes for the same items.
- **Nationally it costs $87, up in step with inflation.** $87.39 in 2026 ($8.74 a person),
  up 31% from 2019, the same as overall prices (+31%) and a little less than groceries
  (+33%). It rose $0.18 from 2025: turkey +$0.49, eggs and butter -$1.42.
- **After essentials, the dinner takes a bigger bite for every income fifth.** Lowest fifth:
  26.9% of a week's non-essential spending (25.7% in 2019); second: 18.6% (16.7%); top: 4.5%
  (4.4%).
- **Minimum-wage workers lost ground (chart 7).** The federal $7.25, unchanged since 2009,
  buys 64% of what it did. The dinner takes 12.1 hours of work, vs 9.2 in 2019, the most in
  32 years.
- **Not in annual data:** the November 2025 shutdown delayed or cut SNAP benefits for
  millions of households just before Thanksgiving.

## Running it

    pip install -r requirements.txt
    python run_all.py

`run_all.py` runs everything in under a minute, reproducibly, saving reports to `output/`.
Charts use a FiveThirtyEight-style theme (`chart_style.py`); fonts are bundled in `fonts/`
(Inter, SIL OFL; JetBrains Mono, Apache 2.0).

| Script | What it does | Main outputs |
|---|---|---|
| `turkey_price_ml_modeling.py` | Nowcasts the discontinued turkey price (backtested ML/time-series ensemble) | `turkey_price_nowcast.csv`, `turkey_price_model_metrics.csv`, charts 8-9 |
| `build_index.py` | Prices the dinner each year (U.S. and NYC), index numbers, item contributions | `index_summary.csv`, `item_costs.csv`, `item_costs_nyc.csv`, `nyc_item_sources.csv`, charts 1-3 |
| `affordability.py` | Dinner vs national wages and income | `affordability.csv` |
| `by_income.py` | Dinner and essentials by income fifth and half | `by_income.csv`, `essentials_by_half.csv`, `week_of_spending.csv`, charts 4-5 |
| `deep_dive.py` | 14 household groups, minimum wage, robustness checks | `deep_dive_*.csv`, charts 6-7 |

## Charts at a glance
Each chart is labeled NYC or National above its headline.

| Chart | Geography | Dinner prices from |
|---|---|---|
| 1 Dinner cost | NYC, with U.S. average for comparison | New York Post NYC survey + BLS |
| 2 Price indexes | National | BLS U.S. averages |
| 3 Item contributions | National | BLS U.S. averages |
| 4 Essentials, bottom vs top half | National | (household spending, no dinner) |
| 5 A week of spending by income fifth | National | BLS U.S. averages |
| 6 Household types | National | (household spending, no dinner) |
| 7 Hours at the minimum wage | National | BLS U.S. averages; federal minimum wage |
| 8-9 Turkey price model | National | BLS U.S. turkey price |

## Nowcasting the turkey price (`turkey_price_ml_modeling.py`)
Turkey is the largest item (about 39% of the cost), and BLS stopped publishing its retail
price (whole frozen, per lb) after February 2020. The script estimates March 2020 to
October 2026 from series still published, after testing the approach.

- **Predictors** (monthly, adjusted for grocery inflation): wholesale turkey prices (with
  3-, 6- and 12-month averages and a 12-month lag, since shelf prices follow wholesale
  slowly), retail chicken, eggs (a bird-flu signal), corn and soybean meal, and month.
- **Models:** chicken ratio, wholesale ratio, linear regression, elastic net, gradient
  boosting, regression with AR(1) errors, and an equal-weight combination of all six.
- **Backtests that mimic the real gap:** train through Feb 2004, 2007, 2010 or 2013, then
  predict up to 80 months ahead from predictors only and score against actual BLS prices.
- **Results:** the combination is best (8.5% error across months, 8.3% in Octobers).
  Diebold-Mariano tests show it beats the chicken ratio (p = 0.016) and AR(1) errors
  (p = 0.038); no model beats it. It is the main estimate, with an 80% band from backtest
  errors. (It was added after a single-model pick proved to be noise; it also wins under
  the original rule.)
- **Independent check:** without seeing Farm Bureau data, the model matches its turkey
  price changes for 2021-23 (+38% vs +39% in 2022). In 2025-26 the model passes the bird-flu
  wholesale jump through to shelf prices (+33% and +35% vs 2019) while the Farm Bureau's
  holiday sale prices stayed low (+3% and +14%); the basket uses regular shelf prices.

## Comparing with prices vs. with income
Comparing the dinner with CPI shows whether it rose faster than other prices. It is not
circular (dropping food from CPI changes the result by under a point), but it is not
affordability: other prices rising faster is itself the squeeze. Affordability is measured
against income.

## Data notes
- **Prices:** BLS October average prices for turkey (until 2020), russet potatoes, milk,
  butter, eggs, flour and sugar. Items BLS does not price start from the Farm Bureau's 2026
  survey price and move back with the closest CPI group on FRED (bakery, fruits and
  vegetables, or dairy), which misses item-specific swings. Green beans use the frozen-pea
  price (the Farm Bureau does not publish one). Apple cider (1 gallon) starts at $6.99, the
  median of November 2026 grocery listings (Costco $6.99 and $5.51, Meijer $7.49, Price
  Chopper $6.99), and moves with the nonalcoholic beverages CPI.
- **NYC prices (chart 1):** 11 items use the New York Post's November 2025 and 2026 prices
  from six NYC supermarkets (`data/nyc_post_prices.csv`; totals $160.30 and $184.43), scaled
  to this menu: turkey (Bell & Evans, $3.99/lb, x 16 lb), yams (x 3 lb), Stove Top (x 14/6),
  crescent rolls (x 1.5), cranberry sauce, baby carrots, Libby's pumpkin (x 2), cider (x 2),
  milk (x 2), butter and flour (x 1/5). 2026 uses the Post's 2026 prices; earlier years move
  back from 2025 with each item's BLS price history or CPI group. The other 7 items are
  national prices x an NYC factor (BEA's New York metro goods price parity, 110.3 in 2024,
  moved with the New York vs U.S. grocery CPI). `nyc_item_sources.csv` shows the Post's
  one-year changes are far larger than BLS indexes (milk +50% vs +1%), so treat the 2025-26
  jump with care.
- **Why the full menu:** a nine-item basket ($61 in 2026) and the Farm Bureau's classic
  menu ($58.63) are spare; the full menu ($87) is closer to a real Thanksgiving but still
  omits alcohol, appetizers and non-food items.
- **Turkey comparisons:** `index_summary.csv` also has the basket with the Farm Bureau's
  holiday turkey price and with a chicken-ratio turkey.
- **Gaps:** October 2013 (turkey) and October 2025 (all items) were not published because of
  shutdowns; the Sep/Nov average is used. Butter has no BLS price for 2012-18; the dairy CPI
  fills the gap. Raw FRED downloads are in `data/`.

## Affordability (`affordability.py`)
Compares the dinner with national income: hours of work at the average wage of production
and nonsupervisory workers, share of a week's median household income, and per-guest cost
as a share of a day's disposable and "discretionary" income per person (disposable income
minus housing, utilities, groceries, health care and energy; BEA, Q3).

Against average wages and per-person income, 2026 is the most affordable year since 1995
(2.7 hours of work vs 2.8 in 2019); against median household income it is not (5.2% of a
week's income in 2025 vs 5.1% in 2019). National essentials stay at 40-41% of disposable
income, but that counts employer- and government-paid health care; household data below
shows the squeeze.

## By income quintile (`by_income.py`)
BLS Consumer Expenditure Survey by pre-tax income quintile, 1995-2025. Total spending is
the budget, since the lowest quintile reports spending about twice its after-tax income.
Essentials = shelter, utilities, food at home and health care (gasoline excluded; its
quintile series is broken from 2023).

- **A week of spending (chart 5).** In 2025 the lowest fifth spends about $730 a week: $405
  on essentials, leaving $325, of which the $87 dinner takes 27%. The dinner is 12.0% of
  that week vs 2.8% of the top fifth's ($3,068). Since 1995 (in 2025 dollars) the lowest
  fifth's week grew from $594 to $730, and $99 of the $136 went to essentials.
- **Bottom vs top half (chart 4).** Housing, health care and groceries take about 62% of the
  bottom half's pre-tax income in 2025 vs 25% for the top half. As a share of income neither
  has risen much (bottom half: 64% in 2019, 66% peak in 2022). The bottom half reports
  spending about 120% of its income, so its shares are approximate; the 2004 drop reflects a
  change in income measurement. (Bottom half = lowest two fifths plus half the middle.)
- Essentials take a near-record share of *spending* in every quintile (2025: 55% lowest,
  53% second, 47% middle), even though incomes kept up.
- After essentials, the dinner takes more of what is left than in 2019 for every quintile.

## Who is squeezed? (`deep_dive.py`)
Tests the averages across 14 household groups (income fifths, renters, homeowners, single
parents, married couples with young or school-age children, four age groups).

- **Definition of essentials:** adding household operations (incl. child care) and vehicle
  insurance barely changes rankings.
- **Spending vs income:** essentials hit record shares of spending for most groups, but not
  of income (except under-25s). Income ranks are also checked within 2004-2025 and
  2013-2025, after survey changes in how income is measured.
- **Single-year noise:** changes use 3-year averages (2017-19 vs 2023-25).
- **Turkey estimate:** with all three turkey versions, the minimum-wage result holds (1st-
  to 4th-most hours in 32 years) and the lowest fifth's dinner-to-income share is the
  lowest on record.

Limitations: averages hide variation within groups; the survey misses people without stable
housing; everyone pays national average prices; the lowest fifth's income is under-reported. Context: the saving rate is 4.1% (Oct 2026) vs 7.3%
in 2019; credit card delinquency is 2.85%, above 2019 (2.58%) but below its 1995-2019
average (3.86%).
