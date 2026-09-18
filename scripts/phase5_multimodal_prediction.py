#!/usr/bin/env python3
"""Phase 5: multimodal market-inefficiency prediction engine.

This stage deliberately broadens the research beyond options. It combines
point-in-time NIFTY price/volatility/memory features with the frozen Phase 4B
option-surface features and tests whether they predict future market states.

Primary test:
  next-trading-day NIFTY direction, using a frozen 80/20 chronological split.

Secondary tests:
  next-5-session volatility expansion and feature-family ablations.

No future outcome is used as a feature. Model hyperparameters and signal
thresholds are fixed ex ante. The holdout is never used for tuning.
Outputs are predictive diagnostics and a settlement-to-settlement trading
proxy; they are not evidence of live profitability.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import math

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


TRAIN_FRAC = 0.80
GAP_DATES = {"2021-03-30", "2024-03-02"}
DIRECTION_THRESHOLD = 0.55
ROUND_TRIP_COST_BPS = (5, 10, 20)


def max_drawdown(r: pd.Series) -> float:
    wealth = (1.0 + r.fillna(0.0)).cumprod()
    peak = wealth.cummax()
    return float((wealth / peak - 1.0).min())


def strategy_metrics(ret: pd.Series) -> dict:
    x = pd.Series(ret).replace([np.inf, -np.inf], np.nan).dropna()
    if len(x) < 20:
        return {"n": int(len(x)), "mean": np.nan, "ann_return": np.nan,
                "ann_vol": np.nan, "sharpe": np.nan, "max_drawdown": np.nan}
    mean = float(x.mean())
    vol = float(x.std(ddof=1))
    ann_return = float((1.0 + mean) ** 252 - 1.0)
    ann_vol = float(vol * np.sqrt(252.0))
    sharpe = float(mean / vol * np.sqrt(252.0)) if vol > 0 else np.nan
    return {
        "n": int(len(x)),
        "mean_daily_return": mean,
        "ann_return_geometric_from_daily_mean": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(x),
        "positive_day_fraction": float((x > 0).mean()),
    }


def load_underlying(path: Path) -> pd.DataFrame:
    u = pd.read_csv(path)
    date_col = next((c for c in ["date", "DATE", "CH_TIMESTAMP", "TIMESTAMP"] if c in u.columns), None)
    close_col = next((c for c in ["close", "CLOSE", "Close"] if c in u.columns), None)
    if not date_col or not close_col:
        raise SystemExit(f"Underlying columns not recognised: {list(u.columns)}")
    u = u.rename(columns={date_col: "date", close_col: "close"})
    u["date"] = pd.to_datetime(u["date"], errors="coerce")
    u["close"] = pd.to_numeric(u["close"], errors="coerce")
    u = u.dropna(subset=["date", "close"])
    u = u[u["close"] > 0].drop_duplicates("date").sort_values("date").reset_index(drop=True)
    u = u[~u["date"].dt.strftime("%Y-%m-%d").isin(GAP_DATES)].copy()

    u["ret1"] = np.log(u["close"] / u["close"].shift(1))
    u["ret5"] = np.log(u["close"] / u["close"].shift(5))
    u["ret20"] = np.log(u["close"] / u["close"].shift(20))
    u["ret60"] = np.log(u["close"] / u["close"].shift(60))

    for w in [5, 20, 60]:
        u[f"rv_{w}"] = np.sqrt(
            u["ret1"].shift(1).rolling(w).apply(lambda x: np.sum(np.asarray(x) ** 2) * 252.0 / len(x), raw=False)
        )
    u["vol_ratio_5_20"] = u["rv_5"] / u["rv_20"]
    u["z20"] = (
        (u["close"] - u["close"].shift(1).rolling(20).mean())
        / u["close"].shift(1).rolling(20).std(ddof=0)
    )
    u["drawdown_60"] = u["close"] / u["close"].shift(1).rolling(60).max() - 1.0

    # Dependence/memory proxies: all based on prior observations only.
    u["ret_autocorr20"] = (
        u["ret1"].shift(1).rolling(20).corr(u["ret1"].shift(2))
    )
    absret = u["ret1"].abs()
    u["absret_autocorr20"] = (
        absret.shift(1).rolling(20).corr(absret.shift(2))
    )

    # Future labels are outcomes, never features.
    u["target_ret1"] = u["ret1"].shift(-1)
    u["target_up1"] = (u["target_ret1"] > 0).astype(float)
    future5 = np.log(u["close"].shift(-5) / u["close"])
    u["target_ret5"] = future5
    u["target_up5"] = (future5 > 0).astype(float)
    fwd5_rv = (
        u["ret1"].shift(-1)
        .rolling(5)
        .apply(lambda x: np.sum(np.asarray(x) ** 2) * 252.0 / len(x), raw=False)
        .shift(-4)
    )
    u["target_rv5"] = fwd5_rv
    u["target_vol_expand5"] = (u["target_rv5"] > u["rv_20"] ** 2).astype(float)
    return u


def discover_iv_files(root: Path) -> list[Path]:
    files = sorted(root.rglob("iv_observations_*.csv.gz"))
    if not files:
        raise SystemExit(f"No Phase 4B IV partitions found below {root}")
    return files


def load_iv(root: Path) -> pd.DataFrame:
    frames = []
    for path in discover_iv_files(root):
        df = pd.read_csv(path)
        required = {"trade_date", "expiry", "option_type", "moneyness", "ttm_days", "iv"}
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"{path}: missing {sorted(missing)}")
        df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
        df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce")
        for c in ["moneyness", "ttm_days", "iv"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["option_type"] = df["option_type"].astype(str).str.upper()
        frames.append(df)
    x = pd.concat(frames, ignore_index=True)
    x = x[~x["trade_date"].dt.strftime("%Y-%m-%d").isin(GAP_DATES)]
    x = x[(x["iv"] > 0) & (x["iv"] <= 5) & (x["ttm_days"] > 0) & (x["moneyness"] > 0)]
    return x


def expiry_band(iv: pd.DataFrame, option_type: str | None, lo: float, hi: float) -> pd.DataFrame:
    mask = iv["moneyness"].between(lo, hi)
    if option_type is not None:
        mask &= iv["option_type"].eq(option_type)
    x = iv.loc[mask, ["trade_date", "expiry", "ttm_days", "iv"]]
    return (
        x.groupby(["trade_date", "expiry", "ttm_days"], as_index=False)["iv"]
        .median()
    )


def const_maturity(band: pd.DataFrame, target_days: int, out_name: str) -> pd.DataFrame:
    rows = []
    for date, g in band.groupby("trade_date", sort=True):
        g = g.sort_values("ttm_days").dropna(subset=["ttm_days", "iv"])
        t = g["ttm_days"].to_numpy(float)
        v = g["iv"].to_numpy(float)
        if len(t) < 1:
            continue
        exact = np.where(t == target_days)[0]
        if len(exact):
            ivv = v[exact[0]]
        else:
            left = np.where(t < target_days)[0]
            right = np.where(t > target_days)[0]
            if len(left) == 0 or len(right) == 0:
                continue
            i, j = left[-1], right[0]
            weight = (target_days - t[i]) / (t[j] - t[i])
            w1 = v[i] * v[i] * t[i] / 365.0
            w2 = v[j] * v[j] * t[j] / 365.0
            ivv = math.sqrt(max((w1 + weight * (w2 - w1)) / (target_days / 365.0), 0.0))
        rows.append({"date": date, out_name: float(ivv)})
    return pd.DataFrame(rows)


def build_surface(iv: pd.DataFrame) -> pd.DataFrame:
    atm = expiry_band(iv, None, 0.97, 1.03)
    down = expiry_band(iv, "PE", 0.85, 0.95)
    up = expiry_band(iv, "CE", 1.05, 1.15)

    pieces = []
    for h in [30, 60]:
        a = const_maturity(atm, h, f"atm_iv_{h}")
        d = const_maturity(down, h, f"down_iv_{h}")
        c = const_maturity(up, h, f"up_iv_{h}")
        x = a.merge(d, on="date", how="inner").merge(c, on="date", how="inner")
        x[f"down_skew_{h}"] = x[f"down_iv_{h}"] - x[f"atm_iv_{h}"]
        x[f"up_skew_{h}"] = x[f"up_iv_{h}"] - x[f"atm_iv_{h}"]
        pieces.append(x)
    x = pieces[0].merge(pieces[1], on="date", how="inner")
    x["term_slope_30_60"] = x["atm_iv_60"] - x["atm_iv_30"]
    x["atm_minus_rv20"] = x["atm_iv_30"] ** 2 - x["rv20_proxy_placeholder"] if "rv20_proxy_placeholder" in x else np.nan
    return x


def build_features(underlying: pd.DataFrame, surface: pd.DataFrame) -> pd.DataFrame:
    x = underlying.merge(surface, on="date", how="left")
    # Ex-ante volatility-premium proxy: current 30D implied variance less
    # prior-20-session realized variance. No future information is used.
    x["vrp_state_proxy"] = x["atm_iv_30"] ** 2 - x["rv_20"] ** 2
    x["surface_skew_spread"] = x["down_skew_30"] - x["up_skew_30"]
    x["surface_atm_change_5"] = x["atm_iv_30"] - x["atm_iv_30"].shift(5)
    x["surface_skew_change_5"] = x["down_skew_30"] - x["down_skew_30"].shift(5)
    x["iv_term_ratio"] = x["atm_iv_60"] / x["atm_iv_30"]
    return x


FEATURES = {
    "price": [
        "ret1", "ret5", "ret20", "ret60", "z20", "drawdown_60",
        "ret_autocorr20", "absret_autocorr20",
    ],
    "price_vol": [
        "ret1", "ret5", "ret20", "ret60", "z20", "drawdown_60",
        "ret_autocorr20", "absret_autocorr20", "rv_5", "rv_20", "rv_60",
        "vol_ratio_5_20",
    ],
    "multimodal": [
        "ret1", "ret5", "ret20", "ret60", "z20", "drawdown_60",
        "ret_autocorr20", "absret_autocorr20", "rv_5", "rv_20", "rv_60",
        "vol_ratio_5_20", "atm_iv_30", "atm_iv_60", "down_skew_30",
        "up_skew_30", "down_skew_60", "up_skew_60", "term_slope_30_60",
        "vrp_state_proxy", "surface_skew_spread", "surface_atm_change_5",
        "surface_skew_change_5", "iv_term_ratio",
    ],
}


def fit_direction(train: pd.DataFrame, hold: pd.DataFrame, columns: list[str]) -> tuple[np.ndarray, dict]:
    pipe = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=0.5, max_iter=3000, solver="lbfgs"),
    )
    xtr = train[columns]
    ytr = train["target_up1"].astype(int)
    yh = hold["target_up1"].astype(int)
    pipe.fit(xtr, ytr)
    p = pipe.predict_proba(hold[columns])[:, 1]
    pred = (p >= 0.5).astype(int)
    metrics = {
        "accuracy_at_0_50": float(accuracy_score(yh, pred)),
        "brier": float(brier_score_loss(yh, p)),
        "log_loss": float(log_loss(yh, np.column_stack([1.0 - p, p]), labels=[0, 1])),
        "auc": float(roc_auc_score(yh, p)) if yh.nunique() == 2 else np.nan,
        "positive_rate_holdout": float(yh.mean()),
        "predicted_positive_rate": float((p >= 0.5).mean()),
        "probability_mean": float(p.mean()),
    }
    return p, metrics


def fit_volatility(train: pd.DataFrame, hold: pd.DataFrame, columns: list[str]) -> tuple[np.ndarray, dict]:
    pipe = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=0.5, max_iter=3000, solver="lbfgs"),
    )
    tr = train.dropna(subset=["target_vol_expand5"]).copy()
    ho = hold.dropna(subset=["target_vol_expand5"]).copy()
    pipe.fit(tr[columns], tr["target_vol_expand5"].astype(int))
    p = pipe.predict_proba(ho[columns])[:, 1]
    y = ho["target_vol_expand5"].astype(int)
    return p, {
        "n": int(len(ho)),
        "accuracy_at_0_50": float(accuracy_score(y, p >= 0.5)),
        "brier": float(brier_score_loss(y, p)),
        "auc": float(roc_auc_score(y, p)) if y.nunique() == 2 else np.nan,
        "positive_rate_holdout": float(y.mean()),
        "predicted_positive_rate": float((p >= 0.5).mean()),
    }


def direction_strategy(hold: pd.DataFrame, p: np.ndarray, cost_bps: int, label: str) -> dict:
    x = hold.loc[np.isfinite(p)].copy()
    x["p"] = p[np.isfinite(p)]
    x["position"] = np.where(
        x["p"] >= DIRECTION_THRESHOLD, 1.0,
        np.where(x["p"] <= 1.0 - DIRECTION_THRESHOLD, -1.0, 0.0),
    )
    x["prev_position"] = x["position"].shift(1).fillna(0.0)
    x["turnover_units"] = (x["position"] - x["prev_position"]).abs()
    cost = x["turnover_units"] * (cost_bps / 10000.0)
    x["gross"] = x["position"] * x["target_ret1"]
    x["net"] = x["gross"] - cost
    m = strategy_metrics(x["net"])
    m.update({
        "strategy": label,
        "cost_bps_per_side": cost_bps,
        "threshold_long": DIRECTION_THRESHOLD,
        "threshold_short": 1.0 - DIRECTION_THRESHOLD,
        "trade_day_fraction": float((x["position"] != 0).mean()),
        "mean_gross_daily": float(x["gross"].mean()),
        "mean_cost_daily": float(cost.mean()),
        "trades": int((x["turnover_units"] > 0).sum()),
        "holdout_start": x["date"].min().strftime("%Y-%m-%d"),
        "holdout_end": x["date"].max().strftime("%Y-%m-%d"),
    })
    return m


def regression_expected_return(train: pd.DataFrame, hold: pd.DataFrame, columns: list[str]) -> dict:
    tr = train.dropna(subset=["target_ret5"]).copy()
    ho = hold.dropna(subset=["target_ret5"]).copy()
    pipe = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=10.0),
    )
    pipe.fit(tr[columns], tr["target_ret5"])
    pred = pipe.predict(ho[columns])
    y = ho["target_ret5"].to_numpy(float)
    corr = float(np.corrcoef(y, pred)[0, 1]) if len(y) > 2 and np.std(pred) > 0 and np.std(y) > 0 else np.nan
    r2 = float(1.0 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)) if np.var(y) > 0 else np.nan
    return {
        "n": int(len(ho)),
        "oos_r2": r2,
        "prediction_target_correlation": corr,
        "actual_mean_5d_return": float(y.mean()),
        "predicted_mean_5d_return": float(pred.mean()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iv-root", type=Path, required=True)
    ap.add_argument("--underlying", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    u = load_underlying(args.underlying)
    iv = load_iv(args.iv_root)
    surface = build_surface(iv)
    x = build_features(u, surface)

    required_target = ["target_up1", "target_ret1", "target_ret5", "target_vol_expand5"]
    x = x.dropna(subset=required_target).copy()
    x = x.sort_values("date").reset_index(drop=True)
    cut = int(math.floor(len(x) * TRAIN_FRAC))
    if cut < 200 or len(x) - cut < 100:
        raise SystemExit(f"Insufficient sample after alignment: n={len(x)}, train={cut}, holdout={len(x)-cut}")
    train = x.iloc[:cut].copy()
    hold = x.iloc[cut:].copy()

    summary = {
        "status": "PASS",
        "phase": "5",
        "objective": "broad multimodal market-inefficiency prediction across price, volatility, memory and options-surface information",
        "sample": {
            "rows": int(len(x)),
            "train_rows": int(len(train)),
            "holdout_rows": int(len(hold)),
            "train_end": train["date"].max().strftime("%Y-%m-%d"),
            "holdout_start": hold["date"].min().strftime("%Y-%m-%d"),
            "holdout_end": hold["date"].max().strftime("%Y-%m-%d"),
        },
        "model_governance": {
            "split": "80% chronological train / 20% untouched holdout",
            "logistic_C": 0.5,
            "ridge_alpha": 10.0,
            "direction_long_short_threshold": 0.55,
            "no_holdout_tuning": True,
            "multiple_feature_families": 3,
            "primary_family": "multimodal",
        },
        "models": {},
        "trading_proxy_guardrail": "Settlement-to-settlement NIFTY proxy only; costs are sensitivity assumptions and not observed bid/ask/slippage. This cannot establish live profitability.",
    }

    for family, cols in FEATURES.items():
        missing = [c for c in cols if c not in x.columns]
        if missing:
            raise SystemExit(f"Feature family {family} missing columns: {missing}")
        p, dm = fit_direction(train, hold, cols)
        rm = regression_expected_return(train, hold, cols)
        vm_p, vm = fit_volatility(train, hold, cols)
        cost_scenarios = [
            direction_strategy(hold, p, c, family)
            for c in ROUND_TRIP_COST_BPS
        ]
        # Also preserve a zero-cost diagnostic, explicitly labelled gross proxy.
        gross = direction_strategy(hold, p, 0, family)
        summary["models"][family] = {
            "features": cols,
            "direction_holdout": dm,
            "expected_return_5d_holdout": rm,
            "volatility_expansion_5d_holdout": vm,
            "direction_strategy_proxy": {
                "zero_cost_gross_diagnostic": gross,
                "cost_sensitivity": cost_scenarios,
            },
        }

    # A simple non-ML benchmark: last-20-session momentum sign.
    hold_base = hold.copy()
    momentum_pos = np.sign(hold_base["ret20"].to_numpy(float))
    momentum_pos[np.abs(hold_base["ret20"].to_numpy(float)) < 1e-12] = 0.0
    p_bench = (momentum_pos + 1.0) / 2.0
    # p=1 for positive momentum, p=0 for negative; fixed 0.55 rule maps to +/-1.
    summary["benchmarks"] = {
        "20d_momentum_sign_proxy": [
            direction_strategy(hold_base, p_bench, c, "20d_momentum_sign")
            for c in ROUND_TRIP_COST_BPS
        ]
    }

    # Cross-family comparison is descriptive only; no winner selection.
    aucs = {k: v["direction_holdout"]["auc"] for k, v in summary["models"].items()}
    summary["comparison"] = {
        "direction_auc_by_family": aucs,
        "primary_interpretation": (
            "Treat the multimodal family as the preregistered primary. "
            "Price-only and price+volatility are ablations, not a basis for "
            "post-hoc model selection on the holdout."
        ),
    }

    features_out = x[["date", "close"] + sorted(set(sum(FEATURES.values(), [])))].copy()
    features_out.to_csv(args.output / "phase5_multimodal_features.csv.gz", index=False, compression="gzip")
    (args.output / "PHASE5_PREDICTION_REPORT.json").write_text(
        json.dumps(summary, indent=2, allow_nan=True) + "\n"
    )
    print(json.dumps(summary, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
