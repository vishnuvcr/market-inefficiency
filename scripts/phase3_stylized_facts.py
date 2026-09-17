#!/usr/bin/env python3
"""Phase 3.1: deterministic stylized-fact diagnostics for canonical underlying data.

No strategy fitting occurs here. The script reports data coverage, returns, volatility,
clustering and tail diagnostics and is deliberately usable on descriptive-only sources.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import pandas as pd


def autocorr_abs(r: pd.Series, lag: int = 1) -> float | None:
    x = r.abs().dropna()
    if len(x) <= lag + 2:
        return None
    v = x.autocorr(lag=lag)
    return None if pd.isna(v) else float(v)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.input)
    required = {"timestamp", "open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp")
    df = df.drop_duplicates("timestamp", keep="first")
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        raise SystemExit("Non-positive price detected")
    r = df["close"].pct_change().dropna()
    log_r = (df["close"].apply(math.log).diff()).dropna()
    out = {
        "phase": "3.1",
        "status": "BASELINE",
        "rows": int(len(df)),
        "start": df["timestamp"].iloc[0].isoformat() if len(df) else None,
        "end": df["timestamp"].iloc[-1].isoformat() if len(df) else None,
        "return_observations": int(len(r)),
        "return_mean": float(r.mean()) if len(r) else None,
        "return_std": float(r.std(ddof=1)) if len(r) > 1 else None,
        "return_skew": float(r.skew()) if len(r) > 2 else None,
        "return_kurtosis_excess": float(r.kurt()) if len(r) > 3 else None,
        "log_return_std": float(log_r.std(ddof=1)) if len(log_r) > 1 else None,
        "abs_return_autocorr_lag1": autocorr_abs(r, 1),
        "abs_return_autocorr_lag5": autocorr_abs(r, 5),
        "close_max_drawdown": float((df["close"] / df["close"].cummax() - 1).min()),
        "diagnostic_only": True,
        "execution_backtest_allowed": False,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
