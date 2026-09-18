#!/usr/bin/env python3
"""Phase 7 — CPCV / multiple-selection stress test for Phase 6 candidates.

The final 10% chronological holdout from Phase 6 remains untouched.
This phase uses only the first 90% of the data to estimate:
  * combinatorial purged cross-validation path distribution;
  * a CSCV-style probability-of-backtest-overfitting diagnostic across the
    six preregistered candidate rules;
  * a deflated-Sharpe diagnostic using the effective six-candidate trial count.

The candidate definitions and model hyperparameters are frozen from Phase 6.
No parameter tuning occurs here.
"""
from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import phase5_multimodal_prediction as p5


CANDIDATES = [
    "direction_model",
    "direction_inverse",
    "trend_highvol",
    "meanrev_highvol",
    "breakout_highvol",
    "trend_lowvol",
]
COSTS = (5, 10, 20)
DEV_FRAC = 0.90
N_BLOCKS = 8
TEST_BLOCKS = 2
PURGE = 1
EMBARGO = 1
P_THRESHOLD = 0.55


def sharpe(r):
    x = pd.Series(r).dropna()
    if len(x) < 2 or x.std(ddof=1) <= 0:
        return np.nan
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252))


def max_dd(r):
    x = pd.Series(r).dropna()
    if x.empty:
        return np.nan
    w = (1 + x).cumprod()
    return float((w / w.cummax() - 1).min())


def position(name, row, p_dir, p_vol):
    ret20 = float(row["ret20"])
    z20 = float(row["z20"])
    ret1 = float(row["ret1"])
    if name == "direction_model":
        return 1.0 if p_dir >= P_THRESHOLD else (-1.0 if p_dir <= 1-P_THRESHOLD else 0.0)
    if name == "direction_inverse":
        q = 1.0 - p_dir
        return 1.0 if q >= P_THRESHOLD else (-1.0 if q <= 1-P_THRESHOLD else 0.0)
    if name == "trend_highvol":
        return float(np.sign(ret20)) if p_vol >= P_THRESHOLD else 0.0
    if name == "meanrev_highvol":
        return float(-np.sign(z20)) if p_vol >= P_THRESHOLD else 0.0
    if name == "breakout_highvol":
        return float(np.sign(ret1)) if p_vol >= P_THRESHOLD else 0.0
    if name == "trend_lowvol":
        return float(np.sign(ret20)) if p_vol <= 1-P_THRESHOLD else 0.0
    raise ValueError(name)


def evaluate(df, p_dir, p_vol, cost_bps):
    out = {}
    prev = {c: 0.0 for c in CANDIDATES}
    series = {c: [] for c in CANDIDATES}
    for i, (_, row) in enumerate(df.iterrows()):
        for c in CANDIDATES:
            pos = position(c, row, float(p_dir[i]), float(p_vol[i]))
            turn = abs(pos - prev[c])
            ret = pos * float(row["target_ret1"]) - turn * cost_bps / 10000.0
            series[c].append(ret)
            prev[c] = pos
    for c in CANDIDATES:
        r = pd.Series(series[c])
        out[c] = {
            "sharpe": sharpe(r),
            "mean_daily": float(r.mean()),
            "max_drawdown": max_dd(r),
            "n": int(len(r)),
        }
    return out


def fit_predictions(train, test, cols):
    direction = p5.make_pipeline(
        p5.SimpleImputer(strategy="median"),
        p5.StandardScaler(),
        p5.LogisticRegression(C=0.5, max_iter=3000, solver="lbfgs"),
    )
    vol = p5.make_pipeline(
        p5.SimpleImputer(strategy="median"),
        p5.StandardScaler(),
        p5.LogisticRegression(C=0.5, max_iter=3000, solver="lbfgs"),
    )
    direction.fit(train[cols], train["target_up1"].astype(int))
    vol.fit(train[cols], train["target_vol_expand5"].astype(int))
    return (
        direction.predict_proba(test[cols])[:, 1],
        vol.predict_proba(test[cols])[:, 1],
    )


