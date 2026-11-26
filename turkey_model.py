"""Rebuild the BLS retail price of whole frozen turkey after BLS stopped publishing it.

BLS series APU0000706311 ends in February 2020. This script estimates it for March 2020
through the latest month from series that are still published, and measures how well
that works before trusting it.

Target: log of the retail turkey price divided by the CPI for food at home ("real"
turkey price). Working in real terms keeps the models from having to extrapolate to
price levels they never saw in training.

Predictors (monthly, all in log real terms):
  - Producer price index, poultry processing: turkeys (PCU3116153116157): current,
    3-, 6- and 12-month averages, and the value 12 months earlier. Retail prices adjust
    to wholesale slowly, so averages and lags matter.
  - Producer price index, slaughter turkeys (WPS014201): current, 6- and 12-month averages.
  - Retail whole chicken price: current and 6-month average.
  - Retail egg price, 3-month average (a signal for avian flu outbreaks).
  - Global corn and soybean meal prices, 12-month averages (feed costs).
  - Calendar month (retailers discount turkey around Thanksgiving).

Models:
  - Chicken ratio: turkey moves one-for-one with chicken (the earlier comparison version).
  - Wholesale ratio: turkey moves one-for-one with the 12-month average wholesale price.
  - Linear regression (OLS) on all predictors.
  - Elastic net: regularized regression, penalty chosen by time-ordered cross-validation.
  - Gradient boosting: tree ensemble (scikit-learn HistGradientBoostingRegressor).
  - Regression with AR(1) errors: linear regression whose errors carry over month to month,
    estimated by maximum likelihood (statsmodels SARIMAX). In reconstruction, the last
    observed error fades out over the following months.
  - Combined: equal-weight average (in logs) of all six models above. This is the main
    estimate. Backtest errors of the individual models are statistically indistinguishable
    (Diebold-Mariano tests below), so picking a single "winner" would mostly pick noise;
    equal-weight forecast combination is the standard robust choice in that situation.

Validation mimics the real problem: fit on data through an origin month, then predict
every month for up to 80 months after it from predictors only, never seeing the target.
Origins: Feb 2004, Feb 2007, Feb 2010, Feb 2013 (test windows end by Feb 2020).
Note on model choice: the first version of this script picked the single model with the
lowest October backtest error (then the wholesale ratio, among models that excluded the
combination). Its edge was within noise and it is the most volatile model after 2020, so
the combination was added and made the main estimate after seeing those results. With it
included, the combination ranks first on both backtest metrics, so the original rule would
also select it.
Uncertainty bands come from the backtest errors at each horizon (empirical 10th-90th
percentiles), so they reflect how wrong this approach has actually been.

Outputs (in output/): turkey_reconstruction.csv, turkey_backtest_errors.csv,
turkey_model_metrics.csv, 9_turkey_backtest.png, 10_turkey_reconstruction.png.
"""
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNetCV, LinearRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "output"
OUT.mkdir(exist_ok=True)
TRAIN_START = "1993-01-01"
LAST_ACTUAL = pd.Timestamp("2020-02-01")
ORIGINS = ["2004-02-01", "2007-02-01", "2010-02-01", "2013-02-01"]
MAX_HORIZON = 80  # months; the real gap (Mar 2020 - Oct 2026) is 80 months
SEED = 0

# Farm Bureau 16-lb turkey, holiday survey (for comparison only; a different measure)
AFBF_TURKEY = {2019: 20.80, 2020: 19.39, 2021: 23.99, 2022: 28.96, 2023: 27.35,
               2024: 25.67, 2025: 21.50, 2026: 23.68}


def load(path, sid=None):
    df = pd.read_csv(path, parse_dates=["observation_date"], na_values=".")
    s = df.set_index("observation_date").iloc[:, 0].astype(float)
    return s


def fill_single_gaps(s):
    """Fill isolated missing months (e.g. shutdown Octobers) by linear interpolation in logs."""
    s = s.copy()
    full = pd.date_range(s.dropna().index.min(), s.dropna().index.max(), freq="MS")
    s = s.reindex(full)
    return np.exp(np.log(s).interpolate(limit=1, limit_area="inside"))


