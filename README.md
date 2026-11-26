# Thanksgiving Dinner Price Index

The cost of a fixed Thanksgiving dinner for 10, priced every October from 1995 to 2026
using BLS average retail prices (downloaded from FRED), compared with the American Farm
Bureau's annual survey and with CPI.

Run it with:

    pip install pandas numpy matplotlib
    python build_index.py
    python affordability.py   # run after build_index.py

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