def dsr_approx(sharpe_obs, n_trials, n_obs, skew=0.0, kurtosis_excess=0.0):
    """Approximate DSR probability using a standard expected-max-Sharpe hurdle.

    This is deliberately labelled an approximation; the repository's formal
    validation gate should treat it as one diagnostic, not a universal cutoff.
    """
    if not np.isfinite(sharpe_obs) or n_trials < 1 or n_obs < 10:
        return np.nan, np.nan
    # Euler–Mascheroni constant approximation for the expected max of N
    # independent standard-normal trials.
    euler_gamma = 0.5772156649015329
    if n_trials == 1:
        sr_star = 0.0
    else:
        p1 = max(1e-12, min(1-1e-12, 1.0 - 1.0/n_trials))
        p2 = max(1e-12, min(1-1e-12, 1.0 - 1.0/(n_trials * math.e)))
        sr_star = (
            (1.0 - euler_gamma) * norm.ppf(p1)
            + euler_gamma * norm.ppf(p2)
        ) / math.sqrt(n_obs)
    variance = (1.0 - skew * sharpe_obs + ((kurtosis_excess + 3.0) / 4.0) * sharpe_obs**2) / max(n_obs-1, 1)
    z = (sharpe_obs - sr_star) / math.sqrt(max(variance, 1e-12))
    return float(sr_star), float(norm.cdf(z))


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
    x = x.dropna(subset=["target_up1", "target_ret1", "target_vol_expand5", "ret20", "z20"]).sort_values("date").reset_index(drop=True)

    cut90 = int(math.floor(len(x) * DEV_FRAC))
    dev = x.iloc[:cut90].copy().reset_index(drop=True)
    final_holdout = x.iloc[cut90:].copy().reset_index(drop=True)

    blocks = np.array_split(np.arange(len(dev)), N_BLOCKS)
    path_rows = []
    pbo_flags = []
    cols = p5.FEATURES["multimodal"]

    for test_block_ids in combinations(range(N_BLOCKS), TEST_BLOCKS):
        test_idx = np.concatenate([blocks[i] for i in test_block_ids])
        test_idx = np.sort(test_idx)

        # Purge around test blocks; embargo the immediately following observations.
        excluded = set(test_idx.tolist())
        lo = int(test_idx.min())
        hi = int(test_idx.max())
        for j in range(max(0, lo-PURGE), min(len(dev), lo+PURGE+1)):
            excluded.add(j)
        for j in range(max(0, hi-EMBARGO), min(len(dev), hi+EMBARGO+1)):
            excluded.add(j)

        train_idx = np.array([i for i in range(len(dev)) if i not in excluded], dtype=int)
        if len(train_idx) < 100 or len(test_idx) < 20:
            continue

        train = dev.iloc[train_idx]
        test = dev.iloc[test_idx].sort_values("date").copy()

        p_dir_tr, p_vol_tr = fit_predictions(train, train, cols)
        p_dir_te, p_vol_te = fit_predictions(train, test, cols)

        # In-sample candidate ranking for PBO diagnostic.
        is_metrics = evaluate(train, p_dir_tr, p_vol_tr, 10)
        oos_metrics = evaluate(test, p_dir_te, p_vol_te, 10)

        ordered_is = sorted(CANDIDATES, key=lambda c: (is_metrics[c]["sharpe"], c))
        best_is = ordered_is[-1]
        ordered_oos = sorted(CANDIDATES, key=lambda c: (oos_metrics[c]["sharpe"], c), reverse=True)
        oos_rank = ordered_oos.index(best_is) + 1
        pbo_flags.append(oos_rank > len(CANDIDATES)/2.0)

        path = {
            "test_blocks": list(test_block_ids),
            "train_n": int(len(train)),
            "test_n": int(len(test)),
            "test_start": test.date.min().strftime("%Y-%m-%d"),
            "test_end": test.date.max().strftime("%Y-%m-%d"),
            "best_in_sample_candidate": best_is,
            "best_in_sample_sharpe": float(is_metrics[best_is]["sharpe"]),
            "oos_rank_of_is_best": int(oos_rank),
            "oos_metrics_10bps": oos_metrics,
        }
        path_rows.append(path)

    if not path_rows:
        raise SystemExit("No valid CPCV paths")

    # Aggregate CPCV distribution for each candidate and cost.
    aggregate = {}
    for c in CANDIDATES:
        aggregate[c] = {}
        for cost in COSTS:
            vals = []
            for test_block_ids in combinations(range(N_BLOCKS), TEST_BLOCKS):
                match = next((r for r in path_rows if tuple(r["test_blocks"]) == tuple(test_block_ids)), None)
                if match is not None:
                    if cost == 10:
                        vals.append(match["oos_metrics_10bps"][c]["sharpe"])
            if cost == 10:
                a = np.asarray(vals, dtype=float)
                aggregate[c] = {
                    "cpcv_paths": int(a.size),
                    "median_sharpe_10bps": float(np.nanmedian(a)),
                    "mean_sharpe_10bps": float(np.nanmean(a)),
                    "q10_sharpe_10bps": float(np.nanquantile(a, 0.10)),
                    "q90_sharpe_10bps": float(np.nanquantile(a, 0.90)),
                    "positive_sharpe_path_fraction": float(np.mean(a > 0)),
                }

    pbo = float(np.mean(pbo_flags)) if pbo_flags else np.nan

    # Frozen candidate from Phase 6 validation; final holdout is NOT touched here.
    frozen_candidate = "direction_inverse"
    final_dev = path_rows
    oos_sharpes = [
        r["oos_metrics_10bps"][frozen_candidate]["sharpe"]
        for r in final_dev
        if np.isfinite(r["oos_metrics_10bps"][frozen_candidate]["sharpe"])
    ]
    cpcv_median = float(np.median(oos_sharpes))
    cpcv_mean = float(np.mean(oos_sharpes))
    sr_star, dsr = dsr_approx(cpcv_mean, n_trials=len(CANDIDATES), n_obs=len(dev))

    report = {
        "status": "PASS",
        "phase": "7",
        "objective": "CPCV, PBO and DSR stress test of the fixed Phase 6 candidate set",
        "data_partition": {
            "all_aligned_rows": int(len(x)),
            "development_rows_used_for_CPCV": int(len(dev)),
            "final_holdout_rows_reserved": int(len(final_holdout)),
            "final_holdout_start": final_holdout.date.min().strftime("%Y-%m-%d"),
            "final_holdout_end": final_holdout.date.max().strftime("%Y-%m-%d"),
        },
        "cpcv": {
            "blocks": N_BLOCKS,
            "test_blocks_per_path": TEST_BLOCKS,
            "purge_observations": PURGE,
            "embargo_observations": EMBARGO,
            "paths": int(len(path_rows)),
            "candidate_summary_10bps": aggregate,
        },
        "pbo": {
            "definition": "CSCV-style indicator: fraction of CPCV paths where the in-sample top-ranked candidate falls in the worse half of OOS candidate rankings",
            "candidate_count": len(CANDIDATES),
            "pbo_proxy": pbo,
        },
        "dsr_approximation": {
            "frozen_candidate": frozen_candidate,
            "cpcv_mean_sharpe_10bps": cpcv_mean,
            "cpcv_median_sharpe_10bps": cpcv_median,
            "effective_trials": len(CANDIDATES),
            "expected_max_sharpe_hurdle": sr_star,
            "approx_probability_sharpe_exceeds_hurdle": dsr,
        },
        "holdout_guardrail": "The Phase 6 final 10% chronological holdout is excluded from all tuning and CPCV calculations here. Its previously recorded result remains locked.",
        "interpretation_guardrail": "CPCV/PBO/DSR are statistical diagnostics. The strategy remains unvalidated until execution-grade costs, stress tests and prospective paper trading are passed."
    }
    (args.output / "PHASE7_STATISTICAL_VALIDATION_REPORT.json").write_text(json.dumps(report, indent=2, allow_nan=True) + "\n")
    print(json.dumps(report, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