# ---------------- Data ----------------
raw = {
    "turkey": load(DATA / "APU0000706311.csv"),
    "food_cpi": fill_single_gaps(load(DATA / "CUUR0000SAF11.csv")),
    "ppi_proc": fill_single_gaps(load(DATA / "turkey_model" / "PCU3116153116157.csv")),
    "ppi_slaughter": fill_single_gaps(load(DATA / "turkey_model" / "WPS014201.csv")),
    "chicken": fill_single_gaps(load(DATA / "APU0000706111.csv")),
    "eggs": fill_single_gaps(load(DATA / "APU0000708111.csv")),
    "corn": fill_single_gaps(load(DATA / "turkey_model" / "PMAIZMTUSDM.csv")),
    "soymeal": fill_single_gaps(load(DATA / "turkey_model" / "PSMEAUSDM.csv")),
}
df = pd.DataFrame(raw)
# Global feed prices are published with a lag; carry the last value forward at most 2 months
for c in ["corn", "soymeal"]:
    df[c] = df[c].ffill(limit=2)
END = df[["ppi_proc", "ppi_slaughter", "chicken", "eggs", "food_cpi"]].dropna().index.max()
df = df.loc[:END]

real = np.log(df.drop(columns="food_cpi").div(df.food_cpi, axis=0))
X = pd.DataFrame(index=df.index)
X["proc"] = real.ppi_proc
for w in (3, 6, 12):
    X[f"proc_ma{w}"] = real.ppi_proc.rolling(w).mean()
X["proc_lag12"] = real.ppi_proc.shift(12)
X["slaughter"] = real.ppi_slaughter
for w in (6, 12):
    X[f"slaughter_ma{w}"] = real.ppi_slaughter.rolling(w).mean()
X["chicken"] = real.chicken
X["chicken_ma6"] = real.chicken.rolling(6).mean()
X["eggs_ma3"] = real.eggs.rolling(3).mean()
X["corn_ma12"] = real.corn.rolling(12).mean()
X["soymeal_ma12"] = real.soymeal.rolling(12).mean()
months = pd.get_dummies(X.index.month, prefix="m", drop_first=True).astype(float)
months.index = X.index
X = pd.concat([X, months], axis=1).loc[TRAIN_START:]
y = real.turkey.reindex(X.index)
assert X.loc[:END].notna().all().all(), X.columns[X.isna().any()].tolist()

AR_COLS = ["proc_ma12", "proc_ma3", "slaughter_ma6", "chicken", "eggs_ma3"] + list(months.columns)


# ---------------- Models ----------------
def ratio_model(col, window=24):
    def fit_predict(Xtr, ytr, Xte):
        offset = (ytr - Xtr[col]).iloc[-window:].mean()
        return Xte[col] + offset
    return fit_predict


def sk_model(make):
    def fit_predict(Xtr, ytr, Xte):
        m = make().fit(Xtr.values, ytr.values)
        return pd.Series(m.predict(Xte.values), index=Xte.index)
    return fit_predict


def ar_errors(Xtr, ytr, Xte):
    # The state-space model needs consecutive months; missing target months (Oct 2013)
    # stay as NaN and are handled by the Kalman filter.
    span = pd.date_range(ytr.index.min(), ytr.index.max(), freq="MS")
    yy, xx = ytr.reindex(span).values, X.loc[span, AR_COLS].values
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = SARIMAX(yy, exog=xx, order=(1, 0, 0), trend="c").fit(disp=False, maxiter=500)
        return pd.Series(np.asarray(m.forecast(steps=len(Xte), exog=Xte[AR_COLS].values)), index=Xte.index)


MODELS = {
    "Chicken ratio": ratio_model("chicken"),
    "Wholesale ratio": ratio_model("proc_ma12"),
    "Linear regression": sk_model(LinearRegression),
    "Elastic net": sk_model(lambda: make_pipeline(
        StandardScaler(), ElasticNetCV(l1_ratio=[0.1, 0.5, 0.9, 1.0], cv=TimeSeriesSplit(5),
                                       max_iter=50000, random_state=SEED))),
    "Gradient boosting": sk_model(lambda: HistGradientBoostingRegressor(
        max_depth=3, learning_rate=0.05, max_iter=300, l2_regularization=1.0,
        min_samples_leaf=20, random_state=SEED)),
    "Regression + AR(1) errors": ar_errors,
}
COMBINED = "Combined (all models)"


def predict_all(Xtr, ytr, Xte):
    preds = {name: f(Xtr, ytr, Xte) for name, f in MODELS.items()}
    preds[COMBINED] = pd.concat(list(preds.values()), axis=1).mean(axis=1)
    return pd.DataFrame(preds)


# ---------------- Backtests ----------------
rows = []
for origin in map(pd.Timestamp, ORIGINS):
    train = y.loc[:origin].dropna().index
    test = y.loc[origin + pd.offsets.MonthBegin(1):LAST_ACTUAL].index[:MAX_HORIZON]
    test = test[y.loc[test].notna()]
    P = predict_all(X.loc[train], y.loc[train], X.loc[test])
    for name in P.columns:
        err = P[name] - y.loc[test]
        h = ((test.year - origin.year) * 12 + (test.month - origin.month)).values
        rows.append(pd.DataFrame({"model": name, "origin": origin.date(), "date": test,
                                  "horizon_months": h, "error_log": err.values}))
