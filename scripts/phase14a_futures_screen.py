#!/usr/bin/env python3
"""Phase 14A.1 — fixed NIFTY futures basis/term discovery screen.

No parameter optimization:
- basis signal: annualized near-future basis; trade opposite sign for 5 sessions;
- term signal: annualized front-vs-next futures curve slope; trade opposite sign for 5 sessions;
- expiry-flow diagnostic: fixed five-session pre-expiry window, reported separately;
- contracts are chosen mechanically from each date; no hindsight contract selection.

These are settlement-price economic proxies, not executable fills.
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

COSTS = (0.0, 5.0, 10.0, 20.0, 40.0)
HOLD = 5
N_GROUPS = 8
N_TEST = 2


def sharpe(x: np.ndarray) -> float | None:
    if len(x) < 2 or np.std(x, ddof=1) <= 0:
        return None
    return float(np.mean(x) / np.std(x, ddof=1) * math.sqrt(252 / HOLD))


def cpcv(x: np.ndarray) -> np.ndarray:
    n = len(x)
    groups = np.floor(np.arange(n) * N_GROUPS / n).astype(int)
    vals = []
    for tg in combinations(range(N_GROUPS), N_TEST):
        s = sharpe(x[np.isin(groups, tg)])
        if s is not None:
            vals.append(s)
    return np.asarray(vals, dtype=float) if vals else np.asarray([np.nan])


def one_sided_p(x: np.ndarray) -> float:
    t, p = stats.ttest_1samp(x, 0.0)
    return float(p / 2.0 if t > 0 else 1.0 - p / 2.0)


def summarize(x: np.ndarray) -> dict:
    out = {}
    for cost in COSTS:
        y = x - 2.0 * cost / 1e4
        paths = cpcv(y)
        wealth = np.cumprod(1.0 + y)
        dd = wealth / np.maximum.accumulate(wealth) - 1.0
        out[str(cost)] = {
            "n_events": int(len(y)),
            "mean_event_return": float(np.mean(y)),
            "event_sharpe": sharpe(y),
            "win_rate": float(np.mean(y > 0)),
            "max_drawdown": float(np.min(dd)),
            "one_sided_t_p": one_sided_p(y),
            "cpcv_median_sharpe": float(np.nanmedian(paths)),
            "cpcv_q10_sharpe": float(np.nanquantile(paths, 0.10)),
            "cpcv_positive_path_fraction": float(np.nanmean(paths > 0)),
        }
    return out


def _clean_fno(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["trade_date"] = pd.to_datetime(out["FH_TIMESTAMP"], errors="coerce", dayfirst=True)
    out["expiry"] = pd.to_datetime(out["FH_EXPIRY_DT"], errors="coerce", dayfirst=True)
    for col in ["FH_CLOSING_PRICE", "FH_SETTLE_PRICE", "FH_UNDERLYING_VALUE", "FH_TOT_TRADED_QTY", "FH_OPEN_INT", "FH_MARKET_LOT"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["trade_date", "expiry", "FH_SETTLE_PRICE", "FH_UNDERLYING_VALUE"])
    out = out[(out["expiry"] > out["trade_date"]) & (out["trade_date"] < pd.Timestamp("2026-05-15"))]
    out["ttm_days"] = (out["expiry"] - out["trade_date"]).dt.days
    out["basis_ann"] = (out["FH_SETTLE_PRICE"] / out["FH_UNDERLYING_VALUE"] - 1.0) * 365.0 / out["ttm_days"]
    return out


def build_events(fno: pd.DataFrame) -> pd.DataFrame:
    rows = []
    by_date = fno.groupby("trade_date")
    # Mechanical nearest-near contract: first expiry >= 7 days and <= 45 days.
    # Mechanical deferred contract: first expiry >= 30 days after the near expiry.
    for d, snap in by_date:
        expiries = sorted(pd.to_datetime(snap["expiry"].dropna().unique()))
        near = next((e for e in expiries if 7 <= (e - d).days <= 45), None)
        if near is None:
            continue
        nxt = next((e for e in expiries if (e - near).days >= 20), None)
        if nxt is None:
            continue
        a = snap[snap["expiry"].eq(near)]
        b = snap[snap["expiry"].eq(nxt)]
        if a.empty or b.empty:
            continue
        a = a.iloc[0]; b = b.iloc[0]
        spot = float(a["FH_UNDERLYING_VALUE"])
        fa = float(a["FH_SETTLE_PRICE"]); fb = float(b["FH_SETTLE_PRICE"])
        ta = max((near - d).days, 1); tb = max((nxt - d).days, 1)
        basis = (fa / spot - 1.0) * 365.0 / ta
        curve = math.log(fb / fa) / max((tb - ta) / 365.0, 1/365.0)
        rows.append({
            "decision": d.date().isoformat(),
            "near_expiry": near.date().isoformat(),
            "next_expiry": nxt.date().isoformat(),
            "near_settle": fa, "next_settle": fb, "spot": spot,
            "basis_ann": basis, "curve_slope_ann": curve,
        })
    events = pd.DataFrame(rows)
    if events.empty:
        return events
    events["entry_date"] = pd.to_datetime(events["decision"])
    events = events.sort_values("entry_date").reset_index(drop=True)
    # Map to next and +5th available decision dates. The strategy is a proxy on the
    # near-vs-spot and front-vs-next relative prices, normalized by initial spot.
    dates = pd.DatetimeIndex(events["entry_date"].unique())
    pos = {d: i for i, d in enumerate(dates)}
    out = []
    for _, r in events.iterrows():
        i = pos[pd.Timestamp(r["entry_date"])]
        if i + HOLD >= len(dates):
            continue
        r = r.copy()
        r["exit_date"] = dates[i + HOLD]
        out.append(r)
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--futures", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    fno = _clean_fno(pd.read_csv(args.futures))
    events = build_events(fno)
    if events.empty:
        raise SystemExit("No futures events available")

    # Reconstruct 5-session P&L using the exact same mechanically chosen expiries.
    fno["key"] = fno["trade_date"].dt.strftime("%Y-%m-%d") + "|" + fno["expiry"].dt.strftime("%Y-%m-%d")
    lookup = fno.set_index("key")["FH_SETTLE_PRICE"].to_dict()
    basis_ret=[]; curve_ret=[]; expiry_ret=[]
    for _, r in events.iterrows():
        exit_day = pd.Timestamp(r["exit_date"])
        nk = exit_day.strftime("%Y-%m-%d") + "|" + r["near_expiry"]
        xk = exit_day.strftime("%Y-%m-%d") + "|" + r["next_expiry"]
        if nk not in lookup or xk not in lookup:
            continue
        f0=float(r["near_settle"]); fn=float(lookup[nk]);
        f20=float(r["next_settle"]); fx=float(lookup[xk]); spot=float(r["spot"])
        basis_pnl = -(fn-f0)/spot if r["basis_ann"]>0 else (fn-f0)/spot
        curve_change=(fx-fn)/spot-(f20-f0)/spot
        curve_pnl = -curve_change if r["curve_slope_ann"]>0 else curve_change
        days_to_expiry=(pd.Timestamp(r["near_expiry"])-pd.Timestamp(r["entry_date"])).days
        expiry_pnl=(fn-f0)/spot if days_to_expiry<=5 else 0.0
        rec=dict(r); rec.update({"basis_ret":basis_pnl,"curve_ret":curve_pnl,"expiry_ret":expiry_pnl})
        basis_ret.append(rec)
    out=pd.DataFrame(basis_ret)
    if out.empty: raise SystemExit("No complete 5-session futures events")
    signals={"FUT_BASIS":"basis_ret","FUT_TERM":"curve_ret","EXPIRY_EFFECT":"expiry_ret"}
    results={sig:{"cost_grid":summarize(out[col].to_numpy(float))} for sig,col in signals.items()}
    out.to_csv(Path(args.output).with_suffix(".events.csv"),index=False)
    payload={
       "phase":"14A.1","track":"nifty_futures",
       "development_end":"2026-05-14","forward_period_excluded":"2026-05-15_to_2026-09-18",
       "mechanics":"nearest eligible futures vs spot and first deferred eligible futures, fixed 5-session horizon",
       "results":results,
       "execution_label":"settlement_proxy_only",
       "decision":"discovery_screen_only_no_optimization",
    }
    Path(args.output).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__": main()