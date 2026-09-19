#!/usr/bin/env python3
"""Phase 14A.1 — PIT cross-sectional equity discovery screen.

Frozen discovery rules:
- 20-session cross-sectional momentum, 5-session cross-sectional reversal,
  20-session illiquidity premium, and 20-session abnormal-turnover signal.
- Rebalance every 5 sessions.
- Rank-centred weights, gross exposure normalised to one.
- Enter next session close and exit five sessions later.
- No top/bottom threshold, leverage, lookback or weight optimisation.
- Only members of NIFTY 50 on decision date may enter.
- Historical former constituents remain in the price union so exits are survivorship-safe.
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

COST_GRID_BPS = (0.0, 5.0, 10.0, 20.0, 40.0)
N_GROUPS = 8
N_TEST = 2
HOLD = 5
SIGNALS = ("XS_MOMENTUM", "XS_REVERSAL", "LIQUIDITY_EFFECT", "VOLUME_SHOCK", "COMBO_XS")


def sharpe(values: np.ndarray) -> float | None:
    if len(values) < 2 or np.std(values, ddof=1) <= 0:
        return None
    return float(np.mean(values) / np.std(values, ddof=1) * math.sqrt(252 / HOLD))


def cpcv(values: np.ndarray) -> np.ndarray:
    n = len(values)
    groups = np.floor(np.arange(n) * N_GROUPS / n).astype(int)
    out = []
    for test_groups in combinations(range(N_GROUPS), N_TEST):
        x = values[np.isin(groups, test_groups)]
        s = sharpe(x)
        if s is not None:
            out.append(s)
    return np.asarray(out, dtype=float)


def one_sided_p(x: np.ndarray) -> float:
    t, p2 = stats.ttest_1samp(x, 0.0)
    return float(p2 / 2.0 if t > 0 else 1.0 - p2 / 2.0)


def bh_qvalues(pvals: dict[str, float]) -> dict[str, float]:
    order = sorted(pvals, key=pvals.get)
    out = {}
    running = 1.0
    n = len(order)
    for rank, name in reversed(list(enumerate(order, 1))):
        running = min(running, pvals[name] * n / rank)
        out[name] = running
    return out


def weighted_portfolio(frame: pd.DataFrame, signal_col: str, exit_date: pd.Timestamp) -> float | None:
    active = frame[frame["active_nifty50"]].copy()
    active = active.dropna(subset=[signal_col, "entry_close", "exit_close"])
    if len(active) < 40:
        return None
    score = active[signal_col].astype(float)
    score = score - score.mean()
    denom = float(np.abs(score).sum())
    if denom <= 0:
        return None
    weights = score / denom
    returns = active["exit_close"] / active["entry_close"] - 1.0
    return float(np.sum(weights.to_numpy() * returns.to_numpy()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input, parse_dates=["date"]).reset_index(drop=True)
    required = {"date", "symbol_raw", "active_nifty50", "close", "turnover_inr"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"missing columns: {missing}")
    instrument = "symbol_raw" if "symbol_raw" in df.columns else "symbol"
    df["active_nifty50"] = df["active_nifty50"].astype(bool)
    # Prefer the primary EQ series if NSE carries multiple series for the same symbol/date.
    series_priority = {"EQ":0,"BE":1,"BZ":2,"ST":3,"SM":4}
    df["_series_priority"] = df.get("series", pd.Series("EQ", index=df.index)).map(series_priority).fillna(99)
    df = df.sort_values([instrument,"date","_series_priority"]).drop_duplicates([instrument,"date"], keep="first")
    df = df.drop(columns=["_series_priority"])
    # Daily return proxy uses exchange PREV_CLOSE when available; it avoids raw-price
    # split shocks without inventing an adjusted-price series.
    if "prev_close" in df.columns:
        df["daily_ret"] = df["close"] / df["prev_close"] - 1.0
    else:
        df["daily_ret"] = df.groupby(instrument)["close"].pct_change()
    df["turnover_inr"] = pd.to_numeric(df["turnover_inr"], errors="coerce")
    g = df.groupby(instrument, group_keys=False)
    df["ret20"] = g["daily_ret"].transform(lambda s: (1.0 + s).rolling(20).apply(np.prod, raw=True) - 1.0)
    df["ret5"] = g["daily_ret"].transform(lambda s: (1.0 + s).rolling(5).apply(np.prod, raw=True) - 1.0)
    df["turn20"] = g["turnover_inr"].transform(lambda s: s.rolling(20).median())
    df["turn5"] = g["turnover_inr"].transform(lambda s: s.rolling(5).median())
    df["vol_shock"] = np.log1p(df["turn5"] / df["turn20"] - 1.0)

    dates = pd.DatetimeIndex(sorted(df["date"].unique()))
    decision_dates = dates[20::HOLD]
    rows = []
    # Build a date-indexed view for deterministic entry/exit mapping.
    date_pos = {d: i for i, d in enumerate(dates)}
    for d in decision_dates:
        i = date_pos[d]
        if i + HOLD >= len(dates):
            break
        entry_date = dates[i + 1]
        exit_date = dates[i + HOLD]
        if exit_date >= pd.Timestamp("2026-05-15"):
            continue
        snap = df[df["date"].eq(d)].copy()
        entry = df[df["date"].eq(entry_date)][[instrument, "close"]].rename(columns={instrument:"instrument_key","close":"entry_close"})
        exit_ = df[df["date"].eq(exit_date)][[instrument, "close"]].rename(columns={instrument:"instrument_key","close":"exit_close"})
        snap["instrument_key"] = snap[instrument]
        snap = snap.merge(entry,on="instrument_key",how="left").merge(exit_,on="instrument_key",how="left")
        # Fixed sign conventions: momentum long winners; reversal long losers;
        # liquidity premium long less liquid; volume shock continuation long high shock.
        for name, source, sign in [
            ("XS_MOMENTUM", "ret20", +1.0),
            ("XS_REVERSAL", "ret5", -1.0),
            ("LIQUIDITY_EFFECT", "turn20", -1.0),
            ("VOLUME_SHOCK", "vol_shock", +1.0),
        ]:
            snap[name] = sign * snap[source]
        valid = snap[snap["active_nifty50"]].copy()
        for name in ("XS_MOMENTUM", "XS_REVERSAL", "LIQUIDITY_EFFECT", "VOLUME_SHOCK"):
            valid[name + "_rank"] = valid[name].rank(pct=True, method="average") - 0.5
        for name in ("XS_MOMENTUM", "XS_REVERSAL", "LIQUIDITY_EFFECT", "VOLUME_SHOCK"):
            r = weighted_portfolio(valid, name + "_rank", exit_date)
            rows.append({"decision": d.date().isoformat(), "entry": entry_date.date().isoformat(), "exit": exit_date.date().isoformat(), "signal": name, "gross_return": r})
        comp = valid[[n + "_rank" for n in ("XS_MOMENTUM", "XS_REVERSAL", "LIQUIDITY_EFFECT", "VOLUME_SHOCK")]].mean(axis=1)
        valid["COMBO_XS_rank"] = comp
        r = weighted_portfolio(valid, "COMBO_XS_rank", exit_date)
        rows.append({"decision": d.date().isoformat(), "entry": entry_date.date().isoformat(), "exit": exit_date.date().isoformat(), "signal": "COMBO_XS", "gross_return": r})

    events = pd.DataFrame(rows).dropna(subset=["gross_return"])
    results = {}
    pvals = {}
    for signal in SIGNALS:
        x = events.loc[events.signal.eq(signal), "gross_return"].to_numpy(float)
        pvals[signal] = one_sided_p(x)
        grid = {}
        for cost in COST_GRID_BPS:
            net = x - 2.0 * cost / 1e4
            paths = cpcv(net)
            wealth = np.cumprod(1.0 + net)
            dd = wealth / np.maximum.accumulate(wealth) - 1.0
            grid[str(cost)] = {
                "n_events": int(len(net)),
                "mean_event_return": float(np.mean(net)),
                "event_sharpe": sharpe(net),
                "win_rate": float(np.mean(net > 0)),
                "max_drawdown": float(np.min(dd)),
                "one_sided_t_p": one_sided_p(net),
                "cpcv_median_sharpe": float(np.median(paths)),
                "cpcv_q10_sharpe": float(np.quantile(paths, 0.10)),
                "cpcv_positive_path_fraction": float(np.mean(paths > 0)),
            }
        results[signal] = {"cost_grid": grid}

    q = bh_qvalues(pvals)
    out = {
        "phase":"14A.1",
        "track":"equity_cross_section",
        "development_end":"2026-05-14",
        "forward_period_excluded":"2026-05-15_to_2026-09-18",
        "rebalance_rule":"every 5 sessions; decision at close t; entry at close t+1; exit at close t+5",
        "weight_rule":"cross-sectional rank centered at zero and normalised to sum absolute weights to one",
        "minimum_active_members":40,
        "cost_grid_bps_per_side":list(COST_GRID_BPS),
        "results":results,
        "bh_qvalues_at_zero_cost":q,
        "execution_label":"settlement_proxy_only",
        "decision":"discovery_screen_only_no_optimization",
    }
    event_path = Path(args.output).with_suffix('.events.csv')
    events.to_csv(event_path,index=False)
    Path(args.output).write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__":
    main()