bt = pd.concat(rows, ignore_index=True)
bt["horizon_year"] = (bt.horizon_months - 1) // 12 + 1
bt.to_csv(OUT / "turkey_backtest_errors.csv", index=False)

pct = lambda e: 100 * (np.exp(e) - 1)
metrics = bt.groupby("model").apply(lambda g: pd.Series({
    "rmse_all_months_pct": 100 * np.sqrt((g.error_log ** 2).mean()),
    "mae_october_pct": 100 * g[g.date.dt.month == 10].error_log.abs().mean(),
    "mean_error_pct": pct(g.error_log.mean()),
    "worst_october_pct": pct(g[g.date.dt.month == 10].error_log.abs().max()),
}), include_groups=False).sort_values("mae_october_pct")
by_h = bt[bt.date.dt.month == 10].groupby(["model", "horizon_year"]).error_log.apply(
    lambda e: 100 * e.abs().mean()).unstack().reindex(metrics.index)
metrics.round(2).to_csv(OUT / "turkey_model_metrics.csv")
BEST = COMBINED


def diebold_mariano(e1, e2, lag=12):
    """DM test on squared-error loss with Newey-West variance (overlapping monthly errors)."""
    d = (e1 ** 2 - e2 ** 2).values
    n, dbar = len(d), d.mean()
    gamma = [np.sum((d[k:] - dbar) * (d[:n - k] - dbar)) / n for k in range(lag + 1)]
    var = gamma[0] + 2 * sum((1 - k / (lag + 1)) * gamma[k] for k in range(1, lag + 1))
    stat = dbar / np.sqrt(var / n)
    from scipy.stats import norm
    return stat, 2 * (1 - norm.cdf(abs(stat)))


wide = bt.pivot_table(index=["origin", "date"], columns="model", values="error_log")
dm = pd.DataFrame([(m, *diebold_mariano(wide[m], wide[COMBINED])) for m in wide.columns if m != COMBINED],
                  columns=["model", "dm_stat_vs_combined", "p_value"]).set_index("model")

# ---------------- Reconstruction ----------------
train = y.loc[:LAST_ACTUAL].dropna().index
gap = X.loc[LAST_ACTUAL + pd.offsets.MonthBegin(1):END].index
P = predict_all(X.loc[train], y.loc[train], X.loc[gap])
h_year = (((gap.year - LAST_ACTUAL.year) * 12 + (gap.month - LAST_ACTUAL.month)) - 1) // 12 + 1
q = bt[bt.model == BEST].groupby("horizon_year").error_log.quantile([0.1, 0.9]).unstack()
q = q.reindex(range(1, h_year.max() + 1)).ffill()  # beyond backtested horizons, keep last band
lo = P[BEST].values - q.loc[h_year, 0.9].values  # actual = prediction - error
hi = P[BEST].values - q.loc[h_year, 0.1].values

to_dollars = lambda s: np.exp(s) * df.food_cpi.reindex(s.index)
rec = pd.DataFrame({f"{m}": to_dollars(P[m]) for m in P.columns})
rec["main_estimate"] = rec[BEST]
rec["band_low_p10"] = to_dollars(pd.Series(lo, index=gap))
rec["band_high_p90"] = to_dollars(pd.Series(hi, index=gap))
actual = df.turkey.loc[:LAST_ACTUAL].dropna()
out = pd.concat([actual.rename("bls_actual"), rec], axis=1)
out.index.name = "month"
out.round(4).to_csv(OUT / "turkey_reconstruction.csv")

# ---------------- Report ----------------
pd.set_option("display.width", 200)
print("== Backtest: rebuild up to 80 months after each origin from predictors only ==")
print(f"Origins: {', '.join(ORIGINS)}; training from {TRAIN_START}; errors are prediction minus actual BLS price")
print(metrics.round(2).to_string())
print("\nOctober absolute error (%) by years after origin:")
print(by_h.round(1).to_string())
print("\nDiebold-Mariano tests, each model vs the combined model (squared error, Newey-West, 12 lags).")
print("Positive statistic = model worse than combined. p < 0.05 would be a real difference:")
print(dm.round(3).to_string())
print(f"\nMain estimate: {BEST}")

