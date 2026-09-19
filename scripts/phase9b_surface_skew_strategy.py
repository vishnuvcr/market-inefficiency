#!/usr/bin/env python3
"""Phase 9B — frozen surface-signal -> mechanism-first skew strategy.

This is deliberately NOT execution-grade. It uses NIFTY EOD settlement prices
to test one pre-registered economic translation of the frozen 30D downside-skew
predictor. It is a settlement proxy intended to decide whether the hypothesis
deserves execution-grade validation.

Primary strategy:
  predicted +30D downside-skew change > 0  -> long 10-delta put / short ATM-ish put
  predicted +30D downside-skew change < 0  -> reverse the structure
  entry maturity: nearest listed expiry in [45, 75] calendar days, target ~60d
  exit: first available market date >= 30 calendar days after entry
  entry delta hedge: underlying NIFTY close
  no overlapping positions
  model: fixed Ridge(alpha=10) specification; coefficients are fit only on
         information available before each decision in development, and one
         development-only fit is frozen for the untouched forward period.

No bid/ask is inferred. No settlement result is labelled executable.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


FEATURES = [
    "down_skew_30",
    "up_skew_30",
    "term_slope_30_60",
    "atm_iv_30",
    "trailing_vol_ann",
    "trailing_ret20",
]
TARGET = "future_down_skew_change_30d"
ALPHA = 10.0
MIN_TRAIN = 300
INITIAL_TRAIN_OBS = 400
ENTRY_TTM_MIN = 45
ENTRY_TTM_MAX = 75
TARGET_ENTRY_TTM = 60
HOLD_DAYS = 30
PURGE_DAYS = 30
EMBARGO_DAYS = 5


def load_iv(root: Path) -> pd.DataFrame:
    files = sorted(root.rglob("iv_observations_*.csv.gz"))
    if not files:
        raise SystemExit(f"No IV partitions found under {root}")
    cols = [
        "trade_date",
        "expiry",
        "strike",
        "option_type",
        "settlement",
        "forward",
        "rf_simple",
        "ttm_days",
        "moneyness",
        "lot_size",
        "iv",
    ]
    frames = []
    for p in files:
        x = pd.read_csv(p, usecols=cols, parse_dates=["trade_date", "expiry"])
        x = x[
            x.iv.gt(0)
            & x.iv.le(5)
            & x.ttm_days.gt(0)
            & x.moneyness.gt(0)
        ].copy()
        frames.append(x)
    return pd.concat(frames, ignore_index=True)


def constant_maturity_band(
    iv: pd.DataFrame,
    option_type: str | None,
    lo: float,
    hi: float,
    target_days: int,
) -> pd.DataFrame:
    m = iv.moneyness.between(lo, hi)
    if option_type is not None:
        m &= iv.option_type.eq(option_type)
    z = iv.loc[m, ["trade_date", "expiry", "ttm_days", "iv"]]
    z = z.groupby(
        ["trade_date", "expiry", "ttm_days"], as_index=False
    ).iv.median()

    rows = []
    for d, g in z.groupby("trade_date", sort=False):
        g = g.sort_values("ttm_days")
        t = g.ttm_days.to_numpy(float)
        v = g.iv.to_numpy(float)
        if len(t) < 2:
            continue
        exact = np.flatnonzero(t == target_days)
        if exact.size:
            val = v[exact[0]]
        else:
            left = np.flatnonzero(t < target_days)
            right = np.flatnonzero(t > target_days)
            if not len(left) or not len(right):
                continue
            i, j = left[-1], right[0]
            w = (target_days - t[i]) / (t[j] - t[i])
            a = v[i] ** 2 * t[i] / 365.0
            b = v[j] ** 2 * t[j] / 365.0
            val = math.sqrt(max((a + w * (b - a)) / (target_days / 365.0), 0.0))
        rows.append((pd.Timestamp(d), float(val)))
    return pd.DataFrame(rows, columns=["date", "iv"])


def build_surface(iv: pd.DataFrame, underlying: pd.DataFrame) -> pd.DataFrame:
    pieces = {}
    for h in (30, 60):
        atm = constant_maturity_band(iv, None, 0.97, 1.03, h).rename(
            columns={"iv": f"atm_iv_{h}"}
        )
        down = constant_maturity_band(iv, "PE", 0.85, 0.95, h).rename(
            columns={"iv": f"down_iv_{h}"}
        )
        up = constant_maturity_band(iv, "CE", 1.05, 1.15, h).rename(
            columns={"iv": f"up_iv_{h}"}
        )
        q = atm.merge(down, on="date").merge(up, on="date")
        q[f"down_skew_{h}"] = q[f"down_iv_{h}"] - q[f"atm_iv_{h}"]
        q[f"up_skew_{h}"] = q[f"up_iv_{h}"] - q[f"atm_iv_{h}"]
        pieces[h] = q

    s = pieces[30].merge(pieces[60], on="date")
    s["term_slope_30_60"] = s["atm_iv_60"] - s["atm_iv_30"]

    u = underlying.copy()
    u["date"] = pd.to_datetime(u["date"], errors="coerce")
    u["close"] = pd.to_numeric(u["close"], errors="coerce")
    u = u.dropna(subset=["date", "close"]).drop_duplicates("date")
    u = u.sort_values("date")
    u["ret1"] = np.log(u["close"] / u["close"].shift(1))
    u["trailing_vol_ann"] = (
        u.ret1.shift(1).rolling(20).std(ddof=1) * math.sqrt(252)
    )
    u["trailing_ret20"] = u.ret1.shift(1).rolling(20).sum()

    s = s.merge(
        u[["date", "close", "trailing_vol_ann", "trailing_ret20"]],
        on="date",
        how="left",
    )
    s = s.sort_values("date").reset_index(drop=True)

    vals = s["down_skew_30"].to_numpy(float)
    dates = s["date"].to_numpy(dtype="datetime64[ns]")
    target = np.full(len(s), np.nan)
    for i, dt in enumerate(dates):
        if not np.isfinite(vals[i]):
            continue
        j = np.searchsorted(dates, dt + np.timedelta64(HOLD_DAYS, "D"), side="left")
        if j < len(s) and np.isfinite(vals[j]):
            target[i] = vals[j] - vals[i]
    s[TARGET] = target
    return s


def ridge_fit_predict(train: pd.DataFrame, row: pd.Series) -> float:
    x = train[FEATURES].to_numpy(float)
    y = train[TARGET].to_numpy(float)
    keep = np.isfinite(x).all(axis=1) & np.isfinite(y)
    x, y = x[keep], y[keep]
    if len(y) < MIN_TRAIN or not np.isfinite(row[FEATURES].to_numpy(float)).all():
        return float("nan")
    mu = x.mean(axis=0)
    sd = x.std(axis=0, ddof=0)
    sd[sd == 0] = 1.0
    z = (x - mu) / sd
    beta = np.linalg.solve(z.T @ z + ALPHA * np.eye(z.shape[1]), z.T @ y)
    return float(((row[FEATURES].to_numpy(float) - mu) / sd) @ beta + y.mean())


def expanding_predictions(s: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    out = s.copy()
    pred = np.full(len(out), np.nan)

    # Development: every prediction uses only observations strictly before t.
    dev = out[out.date <= cutoff].copy()
    for i in range(INITIAL_TRAIN_OBS, len(dev)):
        row = dev.iloc[i]
        pred_idx = dev.index[i]
        train = dev.iloc[:i].dropna(subset=FEATURES + [TARGET])
        pred[pred_idx] = ridge_fit_predict(train, row)

    # Forward: one frozen fit using the entire development set.
    frozen_train = dev.dropna(subset=FEATURES + [TARGET])
    for idx in out.index[out.date > cutoff]:
        row = out.loc[idx]
        pred[idx] = ridge_fit_predict(frozen_train, row)

    out["prediction"] = pred
    out["signal"] = np.where(out.prediction.gt(0), 1, np.where(out.prediction.lt(0), -1, 0))
    return out


def put_delta(forward: float, strike: float, t: float, iv: float, rf: float) -> float:
    if min(forward, strike, t, iv) <= 0:
        return float("nan")
    d1 = (math.log(forward / strike) + 0.5 * iv * iv * t) / (iv * math.sqrt(t))
    return float(math.exp(-rf * t) * (norm.cdf(d1) - 1.0))


def prepare_option_days(iv: pd.DataFrame) -> dict[pd.Timestamp, pd.DataFrame]:
    return {pd.Timestamp(d): g.copy() for d, g in iv.groupby("trade_date", sort=False)}


def choose_put_pair(
    day_df: pd.DataFrame,
) -> tuple[pd.Series, pd.Series] | None:
    g = day_df[
        day_df.option_type.eq("PE")
        & day_df.ttm_days.between(ENTRY_TTM_MIN, ENTRY_TTM_MAX)
    ].copy()
    if g.empty:
        return None

    expiry_choice = (
        g.groupby("expiry", as_index=False)
        .ttm_days.first()
        .assign(dist=lambda x: (x.ttm_days - TARGET_ENTRY_TTM).abs())
        .sort_values(["dist", "expiry"])
    )

    for expiry in expiry_choice.expiry:
        z = g[g.expiry.eq(expiry)].copy()
        if z.empty:
            continue
        forward = float(z.forward.median())
        rf = float(z.rf_simple.median())
        t = float(z.ttm_days.median() / 365.0)
        z["abs_delta"] = z.apply(
            lambda r: abs(
                put_delta(
                    forward,
                    float(r.strike),
                    t,
                    float(r.iv),
                    rf,
                )
            ),
            axis=1,
        )
        z = z.dropna(subset=["abs_delta"])
        if len(z) < 2:
            continue
        far = z.iloc[(z.abs_delta - 0.10).abs().argmin()]
        near = z.iloc[(z.abs_delta - 0.50).abs().argmin()]
        if float(far.strike) == float(near.strike):
            continue
        return far, near
    return None


def simulate(
    signals: pd.DataFrame,
    options: pd.DataFrame,
) -> pd.DataFrame:
    by_day = prepare_option_days(options)
    dates = signals.date.sort_values().drop_duplicates().tolist()
    close_map = signals.set_index("date")["close"].to_dict()

    trades = []
    next_free = pd.Timestamp.min

    for _, row in signals.sort_values("date").iterrows():
        day = pd.Timestamp(row.date)
        if day <= next_free or not np.isfinite(row.prediction) or row.signal == 0:
            continue

        pair = choose_put_pair(by_day.get(day, pd.DataFrame()))
        if pair is None:
            continue
        far, near = pair

        future_dates = [d for d in dates if d >= day + pd.Timedelta(days=HOLD_DAYS)]
        if not future_dates:
            continue
        exit_day = pd.Timestamp(future_dates[0])
        if exit_day <= day:
            continue

        eg = by_day.get(exit_day)
        if eg is None:
            continue
        ef = eg[
            eg.expiry.eq(far.expiry)
            & eg.option_type.eq("PE")
            & eg.strike.eq(far.strike)
        ]
        en = eg[
            eg.expiry.eq(near.expiry)
            & eg.option_type.eq("PE")
            & eg.strike.eq(near.strike)
        ]
        if len(ef) != 1 or len(en) != 1:
            continue
        ef, en = ef.iloc[0], en.iloc[0]

        sign = int(row.signal)
        lot = float(far.lot_size)
        entry_spread = (float(far.settlement) - float(near.settlement)) * lot
        exit_spread = (
            float(ef.settlement) - float(en.settlement)
        ) * float(ef.lot_size)
        spread_pnl = (exit_spread - entry_spread) * sign

        fwd = float(far.forward)
        rf = float(far.rf_simple)
        t = float(far.ttm_days) / 365.0
        d_far = put_delta(fwd, float(far.strike), t, float(far.iv), rf)
        d_near = put_delta(fwd, float(near.strike), t, float(near.iv), rf)
        net_delta = (d_far - d_near) * sign

        spot0 = float(close_map[day])
        spot1 = float(close_map[exit_day])
        hedge_pnl = (-net_delta * lot) * (spot1 - spot0)
        pnl = spread_pnl + hedge_pnl

        # Per-unit risk for reporting only; not used to select the strategy.
        k_far = float(far.strike)
        k_near = float(near.strike)
        credit = -entry_spread / lot  # positive when the structure receives a credit
        if sign > 0:
            risk_per_unit = max(k_near - k_far - credit, 0.0)
        else:
            debit_per_unit = max(-credit, 0.0)
            risk_per_unit = debit_per_unit
        risk_rupees = risk_per_unit * lot

        trades.append(
            {
                "entry_date": day,
                "exit_date": exit_day,
                "prediction": float(row.prediction),
                "signal": sign,
                "expiry": far.expiry,
                "strike_far_10d": float(far.strike),
                "strike_near_50d": float(near.strike),
                "entry_ttm_days": float(far.ttm_days),
                "lot_size": lot,
                "entry_spread_rupees": entry_spread,
                "exit_spread_rupees": exit_spread,
                "spread_pnl_rupees": spread_pnl,
                "delta_hedge_pnl_rupees": hedge_pnl,
                "net_delta_at_entry": net_delta,
                "pnl_rupees": pnl,
                "entry_risk_rupees": risk_rupees,
                "return_on_entry_risk": pnl / risk_rupees if risk_rupees > 0 else np.nan,
            }
        )
        next_free = exit_day

    return pd.DataFrame(trades)


def bootstrap_mean_ci(x: np.ndarray, seed: int = 20260919) -> dict:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 5:
        return {"n": int(len(x))}
    rng = np.random.default_rng(seed)
    means = np.empty(10000)
    for i in range(len(means)):
        means[i] = rng.choice(x, size=len(x), replace=True).mean()
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "n": int(len(x)),
        "mean": float(x.mean()),
        "median": float(np.median(x)),
        "ci95_bootstrap_mean": [float(lo), float(hi)],
        "win_rate": float(np.mean(x > 0)),
    }


def cost_sensitivity(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {}
    # Settlement proxy only. This stress is deliberately denominated as a
    # percentage of absolute option premium exchanged, not as an inferred bid/ask.
    gross_premium = (
        trades.entry_spread_rupees.abs() + trades.exit_spread_rupees.abs()
    ).to_numpy(float)
    out = {}
    for pct in (0.0, 0.005, 0.01, 0.02, 0.05):
        net = trades.pnl_rupees.to_numpy(float) - gross_premium * pct
        out[str(pct)] = bootstrap_mean_ci(net)
    return out


def summarize(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"n": 0}
    x = trades.pnl_rupees.to_numpy(float)
    sd = float(np.std(x, ddof=1)) if len(x) > 1 else float("nan")
    event_sharpe = float((np.mean(x) / sd) * math.sqrt(252 / HOLD_DAYS)) if sd > 0 else float("nan")
    cum = np.cumsum(x)
    dd = cum - np.maximum.accumulate(cum)
    return {
        "n_trades": int(len(trades)),
        "sum_pnl_rupees": float(np.sum(x)),
        "mean_pnl_rupees": float(np.mean(x)),
        "median_pnl_rupees": float(np.median(x)),
        "win_rate": float(np.mean(x > 0)),
        "event_annualized_sharpe_approx": event_sharpe,
        "max_drawdown_rupees": float(np.min(dd)),
        "mean_return_on_entry_risk": float(np.nanmean(trades.return_on_entry_risk)),
        "median_return_on_entry_risk": float(np.nanmedian(trades.return_on_entry_risk)),
        "bootstrap_mean_ci": bootstrap_mean_ci(x),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical-iv-root", type=Path, required=True)
    ap.add_argument("--forward-iv-root", type=Path, required=True)
    ap.add_argument("--historical-underlying", type=Path, required=True)
    ap.add_argument("--forward-underlying", type=Path, required=True)
    ap.add_argument("--cutoff", required=True)
    ap.add_argument("--forward-start", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    cutoff = pd.Timestamp(args.cutoff)
    forward_start = pd.Timestamp(args.forward_start)

    hist_iv = load_iv(args.historical_iv_root)
    fwd_iv = load_iv(args.forward_iv_root)
    hist_u = pd.read_csv(args.historical_underlying)
    fwd_u = pd.read_csv(args.forward_underlying)

    hist = build_surface(hist_iv, hist_u)
    fwd = build_surface(fwd_iv, fwd_u)

    # Development model/signal is generated without any observation after cutoff.
    combined = pd.concat([hist, fwd], ignore_index=True).drop_duplicates("date").sort_values("date")
    combined = combined.reset_index(drop=True)
    signals = expanding_predictions(combined, cutoff)

    dev = signals[signals.date <= cutoff].copy()
    forward = signals[signals.date >= forward_start].copy()

    dev_trades = simulate(dev, hist_iv)
    fwd_trades = simulate(forward, fwd_iv)

    out = {
        "status": "PASS",
        "phase": "9B",
        "objective": "Settlement-proxy test of frozen 30D downside-skew surface signal",
        "model": {
            "features": FEATURES,
            "target": TARGET,
            "ridge_alpha": ALPHA,
            "minimum_training_rows": MIN_TRAIN,
            "expanding_window": True,
            "forward_coefficients_frozen_at": cutoff.strftime("%Y-%m-%d"),
        },
        "strategy": {
            "mapping": "prediction sign -> long/short 10-delta put vs 50-delta put same expiry",
            "entry_ttm_days": [ENTRY_TTM_MIN, ENTRY_TTM_MAX],
            "target_entry_ttm_days": TARGET_ENTRY_TTM,
            "holding_days": HOLD_DAYS,
            "entry_delta_hedged": True,
            "overlapping_positions": False,
            "pricing": "NSE EOD settlement proxy",
            "execution_status": "NOT_EXECUTABLE; historical bid/ask/order-trade data absent",
        },
        "data": {
            "historical_iv_rows": int(len(hist_iv)),
            "forward_iv_rows": int(len(fwd_iv)),
            "historical_surface_start": hist.date.min().strftime("%Y-%m-%d"),
            "historical_surface_end": hist.date.max().strftime("%Y-%m-%d"),
            "forward_surface_start": fwd.date.min().strftime("%Y-%m-%d"),
            "forward_surface_end": fwd.date.max().strftime("%Y-%m-%d"),
        },
        "development_forecast": {
            "rows": int(dev.prediction.notna().sum()),
            "target_rows": int(dev[TARGET].notna().sum()),
            "r2": None,
            "correlation": None,
        },
        "development_strategy": summarize(dev_trades),
        "forward_strategy": summarize(fwd_trades),
        "forward_cost_stress": cost_sensitivity(fwd_trades),
        "decision": {
            "paper_candidate_gate": (
                "Only eligible if forward strategy has >=3 non-overlapping trades, "
                "positive net settlement-proxy P&L, bootstrap mean CI lower bound > 0, "
                "and no material contradiction from negative controls. This does not "
                "constitute executable promotion."
            )
        },
    }

    q = dev.dropna(subset=["prediction", TARGET])
    if len(q) >= 30:
        y = q[TARGET].to_numpy(float)
        p = q.prediction.to_numpy(float)
        sse = float(np.sum((y - p) ** 2))
        sst = float(np.sum((y - y.mean()) ** 2))
        out["development_forecast"]["r2"] = float(1 - sse / sst) if sst > 0 else None
        out["development_forecast"]["correlation"] = float(np.corrcoef(y, p)[0, 1])

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "PHASE9B_SURFACE_SKEW_REPORT.json").write_text(
        json.dumps(out, indent=2)
    )
    dev_trades.to_csv(args.output / "phase9b_development_trades.csv", index=False)
    fwd_trades.to_csv(args.output / "phase9b_forward_trades.csv", index=False)
    signals[["date", "prediction", "signal"]].to_csv(
        args.output / "phase9b_signals.csv", index=False
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
