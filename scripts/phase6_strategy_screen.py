#!/usr/bin/env python3
"""Phase 6: translate predictive states into pre-specified strategy candidates.

This phase creates a NEW final holdout: first 80% development, next 10%
validation for selecting among a frozen candidate set, final 10% untouched.
The candidate set is fixed in code and thresholds are not tuned on the final
holdout.

Strategies combine the Phase 5 predictive outputs with simple, transparent
NIFTY rules. Returns are close-to-close settlement proxies; costs are
sensitivity assumptions, not observed fills.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase5_multimodal_prediction as p5  # noqa: E402


COSTS = (5, 10, 20)
P_THRESHOLD = 0.55
TRAIN_FRAC = 0.80
VALID_FRAC = 0.10


def metrics(r):
    r = pd.Series(r).dropna()
    if len(r) < 20:
        return {"n": int(len(r))}
    vol = float(r.std(ddof=1))
    sharpe = float(r.mean() / vol * np.sqrt(252)) if vol > 0 else np.nan
    wealth = (1 + r).cumprod()
    dd = float((wealth / wealth.cummax() - 1).min())
    return {
        "n": int(len(r)),
        "mean_daily": float(r.mean()),
        "ann_vol": float(vol * np.sqrt(252)),
        "sharpe": sharpe,
        "max_drawdown": dd,
        "positive_fraction": float((r > 0).mean()),
    }


def candidate_position(name, row, p_dir, p_vol):
    ret20 = float(row["ret20"])
    z20 = float(row["z20"])
    ret1 = float(row["ret1"])
    if name == "direction_model":
        return 1.0 if p_dir >= P_THRESHOLD else (-1.0 if p_dir <= 1 - P_THRESHOLD else 0.0)
    if name == "direction_inverse":
        q = 1.0 - p_dir
        return 1.0 if q >= P_THRESHOLD else (-1.0 if q <= 1 - P_THRESHOLD else 0.0)
    if name == "trend_highvol":
        return float(np.sign(ret20)) if p_vol >= P_THRESHOLD else 0.0
    if name == "meanrev_highvol":
        return float(-np.sign(z20)) if p_vol >= P_THRESHOLD else 0.0
    if name == "breakout_highvol":
        return float(np.sign(ret1)) if p_vol >= P_THRESHOLD else 0.0
    if name == "trend_lowvol":
        return float(np.sign(ret20)) if p_vol <= 1 - P_THRESHOLD else 0.0
    raise ValueError(name)


CANDIDATES = [
    "direction_model",
    "direction_inverse",
    "trend_highvol",
    "meanrev_highvol",
    "breakout_highvol",
    "trend_lowvol",
]


def evaluate_candidates(df, p_dir, p_vol, cost_bps):
    out = {}
    for name in CANDIDATES:
        rows = []
        prev = 0.0
        for idx, row in df.reset_index(drop=True).iterrows():
            pos = candidate_position(name, row, float(p_dir[idx]), float(p_vol[idx]))
            turnover = abs(pos - prev)
            gross = pos * float(row["target_ret1"])
            net = gross - turnover * cost_bps / 10000.0
            rows.append((pos, turnover, gross, net))
            prev = pos
        z = pd.DataFrame(rows, columns=["position", "turnover", "gross", "net"])
        m = metrics(z["net"])
        m.update({
            "candidate": name,
            "cost_bps_per_side": cost_bps,
            "trade_day_fraction": float((z.position != 0).mean()),
            "trades": int((z.turnover > 0).sum()),
            "mean_gross_daily": float(z.gross.mean()),
            "mean_cost_daily": float((z.gross - z.net).mean()),
        })
        out[name] = m
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iv-root", type=Path, required=True)
    ap.add_argument("--underlying", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    u = p5.load_underlying(args.underlying)
    iv = p5.load_iv(args.iv_root)
    surface = p5.build_surface(iv)
    x = p5.build_features(u, surface)
    x = x.dropna(subset=["target_up1", "target_ret1", "ret20", "z20"]).sort_values("date").reset_index(drop=True)

    n = len(x)
    train_end = int(math.floor(n * TRAIN_FRAC))
    val_end = int(math.floor(n * (TRAIN_FRAC + VALID_FRAC)))
    train = x.iloc[:train_end].copy()
    val = x.iloc[train_end:val_end].copy()
    final = x.iloc[val_end:].copy()
    if len(train) < 200 or len(val) < 50 or len(final) < 50:
        raise SystemExit(f"Insufficient three-way sample: {n}, train={len(train)}, val={len(val)}, final={len(final)}")

    cols = p5.FEATURES["multimodal"]

    # Fixed Phase-5 model specification.
    direction_pipe = p5.make_pipeline(
        p5.SimpleImputer(strategy="median"),
        p5.StandardScaler(),
        p5.LogisticRegression(C=0.5, max_iter=3000, solver="lbfgs"),
    )
    vol_pipe = p5.make_pipeline(
        p5.SimpleImputer(strategy="median"),
        p5.StandardScaler(),
        p5.LogisticRegression(C=0.5, max_iter=3000, solver="lbfgs"),
    )
    direction_pipe.fit(train[cols], train["target_up1"].astype(int))
    vol_pipe.fit(train[cols], train["target_vol_expand5"].astype(int))

    p_dir_val = direction_pipe.predict_proba(val[cols])[:, 1]
    p_vol_val = vol_pipe.predict_proba(val[cols])[:, 1]
    val_metrics = evaluate_candidates(val, p_dir_val, p_vol_val, 10)
    # Select only on the validation block. Ties break by candidate declaration order.
    selected = max(CANDIDATES, key=lambda name: (val_metrics[name]["sharpe"], -CANDIDATES.index(name)))

    # Refit the same frozen model on train+validation; final block is untouched.
    dev = pd.concat([train, val], ignore_index=True)
    direction_pipe.fit(dev[cols], dev["target_up1"].astype(int))
    vol_pipe.fit(dev[cols], dev["target_vol_expand5"].astype(int))
    p_dir_final = direction_pipe.predict_proba(final[cols])[:, 1]
    p_vol_final = vol_pipe.predict_proba(final[cols])[:, 1]

    final_metrics = evaluate_candidates(final, p_dir_final, p_vol_final, 10)
    final_cost_sensitivity = {
        str(c): evaluate_candidates(final, p_dir_final, p_vol_final, c)[selected]
        for c in COSTS
    }

    report = {
        "status": "PASS",
        "phase": "6",
        "objective": "strategy translation from predictive state signals",
        "split": {
            "development_train_fraction": TRAIN_FRAC,
            "validation_fraction": VALID_FRAC,
            "final_holdout_fraction": 1.0 - TRAIN_FRAC - VALID_FRAC,
            "train_end": train.date.max().strftime("%Y-%m-%d"),
            "validation_start": val.date.min().strftime("%Y-%m-%d"),
            "validation_end": val.date.max().strftime("%Y-%m-%d"),
            "final_holdout_start": final.date.min().strftime("%Y-%m-%d"),
            "final_holdout_end": final.date.max().strftime("%Y-%m-%d"),
            "final_holdout_n": int(len(final)),
        },
        "fixed_model_spec": {
            "features": cols,
            "logistic_C": 0.5,
            "threshold": P_THRESHOLD,
        },
        "candidate_set": CANDIDATES,
        "validation_selection": {
            "selection_cost_bps_per_side": 10,
            "selected_candidate": selected,
            "candidate_metrics": val_metrics,
        },
        "final_holdout": {
            "all_candidate_metrics_at_10bps": final_metrics,
            "selected_candidate_cost_sensitivity": final_cost_sensitivity,
        },
        "interpretation_guardrail": (
            "The final holdout is evaluated only after the candidate set and "
            "selection rule are frozen. Returns are close-to-close NIFTY proxies, "
            "not live fills; costs are sensitivity assumptions rather than "
            "observed bid/ask/slippage."
        ),
    }
    (args.output / "PHASE6_STRATEGY_SCREEN_REPORT.json").write_text(json.dumps(report, indent=2, allow_nan=True) + "\n")
    print(json.dumps(report, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