octs = rec[rec.index.month == 10].copy()
octs.index = octs.index.year
oct19 = actual.loc["2019-10-01"]
cmp = pd.DataFrame({
    "main_$/lb": octs.main_estimate, "low_p10": octs.band_low_p10, "high_p90": octs.band_high_p90,
    "main_vs_2019_%": 100 * (octs.main_estimate / oct19 - 1),
    "farm_bureau_vs_2019_%": [100 * (AFBF_TURKEY[yr] / AFBF_TURKEY[2019] - 1) for yr in octs.index],
    "chicken_ratio_vs_2019_%": 100 * (octs["Chicken ratio"] / oct19 - 1),
})
print(f"\nOctober reconstruction (BLS Oct 2019 actual: ${oct19:.3f}/lb):")
print(cmp.round(2).to_string())
print("\nAll models, October $/lb:")
print(octs[list(P.columns)].round(3).to_string())

# ---------------- Charts ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import chart_style as cs

colors = {"Chicken ratio": cs.GRAY, BEST: cs.BLUE}
fig, axes = cs.figure(2, 2, width=12, height=8.2, sharey=True)
fig.subplots_adjust(hspace=0.45, top=0.8)
for ax, origin in zip(axes.flat, ORIGINS):
    o = pd.Timestamp(origin)
    win_end = min(o + pd.DateOffset(months=MAX_HORIZON + 1), LAST_ACTUAL)
    win = y.loc[o - pd.DateOffset(years=3):win_end]
    ax.plot(win.index, np.exp(win) * df.food_cpi.reindex(win.index), color=cs.TEXT, lw=1.6, label="BLS actual")
    for name in ["Chicken ratio", BEST]:
        g = bt[(bt.model == name) & (bt.origin == o.date())].set_index("date")
        pred = np.exp(y.loc[g.index] + g.error_log) * df.food_cpi.reindex(g.index)
        ax.plot(pred.index, pred, color=colors[name], lw=2.2 if name == BEST else 1.6,
                ls="-" if name == BEST else (0, (3, 2)), label=name)
    ax.axvline(o, color=cs.MUTED, lw=0.8, ls=":")
    ax.set_title(f"Trained through {o:%b %Y}")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    cs.style_ticks(ax)
for ax in axes.flat:
    cs.unit_on_top(ax, fmt=lambda v: f"{v:.2f}", prefix="$")
axes[0, 0].legend(loc="upper left", fontsize=9)
cs.finish(fig, "Backtests: the combined model misses October turkey prices by about 8% on average",
          "Retail whole frozen turkey, $/lb. Each panel predicts years it never saw, from predictors only.",
          "BLS via FRED; author's models", OUT / "9_turkey_backtest.png")

fig, ax = cs.figure()
m = rec.main_estimate
ax.fill_between(rec.index, rec.band_low_p10, rec.band_high_p90, color=cs.BLUE, alpha=0.15, lw=0)
hist = actual.loc["2014":]
ax.plot(hist.index, hist, color=cs.TEXT, lw=2)
ax.plot(m.index, m, color=cs.BLUE)
ax.plot(rec.index, rec["Chicken ratio"], color=cs.GRAY, lw=1.6, ls=(0, (3, 2)))
afbf_pts = pd.Series({pd.Timestamp(f"{yr}-11-01"): oct19 * v / AFBF_TURKEY[2019] for yr, v in AFBF_TURKEY.items()})
ax.scatter(afbf_pts.index, afbf_pts, color=cs.RED, s=28, zorder=4)
ax.text(hist.index[6], hist.max() + 0.05, "BLS actual", color=cs.TEXT, fontsize=10, fontweight="semibold")
pad = pd.DateOffset(months=3)
cs.label_end(ax, m.index[-1], m.iloc[-1], "Model estimate\n(80% band)", cs.BLUE, dx=pad, dy=0.12)
cs.label_end(ax, rec.index[-1], rec["Chicken ratio"].iloc[-1], "Chicken ratio", cs.GRAY, dx=pad, dy=-0.05)
cs.label_end(ax, afbf_pts.index[-1], afbf_pts.iloc[-1], "Farm Bureau\n(holiday, scaled)", cs.RED, dx=pad, dy=-0.12)
ax.set_xlim(hist.index[0], rec.index[-1] + pd.DateOffset(months=2))
fig.subplots_adjust(right=0.82)
cs.unit_on_top(ax, fmt=lambda v: f"{v:.2f}", prefix="$")
cs.finish(fig, "Rebuilding the turkey price BLS stopped publishing",
          "Retail whole frozen turkey, $/lb, monthly. Farm Bureau points are its holiday price, scaled to BLS's 2019 level.",
          "BLS, American Farm Bureau Federation; author's models", OUT / "10_turkey_reconstruction.png")
