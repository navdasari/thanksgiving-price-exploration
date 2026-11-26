# Thanksgiving Dinner Price Index

The cost of a fixed Thanksgiving dinner for 10, priced every October from 1995 to 2026
using BLS average retail prices (downloaded from FRED), compared with the American Farm
Bureau's annual survey and with CPI.

Run it with:

    pip install pandas numpy matplotlib
    python build_index.py

Outputs go to `output/`: summary tables (CSV), three charts, and a text report.

## Data notes
- **Turkey:** BLS stopped publishing whole frozen turkey prices in Feb 2020. From 2020 on,
  the 2019 BLS price is carried forward with the Farm Bureau's year-to-year turkey price
  changes. A version using whole-chicken prices instead is kept for comparison.
- **October 2025:** not published (government shutdown); the Sep/Nov average is used.
- **Butter, 2012–2018:** no BLS price exists; the gap is filled with the dairy CPI.
- Raw FRED downloads are in `data/`.
