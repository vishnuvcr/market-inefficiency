#!/usr/bin/env python3
"""Phase 4C descriptive variance-risk-premium diagnostics.

This is an outcome-stage diagnostic, not a trading rule. For each target
calendar horizon, it builds a constant-maturity ATM implied volatility from
the Phase 4B daily surface by linear interpolation in total variance, then
compares it with subsequently realized NIFTY variance over the matched
calendar horizon.

All future realized returns are outcomes only; they are never used to build
the ex-ante implied-volatility feature.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def nw_mean(x: np.ndarray, max_lag: int):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 5:
        return {"n": int(n), "mean": np.nan, "se": np.nan, "t": np.nan, "ci95_low": np.nan, "ci95_high": np.nan}
    mu = float(x.mean())
    u = x - mu
    gamma0 = float(np.mean(u * u))
    var = gamma0
    L = min(max_lag, n - 1)
    for k in range(1, L + 1):
        gamma_k = float(np.mean(u[k:] * u[:-k]))
        weight = 1.0 - k / (L + 1.0)
        var += 2.0 * weight * gamma_k
    se = float(np.sqrt(max(var, 0.0) / n))
    t = mu / se if se > 0 else np.nan
    return {
        "n": int(n),
        "mean": mu,
        "se": se,
        "t": float(t),
        "ci95_low": float(mu - 1.96 * se),
        "ci95_high": float(mu + 1.96 * se),
    }


def constant_maturity_surface(surface: pd.DataFrame, target_days: int) -> pd.DataFrame:
    rows = []
    target_T = target_days / 365.0
    for date, g in surface.groupby("trade_date", sort=True):
        g = g.sort_values("ttm_days").dropna(subset=["atm_iv", "ttm_days"])
        g = g[g["ttm_days"] > 0].copy()
        if g.empty:
            continue

        t = g["ttm_days"].to_numpy(dtype=float)
        iv = g["atm_iv"].to_numpy(dtype=float)
        w = iv * iv * (t / 365.0)

        exact = np.where(t == target_days)[0]
        if len(exact):
            iv_t = iv[exact[0]]
            method = "exact"
        else:
            left = np.where(t < target_days)[0]
            right = np.where(t > target_days)[0]
            if len(left) == 0 or len(right) == 0:
                continue
            i = left[-1]
            j = right[0]
            wt = (target_days - t[i]) / (t[j] - t[i])
            w_t = w[i] + wt * (w[j] - w[i])
            iv_t = np.sqrt(max(w_t / target_T, 0.0))
            method = "linear_total_variance"

        rows.append(
            {
                "trade_date": date,
                "target_days": int(target_days),
                "atm_iv": float(iv_t),
                "implied_variance": float(iv_t * iv_t),
                "interp_method": method,
            }
        )
    return pd.DataFrame(rows)


def realized_variance_by_calendar_horizon(
    underlying: pd.DataFrame, target_days: int
) -> pd.DataFrame:
    u = underlying.sort_values("date").drop_duplicates("date").copy()
    u["log_return"] = np.log(u["close"] / u["close"].shift(1))
    dates = u["date"].to_numpy(dtype="datetime64[ns]")
    r = u["log_return"].to_numpy(dtype=float)

    out = []
    for i, d in enumerate(dates):
        target = d + np.timedelta64(target_days, "D")
        j = int(np.searchsorted(dates, target, side="left"))
        if j >= len(dates) or j <= i:
            continue
        rr = r[i + 1 : j + 1]
        rr = rr[np.isfinite(rr)]
        if len(rr) < 5:
            continue
        actual_days = int((dates[j] - d) / np.timedelta64(1, "D"))
        if actual_days <= 0:
            continue
        rv = float(np.sum(rr * rr) * 365.0 / actual_days)
        out.append(
            {
                "trade_date": pd.Timestamp(d).strftime("%Y-%m-%d"),
                "realized_variance": rv,
                "realized_vol": float(np.sqrt(max(rv, 0.0))),
                "actual_days": actual_days,
                "realized_return_count": int(len(rr)),
            }
        )
    return pd.DataFrame(out)


def trailing_vol_state(underlying: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    u = underlying.sort_values("date").drop_duplicates("date").copy()
    u["log_return"] = np.log(u["close"] / u["close"].shift(1))
    # Prior-window realized volatility: fully PIT, excluding today's return.
    u["trailing_rv"] = u["log_return"].shift(1).rolling(window).apply(
        lambda x: np.sum(np.asarray(x) ** 2) * 252.0 / len(x), raw=False
    )
    u["trailing_vol"] = np.sqrt(u["trailing_rv"])
    return u[["date", "trailing_vol"]].rename(columns={"date": "trade_date"})


def summarize(df: pd.DataFrame, horizon: int) -> dict:
    x = df.dropna(subset=["vrp_variance"]).copy()
    base = nw_mean(x["vrp_variance"].to_numpy(), max_lag=max(horizon // 2, 1))
    vol_diff = nw_mean(x["vrp_vol"].to_numpy(), max_lag=max(horizon // 2, 1))
    base["positive_fraction"] = float((x["vrp_variance"] > 0).mean()) if len(x) else np.nan
    base["median"] = float(x["vrp_variance"].median()) if len(x) else np.nan
    base["p25"] = float(x["vrp_variance"].quantile(0.25)) if len(x) else np.nan
    base["p75"] = float(x["vrp_variance"].quantile(0.75)) if len(x) else np.nan
    return {
        "horizon_days": int(horizon),
        "n": int(len(x)),
        "coverage_start": x["trade_date"].min() if len(x) else None,
        "coverage_end": x["trade_date"].max() if len(x) else None,
        "variance_risk_premium": base,
        "volatility_difference": vol_diff,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", required=True, type=Path)
    ap.add_argument("--underlying", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--horizons", default="30,60")
    args = ap.parse_args()

    surface = pd.read_csv(args.surface)
    surface["trade_date"] = pd.to_datetime(surface["trade_date"], errors="coerce")
    surface["ttm_days"] = pd.to_numeric(surface["ttm_days"], errors="coerce")
    surface["atm_iv"] = pd.to_numeric(surface["atm_iv"], errors="coerce")
    surface = surface.dropna(subset=["trade_date", "ttm_days", "atm_iv"])
    surface = surface[(surface["atm_iv"] > 0) & (surface["atm_iv"] <= 5)]

    underlying = pd.read_csv(args.underlying)
    underlying["date"] = pd.to_datetime(underlying["date"], errors="coerce")
    underlying["close"] = pd.to_numeric(underlying["close"], errors="coerce")
    underlying = underlying.dropna(subset=["date", "close"])
    underlying = underlying[underlying["close"] > 0].sort_values("date")

    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    combined = []

    for h in [int(v.strip()) for v in args.horizons.split(",") if v.strip()]:
        imp = constant_maturity_surface(surface, h)
        rv = realized_variance_by_calendar_horizon(underlying, h)
        x = imp.merge(rv, on="trade_date", how="inner")
        x["vrp_variance"] = x["implied_variance"] - x["realized_variance"]
        x["vrp_vol"] = x["atm_iv"] - x["realized_vol"]
        state = trailing_vol_state(underlying)
        x = x.merge(state, on="trade_date", how="left")
        x["horizon_days"] = h

        # Volatility-regime terciles are frozen from the PIT trailing measure.
        valid_state = x["trailing_vol"].dropna()
        if len(valid_state) >= 30:
            q1, q2 = valid_state.quantile([1 / 3, 2 / 3]).to_numpy()
            x["regime"] = pd.cut(
                x["trailing_vol"],
                bins=[-np.inf, q1, q2, np.inf],
                labels=["LOW", "MID", "HIGH"],
            )
        else:
            x["regime"] = pd.NA

        combined.append(x)
        s = summarize(x, h)
        regime_summary = {}
        for regime, g in x.groupby("regime", observed=True):
            regime_summary[str(regime)] = {
                "n": int(g["vrp_variance"].notna().sum()),
                "mean_vrp_variance": float(g["vrp_variance"].mean()),
                "median_vrp_variance": float(g["vrp_variance"].median()),
                "positive_fraction": float((g["vrp_variance"] > 0).mean()),
            }
        s["trailing_realized_vol_regimes"] = regime_summary
        s["constant_maturity_coverage"] = {
            "implied_rows": int(len(imp)),
            "matched_rows": int(len(x)),
        }
        reports.append(s)

    if not combined:
        raise SystemExit("No matched IV/realized-variance observations")

    daily = pd.concat(combined, ignore_index=True).sort_values(
        ["trade_date", "horizon_days"]
    )
    daily["trade_date"] = daily["trade_date"].dt.strftime("%Y-%m-%d")
    daily.to_csv(
        args.output / "phase4c_vrp_daily.csv.gz", index=False, compression="gzip"
    )

    report = {
        "status": "PASS",
        "phase": "4C",
        "objective": "Descriptive variance-risk-premium and state-dependence diagnostics",
        "feature_rule": "constant-maturity ATM IV by linear interpolation in total variance",
        "outcome_rule": "subsequent NIFTY realized variance over matched calendar horizon",
        "realized_variance_annualization": "sum of forward daily squared log returns * 365 / actual calendar days",
        "pit_state_rule": "20-session trailing realized volatility using returns through trade_date-1",
        "results": reports,
        "interpretation_guardrail": "Positive mean variance premium means implied variance exceeded subsequent realized variance in this descriptive sample; it is not evidence by itself of a tradable net-of-cost strategy.",
    }
    (args.output / "PHASE4C_VRP_REPORT.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
