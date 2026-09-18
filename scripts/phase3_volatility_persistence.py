#!/usr/bin/env python3
"""Phase 3.3: volatility persistence diagnostics.

Descriptive-only diagnostics for volatility clustering and persistence:
- ACF/PACF of returns and absolute returns
- squared-return autocorrelation
- rolling volatility summary
- simple autocorrelation reference intervals

The output is not a forecast model and does not authorize strategy/execution backtesting.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def acf(series: pd.Series, lag: int) -> float | None:
    x = series.dropna().to_numpy(dtype=float)
    if lag <= 0 or len(x) <= lag + 1:
        return None
    x = x - x.mean()
    denom = float(np.dot(x, x))
    if denom <= 0:
        return None
    return float(np.dot(x[:-lag], x[lag:]) / denom)


def pacf_from_acf(acf_values: list[float | None]) -> dict[str, float | None]:
    """Durbin-Levinson PACF from ACF values indexed by lag 1..k."""
    valid = [v for v in acf_values if v is not None]
    if not valid:
        return {}
    r = [1.0] + [float(v) for v in valid]
    pacf: dict[str, float | None] = {}
    phi = np.zeros((len(r), len(r)), dtype=float)
    var = np.ones(len(r), dtype=float)
    for k in range(1, len(r)):
        num = r[k] - float(np.dot(phi[k - 1, 1:k], r[1:k][::-1]))
        den = var[k - 1]
        if den <= 1e-12:
            pacf[str(k)] = None
            continue
        phi[k, k] = num / den
        for j in range(1, k):
            phi[k, j] = phi[k - 1, j] - phi[k, k] * phi[k - 1, k - j]
        var[k] = var[k - 1] * (1.0 - phi[k, k] ** 2)
        pacf[str(k)] = float(phi[k, k])
    return pacf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-lag", type=int, default=10)
    ap.add_argument("--rolling-window", type=int, default=20)
    args = ap.parse_args()

    if args.max_lag < 1:
        raise SystemExit("max-lag must be >= 1")
    if args.rolling_window < 2:
        raise SystemExit("rolling-window must be >= 2")

    df = pd.read_csv(args.input)
    required = {"timestamp", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = (
        df.dropna(subset=["timestamp", "close"])
        .sort_values("timestamp")
        .drop_duplicates("timestamp", keep="first")
    )
    if len(df) < 4:
        raise SystemExit("At least 4 observations required")
    if (df["close"] <= 0).any():
        raise SystemExit("Non-positive close detected")

    returns = df["close"].pct_change().dropna()
    log_returns = np.log(df["close"]).diff().dropna()
    abs_returns = returns.abs()
    squared_returns = returns.pow(2)

    max_lag = min(args.max_lag, max(1, len(returns) - 2))
    lags = list(range(1, max_lag + 1))

    def acf_dict(series: pd.Series) -> dict[str, float | None]:
        return {str(lag): acf(series, lag) for lag in lags}

    return_acf = acf_dict(returns)
    abs_acf = acf_dict(abs_returns)
    sq_acf = acf_dict(squared_returns)

    def ci_width(n: int) -> float:
        return 1.96 / math.sqrt(max(n, 1))

    width = ci_width(len(returns))
    def attach_ci(values: dict[str, float | None]) -> dict[str, dict[str, float | None]]:
        out: dict[str, dict[str, float | None]] = {}
        for k, value in values.items():
            out[k] = {
                "acf": value,
                "reference_ci_low": None if value is None else float(value - width),
                "reference_ci_high": None if value is None else float(value + width),
            }
        return out

    rolling_vol = returns.rolling(args.rolling_window).std(ddof=1).dropna()
    rolling_summary = {
        "window_periods": args.rolling_window,
        "observations": int(len(rolling_vol)),
        "mean": float(rolling_vol.mean()) if len(rolling_vol) else None,
        "median": float(rolling_vol.median()) if len(rolling_vol) else None,
        "min": float(rolling_vol.min()) if len(rolling_vol) else None,
        "max": float(rolling_vol.max()) if len(rolling_vol) else None,
    }

    pacf_returns = pacf_from_acf([return_acf[str(lag)] for lag in lags])
    pacf_abs = pacf_from_acf([abs_acf[str(lag)] for lag in lags])

    out = {
        "phase": "3.3",
        "status": "BASELINE",
        "rows": int(len(df)),
        "return_observations": int(len(returns)),
        "start": df["timestamp"].iloc[0].isoformat(),
        "end": df["timestamp"].iloc[-1].isoformat(),
        "max_lag": int(max_lag),
        "return_acf": attach_ci(return_acf),
        "absolute_return_acf": attach_ci(abs_acf),
        "squared_return_acf": attach_ci(sq_acf),
        "return_pacf": pacf_returns,
        "absolute_return_pacf": pacf_abs,
        "rolling_volatility": rolling_summary,
        "clustering_diagnostics": {
            "absolute_return_acf_lag1": abs_acf.get("1"),
            "absolute_return_acf_lag5": abs_acf.get("5"),
            "squared_return_acf_lag1": sq_acf.get("1"),
            "squared_return_acf_lag5": sq_acf.get("5"),
        },
        "uncertainty": {
            "reference_interval": "approximately ±1.96/sqrt(N) around each ACF estimate",
            "N": int(len(returns)),
            "caveat": "Reference intervals are an IID benchmark, not a HAC or block-bootstrap confidence interval."
        },
        "diagnostic_only": True,
        "execution_backtest_allowed": False,
        "notes": "Persistence diagnostics are descriptive. Sampling frequency, session construction and missing-data rules must be fixed before comparisons across datasets."
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
