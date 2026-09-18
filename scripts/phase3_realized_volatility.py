#!/usr/bin/env python3
"""Phase 3.2: range-based realized-volatility diagnostics.

Computes daily/session realized volatility estimators from OHLC data:
- close-to-close (CC)
- Parkinson
- Garman-Klass (GK)
- Yang-Zhang (YZ)

Inputs must already be normalized and ordered. This module is descriptive only:
it does not infer tradability, forecast returns, or authorize execution backtests.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import pandas as pd

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--annualization-periods", type=float, default=252.0)
    args = ap.parse_args()
    if args.annualization_periods <= 0:
        raise SystemExit("annualization-periods must be positive")
    df = pd.read_csv(args.input)
    required = {"timestamp", "open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for c in ["open","high","low","close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=list(required)).sort_values("timestamp")
    df = df.drop_duplicates("timestamp", keep="first")
    if len(df) < 3:
        raise SystemExit("At least 3 observations required")
    if (df[["open","high","low","close"]] <= 0).any().any():
        raise SystemExit("Non-positive price detected")
    if (df["high"] < df[["open","close"]].max(axis=1)).any() or (df["low"] > df[["open","close"]].min(axis=1)).any():
        raise SystemExit("OHLC consistency violation")
    # Treat each input row as one independent period/session. YZ uses the previous close.
    prev_close = df["close"].shift(1)
    oc = (df["open"] / prev_close).apply(math.log)
    co = (df["close"] / df["open"]).apply(math.log)
    hl = (df["high"] / df["low"]).apply(math.log)
    rs = (df["high"] / df["close"]).apply(math.log) * (df["high"] / df["open"]).apply(math.log) +          (df["low"] / df["close"]).apply(math.log) * (df["low"] / df["open"]).apply(math.log)
    valid = prev_close.notna()
    n = int(valid.sum())
    if n < 2:
        raise SystemExit("At least 2 complete return periods required")
    # Period-level components; annualized variance estimates are reported as sqrt(variance * P).
    cc_var = float((oc[valid] + co[valid]).var(ddof=1))
    par_var = float((hl[valid] ** 2).mean() / (4.0 * math.log(2.0)))
    gk_var = float((0.5 * hl[valid] ** 2 - (2.0 * math.log(2.0) - 1.0) * co[valid] ** 2).mean())
    # Yang-Zhang: k chosen from n following the standard finite-sample weighting.
    k = 0.34 / (1.34 + (n + 1.0) / max(n - 1.0, 1.0))
    yz_var = float(oc[valid].var(ddof=1) + k * co[valid].var(ddof=1) + (1.0-k) * rs[valid].mean())
    estimates = {
        "close_to_close": cc_var,
        "parkinson": par_var,
        "garman_klass": gk_var,
        "yang_zhang": yz_var,
    }
    out = {
        "phase": "3.2",
        "status": "BASELINE",
        "rows": int(len(df)),
        "complete_periods": n,
        "start": df["timestamp"].iloc[0].isoformat(),
        "end": df["timestamp"].iloc[-1].isoformat(),
        "annualization_periods": args.annualization_periods,
        "variance_estimates_per_period": estimates,
        "volatility_estimates_annualized": {k: math.sqrt(max(v,0.0)*args.annualization_periods) for k,v in estimates.items()},
        "yang_zhang_k": k,
        "diagnostic_only": True,
        "execution_backtest_allowed": False,
        "notes": "Estimator comparison is descriptive. Sampling frequency and session definition must be fixed before cross-study comparisons."
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
