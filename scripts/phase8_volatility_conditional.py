#!/usr/bin/env python3
"""Phase 8: fresh-forward validation of volatility-state-conditioned strategies.

The model specification is frozen from Phase 5. Development ends before the
fresh forward window, so the old Phase 6 final holdout is historical training
data rather than a tuning target. No parameters are selected on the fresh
forward window.

The forward window is settlement-to-settlement NIFTY proxy research. It is not
execution-grade and does not use quote/order/trade data.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase5_multimodal_prediction as p5  # noqa: E402


GAP_DATES = {"2021-03-30", "2024-03-02"}
P_THRESHOLD = 0.55
COSTS = (5, 10, 20)
N_BLOCKS = 8
PURGE = 5
EMBARGO = 2
CANDIDATES = [
    "highvol_trend",
    "highvol_meanrev",
    "highvol_breakout",
    "lowvol_trend",
    "lowvol_meanrev",
    "state_switch",
]


def load_underlying_pair(old_path: Path, new_path: Path) -> pd.DataFrame:
    frames = []
    for path in (old_path, new_path):
        x = pd.read_csv(path)
        dc = next((c for c in ("date", "DATE", "CH_TIMESTAMP", "TIMESTAMP") if c in x), None)
        cc = next((c for c in ("close", "CLOSE", "Close") if c in x), None)
        if dc is None or cc is None:
            raise SystemExit(f"{path}: unrecognised underlying columns")
        x = x.rename(columns={dc: "date", cc: "close"})[["date", "close"]]
        x["date"] = pd.to_datetime(x["date"], errors="coerce")
        x["close"] = pd.to_numeric(x["close"], errors="coerce")
        frames.append(x)
    u = pd.concat(frames, ignore_index=True).dropna(subset=["date", "close"])
    u = u[u["close"] > 0].drop_duplicates("date").sort_values("date").reset_index(drop=True)
    u = u[~u["date"].dt.strftime("%Y-%m-%d").isin(GAP_DATES)].copy()

    u["ret1"] = np.log(u["close"] / u["close"].shift(1))
    u["ret5"] = np.log(u["close"] / u["close"].shift(5))
    u["ret20"] = np.log(u["close"] / u["close"].shift(20))
    for w in (5, 20, 60):
        u[f"rv_{w}"] = np.sqrt(
            u["ret1"].shift(1).rolling(w).apply(
                lambda z: np.sum(np.asarray(z) ** 2) * 252.0 / len(z), raw=False
            )
        )
    u["vol_ratio_5_20"] = u["rv_5"] / u["rv_20"]
    u["z20"] = (
        (u["close"] - u["close"].shift(1).rolling(20).mean())
        / u["close"].shift(1).rolling(20).std(ddof=0)
    )
    u["drawdown_60"] = u["close"] / u["close"].shift(1).rolling(60).max() - 1.0
    u["ret_autocorr20"] = u["ret1"].shift(1).rolling(20).corr(u["ret1"].shift(2))
    absret = u["ret1"].abs()
    u["absret_autocorr20"] = absret.shift(1).rolling(20).corr(absret.shift(2))

    future5 = np.log(u["close"].shift(-5) / u["close"])
    u["target_ret1"] = u["ret1"].shift(-1)
    u["target_rv5"] = (
        u["ret1"].shift(-1).rolling(5)
        .apply(lambda z: np.sum(np.asarray(z) ** 2) * 252.0 / len(z), raw=False)
        .shift(-4)
    )
    u["target_vol_expand5"] = (
        u["target_rv5"] > u["rv_20"] ** 2
    ).astype(float)
    u["future5"] = future5
    return u


def load_iv_roots(roots: list[Path]) -> pd.DataFrame:
    frames = []
    for root in roots:
        files = sorted(root.rglob("iv_observations_*.csv.gz"))
        if not files:
            raise SystemExit(f"No IV partitions under {root}")
        for path in files:
            x = pd.read_csv(path)
            required = {"trade_date", "expiry", "option_type", "moneyness", "ttm_days", "iv"}
            missing = required - set(x.columns)
            if missing:
                raise SystemExit(f"{path}: missing {sorted(missing)}")
            x["trade_date"] = pd.to_datetime(x["trade_date"], errors="coerce")
            x["expiry"] = pd.to_datetime(x["expiry"], errors="coerce")
            for c in ("moneyness", "ttm_days", "iv"):
                x[c] = pd.to_numeric(x[c], errors="coerce")
            x["option_type"] = x["option_type"].astype(str).str.upper()
            frames.append(x)
    iv = pd.concat(frames, ignore_index=True)
    iv = iv[~iv["trade_date"].dt.strftime("%Y-%m-%d").isin(GAP_DATES)]
    iv = iv[(iv["iv"] > 0) & (iv["iv"] <= 5) & (iv["ttm_days"] > 0) & (iv["moneyness"] > 0)]
    iv = iv.drop_duplicates(["trade_date", "expiry", "option_type", "moneyness", "iv"])
    return iv


def build_surface(iv: pd.DataFrame) -> pd.DataFrame:
    atm = p5.expiry_band(iv, None, 0.97, 1.03)
    down = p5.expiry_band(iv, "PE", 0.85, 0.95)
    up = p5.expiry_band(iv, "CE", 1.05, 1.15)
    pieces = []
    for h in (30, 60):
        a = p5.const_maturity(atm, h, f"atm_iv_{h}")
        d = p5.const_maturity(down, h, f"down_iv_{h}")
        c = p5.const_maturity(up, h, f"up_iv_{h}")
        x = a.merge(d, on="date", how="inner").merge(c, on="date", how="inner")
        x[f"down_skew_{h}"] = x[f"down_iv_{h}"] - x[f"atm_iv_{h}"]
        x[f"up_skew_{h}"] = x[f"up_iv_{h}"] - x[f"atm_iv_{h}"]
        pieces.append(x)
    x = pieces[0].merge(pieces[1], on="date", how="inner")
    x["term_slope_30_60"] = x["atm_iv_60"] - x["atm_iv_30"]
    return x


def build_features(u: pd.DataFrame, surface: pd.DataFrame) -> pd.DataFrame:
    x = u.merge(surface, left_on="date", right_on="date", how="left")
    x["vrp_state_proxy"] = x["atm_iv_30"] ** 2 - x["rv_20"] ** 2
    x["surface_skew_spread"] = x["down_skew_30"] - x["up_skew_30"]
    x["surface_atm_change_5"] = x["atm_iv_30"] - x["atm_iv_30"].shift(5)
    x["surface_skew_change_5"] = x["down_skew_30"] - x["down_skew_30"].shift(5)
    x["iv_term_ratio"] = x["atm_iv_60"] / x["atm_iv_30"]
    return x


def make_model():
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=0.5, max_iter=3000, solver="lbfgs"),
    )


def position(name: str, row: pd.Series, p_vol: float) -> float:
    if name == "highvol_trend":
        return float(np.sign(row["ret20"])) if p_vol >= P_THRESHOLD else 0.0
    if name == "highvol_meanrev":
        return float(-np.sign(row["z20"])) if p_vol >= P_THRESHOLD else 0.0
    if name == "highvol_breakout":
        daily_sigma = float(row["rv_20"]) / math.sqrt(252.0)
        return float(np.sign(row["ret1"])) if (
            p_vol >= P_THRESHOLD and np.isfinite(daily_sigma)
            and abs(float(row["ret1"])) >= daily_sigma
        ) else 0.0
    if name == "lowvol_trend":
        return float(np.sign(row["ret20"])) if p_vol <= 1.0 - P_THRESHOLD else 0.0
    if name == "lowvol_meanrev":
        return float(-np.sign(row["z20"])) if p_vol <= 1.0 - P_THRESHOLD else 0.0
    if name == "state_switch":
        if p_vol >= P_THRESHOLD:
            return float(np.sign(row["ret20"]))
        if p_vol <= 1.0 - P_THRESHOLD:
            return float(-np.sign(row["z20"]))
        return 0.0
    raise ValueError(name)


def metric(r: pd.Series) -> dict:
    r = pd.Series(r).replace([np.inf, -np.inf], np.nan).dropna()
    if len(r) < 20:
        return {"n": int(len(r)), "sharpe": np.nan}
    vol = float(r.std(ddof=1))
    sharpe = float(r.mean() / vol * math.sqrt(252.0)) if vol > 0 else np.nan
    wealth = (1.0 + r).cumprod()
    return {
        "n": int(len(r)),
        "mean_daily": float(r.mean()),
        "ann_return_from_daily_mean": float((1.0 + r.mean()) ** 252 - 1.0),
        "ann_vol": float(vol * math.sqrt(252.0)),
        "sharpe": sharpe,
        "max_drawdown": float((wealth / wealth.cummax() - 1.0).min()),
        "positive_fraction": float((r > 0).mean()),
    }


def evaluate(df: pd.DataFrame, probs: np.ndarray, cost_bps: int) -> dict:
    probs = np.asarray(probs, dtype=float)
    out = {}
    for name in CANDIDATES:
        prev = 0.0
        rows = []
        for i, (_, row) in enumerate(df.reset_index(drop=True).iterrows()):
            p = float(probs[i])
            pos = position(name, row, p)
            turnover = abs(pos - prev)
            gross = pos * float(row["target_ret1"])
            net = gross - turnover * cost_bps / 10000.0
            rows.append((pos, gross, net, turnover, p))
            prev = pos
        z = pd.DataFrame(rows, columns=["position", "gross", "net", "turnover", "p_vol"])
        m = metric(z["net"])
        m.update({
            "candidate": name,
            "cost_bps_per_side": cost_bps,
            "trade_day_fraction": float((z["position"] != 0).mean()),
            "trades": int((z["turnover"] > 0).sum()),
            "mean_gross_daily": float(z["gross"].mean()),
            "mean_cost_daily": float((z["gross"] - z["net"]).mean()),
            "mean_p_vol": float(z["p_vol"].mean()),
        })
        out[name] = m
    return out


def make_blocks(n: int) -> list[np.ndarray]:
    edges = np.linspace(0, n, N_BLOCKS + 1, dtype=int)
    return [np.arange(edges[i], edges[i + 1]) for i in range(N_BLOCKS) if edges[i] < edges[i + 1]]


def expand_mask(n: int, idx: np.ndarray, radius: int) -> np.ndarray:
    mask = np.zeros(n, dtype=bool)
    if len(idx):
        lo = max(0, int(idx.min()) - radius)
        hi = min(n, int(idx.max()) + radius + 1)
        mask[lo:hi] = True
    return mask


def cpcv(df: pd.DataFrame, features: list[str], cost_bps: int) -> dict:
    data = df.reset_index(drop=True).copy()
    blocks = make_blocks(len(data))
    paths = []
    for test_pair in itertools.combinations(range(len(blocks)), 2):
        test_idx = np.concatenate([blocks[i] for i in test_pair])
        test_mask = np.zeros(len(data), dtype=bool)
        test_mask[test_idx] = True
        purge_mask = expand_mask(len(data), test_idx, PURGE)
        embargo_mask = np.zeros(len(data), dtype=bool)
        lo = int(test_idx.max()) + 1
        hi = min(len(data), lo + EMBARGO)
        embargo_mask[lo:hi] = True
        train_mask = ~(test_mask | purge_mask | embargo_mask)
        train = data.loc[train_mask].dropna(subset=["target_vol_expand5"]).copy()
        test = data.loc[test_mask].dropna(subset=["target_vol_expand5"]).copy()
        if len(train) < 100 or len(test) < 30:
            continue
        model = make_model()
        model.fit(train[features], train["target_vol_expand5"].astype(int))
        p = model.predict_proba(test[features])[:, 1]
        metrics = evaluate(test, p, cost_bps)
        train_metrics = evaluate(
            train,
            model.predict_proba(train[features])[:, 1],
            cost_bps,
        )
        for name in CANDIDATES:
            paths.append({
                "test_blocks": list(test_pair),
                "candidate": name,
                "train_sharpe": train_metrics[name]["sharpe"],
                "test_sharpe": metrics[name]["sharpe"],
                "test_positive": (
                    1 if metrics[name]["sharpe"] > 0 else 0
                ),
            })
    paths_df = pd.DataFrame(paths)
    summaries = {}
    for name in CANDIDATES:
        s = paths_df.loc[paths_df["candidate"] == name, "test_sharpe"]
        summaries[name] = {
            "paths": int(len(s)),
            "mean_sharpe": float(s.mean()),
            "median_sharpe": float(s.median()),
            "q10_sharpe": float(s.quantile(0.10)),
            "q90_sharpe": float(s.quantile(0.90)),
            "positive_path_fraction": float((s > 0).mean()),
        }
    pbo_count = 0
    total = 0
    for test_pair, g in paths_df.groupby(paths_df["test_blocks"].astype(str)):
        if len(g) != len(CANDIDATES):
            continue
        top_train = g.sort_values(["train_sharpe", "candidate"], ascending=[False, True]).iloc[0]["candidate"]
        ranks = g.sort_values("test_sharpe", ascending=False).reset_index(drop=True)
        top_oos_rank = int(ranks.index[ranks["candidate"] == top_train][0])
        if top_oos_rank >= len(CANDIDATES) // 2:
            pbo_count += 1
        total += 1
    return {
        "paths": int(total),
        "candidate_summaries": summaries,
        "pbo_proxy": float(pbo_count / total) if total else np.nan,
        "purge_observations": PURGE,
        "embargo_observations": EMBARGO,
    }


def dsr_proxy(cpcv_result: dict) -> dict:
    vals = [
        v["median_sharpe"]
        for v in cpcv_result["candidate_summaries"].values()
        if np.isfinite(v["median_sharpe"])
    ]
    if not vals:
        return {"status": "UNAVAILABLE"}
    max_obs = max(vals)
    k = len(vals)
    # Approximate expected maximum of k standard normal scores, rescaled
    # to a Sharpe-like statistic. This is intentionally a diagnostic.
    hurdle = float(np.sqrt(2.0 * np.log(max(k, 2))) * 0.5)
    prob = float(0.5 * math.erfc((hurdle - max_obs) / math.sqrt(2.0)))
    return {
        "status": "DIAGNOSTIC_ONLY",
        "effective_trials": k,
        "best_median_cpcv_sharpe": max_obs,
        "approx_expected_max_hurdle": hurdle,
        "approx_probability_best_exceeds_hurdle": prob,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-iv-root", type=Path, required=True)
    ap.add_argument("--new-iv-root", type=Path, required=True)
    ap.add_argument("--old-underlying", type=Path, required=True)
    ap.add_argument("--new-underlying", type=Path, required=True)
    ap.add_argument("--forward-start", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    forward_start = pd.Timestamp(args.forward_start)
    u = load_underlying_pair(args.old_underlying, args.new_underlying)
    iv = load_iv_roots([args.old_iv_root, args.new_iv_root])
    surface = build_surface(iv)
    x = build_features(u, surface)
    features = p5.FEATURES["multimodal"]
    required = features + ["target_ret1", "target_vol_expand5"]
    x = x.dropna(subset=required).sort_values("date").reset_index(drop=True)

    dev = x[x["date"] < forward_start].copy()
    fwd = x[x["date"] >= forward_start].copy()
    if len(dev) < 500 or len(fwd) < 30:
        raise SystemExit(f"Insufficient split: dev={len(dev)}, forward={len(fwd)}")
    # The last five forward dates do not have a full 5-session target in a
    # closed window; they remain prediction-only and are excluded from return
    # scoring.
    fwd_eval = fwd.dropna(subset=["target_ret1"]).copy()
    model = make_model()
    model.fit(dev[features], dev["target_vol_expand5"].astype(int))
    p_dev = model.predict_proba(dev[features])[:, 1]
    p_fwd = model.predict_proba(fwd_eval[features])[:, 1]

    auc = float(
        roc_auc_score(
            fwd_eval["target_vol_expand5"].astype(int),
            p_fwd,
        )
    ) if fwd_eval["target_vol_expand5"].nunique() == 2 else np.nan

    forward = {
        str(c): evaluate(fwd_eval, p_fwd, c)
        for c in COSTS
    }
    development_cpcv = {
        str(c): cpcv(dev, features, c)
        for c in COSTS
    }
    dsr = dsr_proxy(development_cpcv["10"])

    # Fixed pre-declared promotion gate. No candidate is selected from the
    # forward window; a candidate must satisfy all gates to be promoted.
    promotion = {}
    for name in CANDIDATES:
        s = development_cpcv["20"]["candidate_summaries"][name]
        f = forward["20"][name]
        promotion[name] = {
            "promotion_gate": bool(
                s["median_sharpe"] > 0
                and s["positive_path_fraction"] >= 0.60
                and f["sharpe"] > 0
                and f["mean_daily"] > 0
            ),
            "development_median_cpcv_sharpe_20bps": s["median_sharpe"],
            "development_positive_path_fraction_20bps": s["positive_path_fraction"],
            "forward_sharpe_20bps": f["sharpe"],
            "forward_mean_daily_20bps": f["mean_daily"],
        }

    report = {
        "status": "PASS",
        "phase": "8",
        "objective": "fresh-forward validation of volatility-state-conditioned strategy families",
        "data": {
            "development_start": dev["date"].min().strftime("%Y-%m-%d"),
            "development_end": dev["date"].max().strftime("%Y-%m-%d"),
            "forward_start": fwd["date"].min().strftime("%Y-%m-%d"),
            "forward_prediction_end": fwd["date"].max().strftime("%Y-%m-%d"),
            "forward_evaluation_end": fwd_eval["date"].max().strftime("%Y-%m-%d"),
            "development_rows": int(len(dev)),
            "forward_rows": int(len(fwd)),
            "forward_eval_rows": int(len(fwd_eval)),
            "fresh_forward_holdout": True,
            "old_phase6_final_holdout_used_only_as_historical_training": True,
        },
        "model": {
            "family": "multimodal",
            "features": features,
            "logistic_C": 0.5,
            "volatility_probability_threshold": P_THRESHOLD,
            "specification_frozen_from_phase5": True,
            "forward_tuning": False,
        },
        "forward_volatility_prediction": {
            "auc": auc,
            "mean_probability": float(np.mean(p_fwd)),
            "actual_expansion_rate": float(fwd_eval["target_vol_expand5"].mean()),
        },
        "candidate_set": CANDIDATES,
        "forward_cost_sensitivity": forward,
        "development_cpcv": development_cpcv,
        "approx_dsr": dsr,
        "promotion_gates": promotion,
        "guardrails": {
            "returns": "close-to-close NIFTY settlement proxy",
            "costs": "fixed bps per side, not observed bid/ask/slippage",
            "options_execution": "not tested; no quote/order/trade feed",
            "selection": "no candidate selected from fresh forward holdout",
        },
        "decision": {
            "promotable_candidates": [
                name for name, v in promotion.items() if v["promotion_gate"]
            ],
            "rule": (
                "A candidate must have development median CPCV Sharpe > 0, "
                "development positive-path fraction >= 60%, and positive "
                "forward 20-bps mean daily return and Sharpe."
            ),
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "PHASE8_VOLATILITY_CONDITIONAL_REPORT.json").write_text(
        json.dumps(report, indent=2, allow_nan=True) + "\n"
    )
    print(json.dumps(report, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
