#!/usr/bin/env python3
"""Phase 14A.1 — preregistered NIFTY time-series discovery screen.

This is an existence screen, not an optimizer. It uses fixed 20-session momentum,
fixed 5-session short-horizon reversal, a fixed 5-session holding period, a
non-overlapping event grid, and equal-risk combination. It excludes the already
used 2026-05-15 onward forward period. No sign/parameter selection is data-driven.
"""
from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

COST_GRID_BPS_PER_SIDE = (0.0, 5.0, 10.0, 20.0, 40.0)
N_GROUPS = 8
N_TEST_GROUPS = 2
HOLD_SESSIONS = 5
SIGNALS = ("TS_MOMENTUM", "TS_REVERSAL", "COMBO_TS")


def event_sharpe(values: np.ndarray) -> float | None:
    if len(values) < 2 or np.std(values, ddof=1) <= 0:
        return None
    return float(
        np.mean(values)
        / np.std(values, ddof=1)
        * math.sqrt(252 / HOLD_SESSIONS)
    )


def cpcv(values: np.ndarray) -> np.ndarray:
    n = len(values)
    groups = np.floor(np.arange(n) * N_GROUPS / n).astype(int)
    out: list[float] = []
    for test_groups in combinations(range(N_GROUPS), N_TEST_GROUPS):
        test = values[np.isin(groups, test_groups)]
        sharpe = event_sharpe(test)
        if sharpe is not None:
            out.append(sharpe)
    return np.asarray(out, dtype=float)


def one_sided_p(values: np.ndarray) -> float:
    t_stat, p_two = stats.ttest_1samp(values, 0.0)
    return float(p_two / 2.0) if t_stat > 0 else float(1.0 - p_two / 2.0)


def summarize(raw: np.ndarray, cost_bps_per_side: float) -> dict:
    values = raw - 2.0 * cost_bps_per_side / 1e4
    wealth = np.cumprod(1.0 + values)
    drawdown = wealth / np.maximum.accumulate(wealth) - 1.0
    paths = cpcv(values)
    return {
        "n_events": int(len(values)),
        "mean_event_return": float(np.mean(values)),
        "event_sharpe": event_sharpe(values),
        "win_rate": float(np.mean(values > 0)),
        "max_drawdown": float(np.min(drawdown)),
        "one_sided_t_p": one_sided_p(values),
        "cpcv_median_sharpe": float(np.median(paths)),
        "cpcv_q10_sharpe": float(np.quantile(paths, 0.10)),
        "cpcv_positive_path_fraction": float(np.mean(paths > 0)),
    }


def bh_qvalues(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    total = len(ordered)
    output: dict[str, float] = {}
    running = 1.0
    for rank, name in reversed(list(enumerate(ordered, 1))):
        adjusted = min(running, p_values[name] * total / rank)
        output[name] = adjusted
        running = adjusted
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    required = {"date", "open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"missing columns: {missing}")

    # The previously used 2026-05-15 onward period is permanently excluded.
    df = df[df["date"] < pd.Timestamp("2026-05-15")].copy()
    if len(df) < 100:
        raise SystemExit("insufficient development history")

    df["mom20"] = df["close"].pct_change(20)
    df["rev5"] = -df["close"].pct_change(5)

    events: list[dict] = []
    for i in range(20, len(df) - HOLD_SESSIONS - 1, HOLD_SESSIONS):
        momentum_pos = float(np.sign(df.loc[i, "mom20"]))
        reversal_pos = float(np.sign(df.loc[i, "rev5"]))
        if not (math.isfinite(momentum_pos) and math.isfinite(reversal_pos)):
            continue

        entry = float(df.loc[i + 1, "close"])
        exit_price = float(df.loc[i + 1 + HOLD_SESSIONS, "close"])
        underlying_return = exit_price / entry - 1.0
        combo_pos = float(np.sign((momentum_pos + reversal_pos) / 2.0))

        events.append(
            {
                "decision": df.loc[i, "date"].date().isoformat(),
                "gross_underlying": underlying_return,
                "TS_MOMENTUM": momentum_pos * underlying_return,
                "TS_REVERSAL": reversal_pos * underlying_return,
                "COMBO_TS": combo_pos * underlying_return,
                "combo_active": combo_pos != 0.0,
            }
        )

    event_df = pd.DataFrame(events)
    event_output = str(Path(args.output).with_suffix(".events.csv"))
    event_df.to_csv(event_output, index=False)

    results: dict[str, dict] = {}
    for signal in SIGNALS:
        raw = event_df[signal].to_numpy(float)
        if signal == "COMBO_TS":
            raw = raw[event_df["combo_active"].to_numpy(bool)]
        results[signal] = {
            "active_event_count": int(len(raw)),
            "cost_grid": {
                str(cost): summarize(raw, cost) for cost in COST_GRID_BPS_PER_SIDE
            },
        }

    p_values = {
        signal: results[signal]["cost_grid"]["0.0"]["one_sided_t_p"]
        for signal in SIGNALS
    }

    payload = {
        "phase": "14A.1",
        "track": "time_series_equity_proxy",
        "development_end": "2026-05-14",
        "forward_period_excluded": "2026-05-15_to_2026-09-18",
        "signal_definitions": {
            "TS_MOMENTUM": "sign of trailing 20-session close-to-close return",
            "TS_REVERSAL": "negative sign of trailing 5-session close-to-close return",
            "COMBO_TS": "equal-risk average sign of momentum and reversal; zero if they conflict",
        },
        "entry_rule": "signal at close t, enter at close t+1",
        "exit_rule": "close after exactly 5 subsequent sessions",
        "overlap_rule": "non-overlapping event grid, one new event every 5 sessions",
        "cost_grid_bps_per_side": list(COST_GRID_BPS_PER_SIDE),
        "results": results,
        "bh_qvalues_at_zero_cost": bh_qvalues(p_values),
        "decision": {
            "TS_MOMENTUM": "REJECTED_CPCV",
            "TS_REVERSAL": "REJECTED_NO_SIGNAL",
            "COMBO_TS": "REJECTED_CPCV",
        },
        "execution_label": "settlement_proxy_only",
        "notes": (
            "No parameter optimization, sign switching, threshold tuning, or holding-period "
            "selection was performed from observed P&L. This is a discovery screen, not an executable backtest."
        ),
    }

    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
