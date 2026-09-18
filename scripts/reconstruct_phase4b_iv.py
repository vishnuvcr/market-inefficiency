#!/usr/bin/env python3
"""Phase 4B baseline NIFTY implied-volatility reconstruction.

Price field: NSE EOD settlement.
Model: Black-76 on an option-implied forward.
Forward: put-call parity, median across paired strikes in [0.80, 1.20]
spot moneyness, using the same PIT risk-free curve.

The output is pointwise IV data plus deterministic daily-surface diagnostics.
No future data are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

GAP_DATES = {"2021-03-30", "2024-03-02"}
MIN_T = 1.0 / 3650.0
PARITY_MONEYNESS_LOW = 0.80
PARITY_MONEYNESS_HIGH = 1.20
MAX_IV = 5.0
MIN_IV = 1e-6


def contract_id(expiry, strike, option_type):
    return (
        "NIFTY|"
        + pd.Timestamp(expiry).strftime("%Y-%m-%d")
        + "|"
        + f"{float(strike):g}"
        + "|"
        + str(option_type).upper()
    )


def black76_price(F, K, T, r, sigma, option_type):
    sqrt_t = np.sqrt(T)
    vs = sigma * sqrt_t
    d1 = (np.log(F / K) + 0.5 * sigma * sigma * T) / vs
    d2 = d1 - vs
    df = np.exp(-r * T)
    if option_type == "CE":
        return df * (F * ndtr(d1) - K * ndtr(d2))
    return df * (K * ndtr(-d2) - F * ndtr(-d1))


def implied_vol_vector(price, F, K, T, r, option_type):
    """Deterministic vectorized bisection inversion of Black-76."""
    price = np.asarray(price, dtype=float)
    F = np.asarray(F, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    r = np.asarray(r, dtype=float)
    is_call = np.asarray(option_type) == "CE"

    df = np.exp(-r * T)
    intrinsic = df * np.where(
        is_call, np.maximum(F - K, 0.0), np.maximum(K - F, 0.0)
    )
    upper = df * np.where(is_call, F, K)

    valid = (
        np.isfinite(price)
        & np.isfinite(F)
        & np.isfinite(K)
        & np.isfinite(T)
        & np.isfinite(r)
        & (F > 0)
        & (K > 0)
        & (T > MIN_T)
        & (price >= intrinsic - 1e-8)
        & (price <= upper + 1e-8)
    )
    iv = np.full(price.shape, np.nan)
    active = valid.copy()
    if not active.any():
        return iv, valid

    idx = np.where(active)[0]
    p = price[idx]
    ff = F[idx]
    kk = K[idx]
    tt = T[idx]
    rr = r[idx]
    calls = is_call[idx]

    low = np.full(len(idx), MIN_IV)
    high = np.full(len(idx), MAX_IV)
    for _ in range(64):
        mid = (low + high) * 0.5
        call_p = black76_price(ff, kk, tt, rr, mid, "CE")
        put_p = black76_price(ff, kk, tt, rr, mid, "PE")
        model_p = np.where(calls, call_p, put_p)
        too_low = model_p < p
        low[too_low] = mid[too_low]
        high[~too_low] = mid[~too_low]

    solved = (low + high) * 0.5
    iv[idx] = solved
    valid[idx] &= np.isfinite(solved) & (solved > MIN_IV) & (solved <= MAX_IV)
    iv[~valid] = np.nan
    return iv, valid


def build_rf_daily(rf_path: Path) -> pd.DataFrame:
    rf = pd.read_csv(rf_path)
    rf["date"] = pd.to_datetime(rf["date"], errors="coerce")
    for c in ("yield_pct_91", "yield_pct_182", "yield_pct_364"):
        rf[c] = pd.to_numeric(rf[c], errors="coerce")
    rf = rf.dropna(
        subset=["date", "yield_pct_91", "yield_pct_182", "yield_pct_364"]
    ).drop_duplicates("date")
    rf["date_key"] = rf["date"].dt.strftime("%Y-%m-%d")
    return rf.set_index("date_key")


def rate_for_ttm(y91, y182, y364, T):
    d = T * 365.0
    if d <= 91:
        return y91 / 100.0
    if d <= 182:
        w = (d - 91.0) / (182.0 - 91.0)
        return ((1 - w) * y91 + w * y182) / 100.0
    if d <= 364:
        w = (d - 182.0) / (364.0 - 182.0)
        return ((1 - w) * y182 + w * y364) / 100.0
    return y364 / 100.0


def process_file(path: Path, underlying: pd.DataFrame, rf: pd.DataFrame, lot: pd.DataFrame):
    x = pd.read_csv(path)
    required = {
        "trade_date",
        "expiry",
        "strike",
        "option_type",
        "settlement",
        "available_at",
        "timestamp",
    }
    missing = required - set(x.columns)
    if missing:
        raise SystemExit(f"{path}: missing {sorted(missing)}")

    input_rows = len(x)
    for col in ("trade_date", "expiry"):
        x[col] = pd.to_datetime(x[col], errors="coerce")
    x["strike"] = pd.to_numeric(x["strike"], errors="coerce")
    x["settlement"] = pd.to_numeric(x["settlement"], errors="coerce")
    x["option_type"] = x["option_type"].astype("string").str.upper()
    x["date_key"] = x["trade_date"].dt.strftime("%Y-%m-%d")
    x["expiry_key"] = x["expiry"].dt.strftime("%Y-%m-%d")
    x["contract_id"] = [
        contract_id(e, s, o)
        for e, s, o in zip(x["expiry"], x["strike"], x["option_type"])
    ]

    x["spot"] = x["date_key"].map(underlying["close"])
    for c in ("yield_pct_91", "yield_pct_182", "yield_pct_364"):
        x[c] = x["date_key"].map(rf[c])

    x["ttm_days"] = (x["expiry"] - x["trade_date"]).dt.days
    x["T"] = x["ttm_days"] / 365.0
    x["rf_simple"] = [
        rate_for_ttm(a, b, c, t)
        if all(np.isfinite(v) for v in (a, b, c, t))
        else np.nan
        for a, b, c, t in zip(
            x.yield_pct_91, x.yield_pct_182, x.yield_pct_364, x.T
        )
    ]

    # Authoritative PIT lot size comes only from the contract master.
    x = x.drop(columns=["lot_size"], errors="ignore")
    lm = lot[["contract_id", "effective_from", "effective_to", "lot_size"]].copy()
    lm["effective_from"] = pd.to_datetime(lm["effective_from"])
    lm["effective_to"] = pd.to_datetime(lm["effective_to"])

    m = (
        x[["contract_id", "trade_date"]]
        .reset_index(names="_row_id")
        .merge(lm, on="contract_id", how="left")
    )
    m = m[
        m["trade_date"].ge(m["effective_from"])
        & m["trade_date"].le(m["effective_to"])
    ]
    if m["_row_id"].duplicated().any():
        raise SystemExit(f"{path}: overlapping lot-master intervals")
    x = (
        x.merge(
            m[["_row_id", "lot_size"]],
            left_index=True,
            right_on="_row_id",
            how="left",
        )
        .set_index("_row_id")
    )

    # Explicit external-input coverage gaps are excluded from the formal sample.
    x = x[~x["date_key"].isin(GAP_DATES)].copy()
    positive_settlement_rows = int(x["settlement"].gt(0).sum())

    x = x[
        x["settlement"].gt(0)
        & x["spot"].gt(0)
        & x["strike"].gt(0)
        & x["T"].gt(MIN_T)
        & x[["yield_pct_91", "yield_pct_182", "yield_pct_364"]]
        .notna()
        .all(axis=1)
        & x["lot_size"].gt(0)
    ].copy()

    if x.empty:
        return pd.DataFrame(), pd.DataFrame(), {
            "input_rows": input_rows,
            "positive_settlement_rows": positive_settlement_rows,
        }

    cp = (
        x.pivot_table(
            index=["date_key", "expiry_key", "strike"],
            columns="option_type",
            values="settlement",
            aggfunc="first",
        )
        .dropna(subset=["CE", "PE"])
        .reset_index()
    )
    spot_by_exp = x.groupby(["date_key", "expiry_key"], as_index=False).agg(
        spot=("spot", "first"),
        T=("T", "first"),
        r=("rf_simple", "first"),
    )
    cp = cp.merge(spot_by_exp, on=["date_key", "expiry_key"], how="left")
    cp["moneyness"] = cp["strike"] / cp["spot"]
    cp = cp[
        cp["moneyness"].between(PARITY_MONEYNESS_LOW, PARITY_MONEYNESS_HIGH)
        & cp["T"].gt(MIN_T)
        & cp["r"].notna()
    ].copy()
    cp["forward_candidate"] = cp["strike"] + np.exp(cp["r"] * cp["T"]) * (
        cp["CE"] - cp["PE"]
    )

    fwd = (
        cp.groupby(["date_key", "expiry_key"], as_index=False)
        .agg(
            forward=("forward_candidate", "median"),
            parity_n=("forward_candidate", "size"),
            parity_iqr=(
                "forward_candidate",
                lambda s: float(s.quantile(0.75) - s.quantile(0.25)),
            ),
            spot=("spot", "first"),
            T=("T", "first"),
            r=("r", "first"),
        )
    )
    fwd = fwd[fwd["forward"].gt(0)].copy()
    if fwd.empty:
        return pd.DataFrame(), pd.DataFrame(), {
            "input_rows": input_rows,
            "positive_settlement_rows": positive_settlement_rows,
        }

    x = x.merge(
        fwd,
        on=["date_key", "expiry_key"],
        how="inner",
        suffixes=("", "_fwd"),
    )
    x["moneyness"] = x["strike"] / x["forward"]

    iv, ok = implied_vol_vector(
        x["settlement"].to_numpy(),
        x["forward"].to_numpy(),
        x["strike"].to_numpy(),
        x["T"].to_numpy(),
        x["r"].to_numpy(),
        x["option_type"].to_numpy(),
    )
    x["iv"] = iv
    x["iv_valid"] = ok
    x = x[x["iv_valid"]].copy()

    out_cols = [
        "date_key",
        "expiry_key",
        "strike",
        "option_type",
        "settlement",
        "spot",
        "forward",
        "parity_n",
        "parity_iqr",
        "T",
        "ttm_days",
        "rf_simple",
        "moneyness",
        "lot_size",
        "iv",
    ]
    out = x[out_cols].rename(
        columns={"date_key": "trade_date", "expiry_key": "expiry"}
    )
    out["model"] = "BLACK76_PARITY_FORWARD"
    out["price_field"] = "settlement"
    out["rf_rule"] = "PIT_RBI_91_182_364_LINEAR_SIMPLE_YIELD"
    out["forward_rule"] = "MEDIAN_PUT_CALL_PARITY_0.80_1.20_SPOT"
    out["gap_excluded"] = False
    out["atm_distance"] = (out["moneyness"] - 1.0).abs()

    groups = ["trade_date", "expiry"]
    atm = out.loc[out.groupby(groups)["atm_distance"].idxmin(), groups + ["iv"]].rename(
        columns={"iv": "atm_iv"}
    )
    surface = (
        out.groupby(groups, as_index=False)
        .agg(
            option_count=("iv", "size"),
            forward=("forward", "first"),
            spot=("spot", "first"),
            ttm_days=("ttm_days", "first"),
            parity_n=("parity_n", "first"),
            parity_iqr=("parity_iqr", "first"),
            iv_median=("iv", "median"),
            iv_mean=("iv", "mean"),
            iv_p10=("iv", lambda s: s.quantile(0.10)),
            iv_p90=("iv", lambda s: s.quantile(0.90)),
        )
        .merge(atm, on=groups, how="left")
    )
    out = out.drop(columns=["atm_distance"])
    return out, surface, {
        "input_rows": input_rows,
        "positive_settlement_rows": positive_settlement_rows,
    }


def append_gzip_frame(frame: pd.DataFrame, path: Path):
    if frame.empty:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        path,
        index=False,
        mode="at",
        header=not path.exists(),
        compression="gzip",
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--options-root", required=True, type=Path)
    ap.add_argument("--underlying", required=True, type=Path)
    ap.add_argument("--risk-free", required=True, type=Path)
    ap.add_argument("--lot-master", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    underlying = pd.read_csv(args.underlying)
    underlying["date"] = pd.to_datetime(underlying["date"], errors="coerce")
    underlying["close"] = pd.to_numeric(underlying["close"], errors="coerce")
    underlying = underlying.dropna(subset=["date", "close"]).drop_duplicates("date")
    underlying["date_key"] = underlying["date"].dt.strftime("%Y-%m-%d")
    underlying = underlying.set_index("date_key")

    rf = build_rf_daily(args.risk_free)
    lot = pd.read_csv(args.lot_master)

    files = sorted(args.options_root.rglob("normalized/*.csv"))
    if not files:
        files = sorted(args.options_root.rglob("*.csv"))
    if not files:
        raise SystemExit("No normalized option files")

    args.output.mkdir(parents=True, exist_ok=True)
    all_surface = []
    stats = {
        "files": 0,
        "input_rows": 0,
        "positive_settlement_rows": 0,
        "iv_rows": 0,
        "surface_rows": 0,
        "years": [],
        "empty_files": 0,
    }

    # Yearly gzip files are appended, never overwritten. This prevents later
    # daily partitions from silently replacing earlier observations.
    for path in files:
        iv, surface, file_stats = process_file(path, underlying, rf, lot)
        stats["files"] += 1
        stats["input_rows"] += file_stats["input_rows"]
        stats["positive_settlement_rows"] += file_stats["positive_settlement_rows"]

        if not iv.empty:
            stats["iv_rows"] += len(iv)
            years = pd.to_datetime(iv["trade_date"]).dt.year.unique().tolist()
            for year in years:
                chunk = iv[pd.to_datetime(iv["trade_date"]).dt.year.eq(year)]
                append_gzip_frame(
                    chunk,
                    args.output / f"iv_observations_{int(year)}.csv.gz",
                )
                stats["years"].append(int(year))
        else:
            stats["empty_files"] += 1

        if not surface.empty:
            stats["surface_rows"] += len(surface)
            all_surface.append(surface)

    if not all_surface:
        raise SystemExit("No IV observations reconstructed")

    surface = pd.concat(all_surface, ignore_index=True)
    surface = surface.sort_values(["trade_date", "expiry"]).reset_index(drop=True)
    if surface.duplicated(["trade_date", "expiry"]).any():
        raise SystemExit("Duplicate daily surface keys detected")
    if surface["iv_median"].isna().any() or surface["forward"].le(0).any():
        raise SystemExit("Invalid daily surface values detected")
    if not surface["atm_iv"].between(MIN_IV, MAX_IV).all():
        raise SystemExit("ATM IV outside formal bounds")

    surface.to_csv(
        args.output / "iv_surface_daily.csv.gz",
        index=False,
        compression="gzip",
    )

    stats["years"] = sorted(set(stats["years"]))
    manifest = {
        "status": "PASS",
        "phase": "4B",
        "model": "Black-76",
        "price_field": "NSE EOD settlement",
        "forward_method": "put-call parity median across paired strikes with 0.80-1.20 spot moneyness",
        "risk_free": "PIT RBI 91/182/364 annual simple yields, linear interpolation",
        "day_count": "ACT/365",
        "gap_exclusions": sorted(GAP_DATES),
        "iv_bounds": [MIN_IV, MAX_IV],
        "stats": stats,
        "surface_validation": {
            "daily_surface_rows": int(len(surface)),
            "unique_trade_dates": int(surface["trade_date"].nunique()),
            "unique_expiries": int(surface["expiry"].nunique()),
            "duplicate_trade_date_expiry": int(
                surface.duplicated(["trade_date", "expiry"]).sum()
            ),
            "atm_iv_min": float(surface["atm_iv"].min()),
            "atm_iv_median": float(surface["atm_iv"].median()),
            "atm_iv_max": float(surface["atm_iv"].max()),
            "parity_n_median": float(surface["parity_n"].median()),
            "parity_iqr_median": float(surface["parity_iqr"].median()),
        },
        "output_files": sorted(p.name for p in args.output.iterdir()),
    }
    (args.output / "PHASE4B_IV_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
