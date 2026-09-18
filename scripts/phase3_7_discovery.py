#!/usr/bin/env python3
"""Phase 3.7: exploratory cross-sectional/time-series discovery diagnostics.

This is a descriptive discovery layer only. It does not fit a trading strategy,
does not claim an inefficiency, and is not leakage-safe predictive modelling.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def load_daily(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns in {path}: {missing}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    return df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)


def sessionize_minute(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"date", "open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns in {path}: {missing}")
    t = pd.to_datetime(df["date"], errors="coerce", format="mixed", dayfirst=True)
    df["ts"] = t.dt.tz_localize("Asia/Kolkata", ambiguous="NaT", nonexistent="NaT")
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["ts", "open", "high", "low", "close"])
    mins = df["ts"].dt.hour * 60 + df["ts"].dt.minute
    df = df[(mins >= 555) & (mins <= 930)].copy()
    df["session_date"] = df["ts"].dt.date
    daily = df.groupby("session_date", sort=True).agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last")
    ).reset_index()
    d = pd.to_datetime(daily["session_date"])
    daily["timestamp"] = d.dt.tz_localize("Asia/Kolkata").dt.tz_convert("UTC")
    return daily[["timestamp", "open", "high", "low", "close"]]


def corr(a: pd.Series, b: pd.Series, method: str) -> float | None:
    x = pd.concat([a, b], axis=1).dropna()
    if len(x) < 20:
        return None
    v = x.iloc[:, 0].corr(x.iloc[:, 1], method=method)
    return None if pd.isna(v) else float(v)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nifty", required=True)
    ap.add_argument("--vix", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    n = load_daily(args.nifty)
    v = sessionize_minute(args.vix)
    n["return"] = n["close"].pct_change()
    n["range_pct"] = (n["high"] - n["low"]) / n["open"]
    n["realized_proxy"] = n["return"].rolling(20).std() * np.sqrt(252)
    v = v.rename(columns={"close": "vix_close"})
    m = n[["timestamp", "return", "range_pct", "realized_proxy"]].merge(
        v[["timestamp", "vix_close"]], on="timestamp", how="inner"
    )
    m["vix_change"] = m["vix_close"].pct_change()
    m["next_return"] = m["return"].shift(-1)
    m["next_abs_return"] = m["return"].abs().shift(-1)

    # Build terciles only from non-missing VIX observations, then restore the
    # original index. This avoids qcut failures caused by NaN ranks in small
    # or synthetic fixtures while leaving missing VIX rows unclassified.
    valid_vix = m["vix_close"].notna()
    if int(valid_vix.sum()) < 3:
        raise SystemExit("Insufficient non-missing VIX observations for terciles")
    ranks = m.loc[valid_vix, "vix_close"].rank(method="first")
    labels = pd.qcut(ranks, 3, labels=["LOW", "MID", "HIGH"])
    m["vix_tercile"] = pd.Series(labels.astype("object").to_numpy(), index=m.index[valid_vix])

    conditional = {}
    for label, g in m.groupby("vix_tercile", observed=True):
        conditional[str(label)] = {
            "observations": int(len(g)),
            "mean_abs_return": float(g["return"].abs().mean()),
            "mean_range_pct": float(g["range_pct"].mean()),
            "mean_realized_proxy_20d": float(g["realized_proxy"].mean()),
            "mean_next_abs_return": float(g["next_abs_return"].mean()),
        }

    out = {
        "phase": "3.7",
        "status": "DISCOVERY",
        "diagnostic_only": True,
        "execution_backtest_allowed": False,
        "nifty_rows": int(len(n)),
        "vix_session_rows": int(len(v)),
        "overlap_rows": int(len(m)),
        "overlap_start": m["timestamp"].min().isoformat() if len(m) else None,
        "overlap_end": m["timestamp"].max().isoformat() if len(m) else None,
        "nifty_return_vix_level": {
            "pearson": corr(m["return"], m["vix_close"], "pearson"),
            "spearman": corr(m["return"], m["vix_close"], "spearman"),
        },
        "abs_return_vix_level": {
            "pearson": corr(m["return"].abs(), m["vix_close"], "pearson"),
            "spearman": corr(m["return"].abs(), m["vix_close"], "spearman"),
        },
        "vix_change_next_abs_return": {
            "pearson": corr(m["vix_change"], m["next_abs_return"], "pearson"),
            "spearman": corr(m["vix_change"], m["next_abs_return"], "spearman"),
        },
        "conditional_by_vix_tercile": conditional,
        "notes": [
            "Discovery statistics are exploratory and unadjusted for multiple testing.",
            "VIX level is contemporaneous with the same session and is not a predictive signal here.",
            "No option prices, bid/ask quotes, implied-volatility surface, or execution costs are used.",
            "Any candidate inefficiency must pass preregistration, point-in-time controls, CPCV, DSR/PBO, cost and untouched-holdout tests."
        ]
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
