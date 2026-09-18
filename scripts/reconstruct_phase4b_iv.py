#!/usr/bin/env python3
"""Phase 4B baseline NIFTY implied-volatility reconstruction.

Price field: NSE EOD settlement.
Model: Black-76 on an option-implied forward.
Forward: put-call parity, median across paired strikes in [0.80, 1.20]
spot moneyness, using the same PIT risk-free curve. A spot/risk-free fallback
is NOT used for the formal IV sample; contracts without a usable parity
forward are excluded.

The output is pointwise IV data plus deterministic surface-quality diagnostics.
No future data are used.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
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
        "NIFTY|" + pd.Timestamp(expiry).strftime("%Y-%m-%d") + "|"
        + f"{float(strike):g}" + "|" + str(option_type).upper()
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
    """Vectorized bisection inversion of Black-76."""
    price = np.asarray(price, dtype=float)
    F = np.asarray(F, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    r = np.asarray(r, dtype=float)
    is_call = np.asarray(option_type) == "CE"

    df = np.exp(-r * T)
    intrinsic = df * np.where(is_call, np.maximum(F - K, 0.0), np.maximum(K - F, 0.0))
    upper = df * np.where(is_call, F, K)

    valid = (
        np.isfinite(price) & np.isfinite(F) & np.isfinite(K)
        & np.isfinite(T) & np.isfinite(r) & (F > 0) & (K > 0) & (T > MIN_T)
        & (price >= intrinsic - 1e-8) & (price <= upper + 1e-8)
    )
    lo = np.full(price.shape, MIN_IV)
    hi = np.full(price.shape, MAX_IV)
    iv = np.full(price.shape, np.nan)

    # Keep only numerically admissible observations.
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

    # A fixed 64-step bisection is deterministic and sufficiently precise.
    low = np.full(len(idx), MIN_IV)
    high = np.full(len(idx), MAX_IV)
    for _ in range(64):
        mid = (low + high) * 0.5
        cp = np.where(
            calls,
            black76_price(ff, kk, tt, rr, mid, "CE"),
            black76_price(ff, kk, tt, rr, mid, "PE"),
        )
        # Price is monotone increasing in sigma.
        too_low = cp < p
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
    rf = rf.dropna(subset=["date", "yield_pct_91", "yield_pct_182", "yield_pct_364"])
    return rf.drop_duplicates("date").set_index(rf["date"].dt.strftime("%Y-%m-%d"))


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
        "trade_date", "expiry", "strike", "option_type", "settlement",
        "available_at", "timestamp",
    }
    missing = required - set(x.columns)
    if missing:
        raise SystemExit(f"{path}: missing {sorted(missing)}")

    x["trade_date"] = pd.to_datetime(x["trade_date"], errors="coerce")
    x["expiry"] = pd.to_datetime(x["expiry"], errors="coerce")
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
        rate_for_ttm(a, b, c, t) if all(np.isfinite(v) for v in (a, b, c, t)) else np.nan
        for a, b, c, t in zip(x.yield_pct_91, x.yield_pct_182, x.yield_pct_364, x.T)
    ]

    # The contract master is used as a PIT validation input and supplies lot size.
    lm = lot[["contract_id", "effective_from", "effective_to", "lot_size"]].copy()
    lm["effective_from"] = pd.to_datetime(lm["effective_from"])
    lm["effective_to"] = pd.to_datetime(lm["effective_to"])
    m = x[["contract_id", "trade_date"]].reset_index(names="_row_id").merge(lm, on="contract_id", how="left")
    m = m[m["trade_date"].ge(m["effective_from"]) & m["trade_date"].le(m["effective_to"])]
    if m["_row_id"].duplicated().any():
        raise SystemExit(f"{path}: overlapping lot-master intervals")
    x = x.merge(m[["_row_id", "lot_size"]], left_index=True, right_on="_row_id", how="left").set_index("_row_id")
    # lot_size is supplied exclusively by the PIT contract master.
    # Drop any source-provided lot-size field so the PIT master remains authoritative.
    x = x.drop(columns=["lot_size"], errors="ignore")

    # Remove the two documented external-input gaps from formal IV reconstruction.
    x = x[~x["date_key"].isin(GAP_DATES)].copy()
    x = x[
        x["settlement"].gt(0)
        & x["spot"].gt(0)
        & x["strike"].gt(0)
        & x["T"].gt(MIN_T)
        & x[["yield_pct_91", "yield_pct_182", "yield_pct_364"]].notna().all(axis=1)
        & x["lot_size"].gt(0)
    ].copy()

    if x.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Paired call/put parity candidates by date/expiry/strike.
    cp = x.pivot_table(
        index=["date_key", "expiry_key", "strike"],
        columns="option_type",
        values="settlement",
        aggfunc="first",
    ).reset_index()
    cp = cp.dropna(subset=["CE", "PE"])
    spot_by_exp = x.groupby(["date_key", "expiry_key"], as_index=False).agg(
        spot=("spot", "first"), T=("T", "first"), r=("rf_simple", "first")
    )
    cp = cp.merge(spot_by_exp, on=["date_key", "expiry_key"], how="left")
    cp["moneyness"] = cp["strike"] / cp["spot"]
    cp = cp[
        cp["moneyness"].between(PARITY_MONEYNESS_LOW, PARITY_MONEYNESS_HIGH)
        & cp["T"].gt(MIN_T)
    ].copy()
    cp["forward_candidate"] = cp["strike"] + np.exp(cp["r"] * cp["T"]) * (cp["CE"] - cp["PE"])

    # Robust forward: median of parity candidates; retain dispersion diagnostics.
    fwd = (
        cp.groupby(["date_key", "expiry_key"], as_index=False)
        .agg(
            forward=("forward_candidate", "median"),
            parity_n=("forward_candidate", "size"),
            parity_iqr=("forward_candidate", lambda s: float(s.quantile(.75) - s.quantile(.25))),
            spot=("spot", "first"), T=("T", "first"), r=("r", "first"),
        )
    )
    fwd = fwd[fwd["forward"].gt(0)].copy()
    if fwd.empty:
        return pd.DataFrame(), pd.DataFrame()

    x = x.merge(fwd, on=["date_key", "expiry_key"], how="inner", suffixes=("", "_fwd"))
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
        "date_key", "expiry_key", "strike", "option_type", "settlement",
        "spot", "forward", "parity_n", "parity_iqr", "T", "ttm_days",
        "rf_simple", "moneyness", "lot_size", "iv",
    ]
    out = x[out_cols].rename(columns={"date_key": "trade_date", "expiry_key": "expiry"})
    out["model"] = "BLACK76_PARITY_FORWARD"
    out["price_field"] = "settlement"
    out["rf_rule"] = "PIT_RBI_91_182_364_LINEAR_SIMPLE_YIELD"
    out["forward_rule"] = "MEDIAN_PUT_CALL_PARITY_0.80_1.20_SPOT"
    out["gap_excluded"] = False

    surface = (
        out.groupby(["trade_date", "expiry"], as_index=False)
        .agg(
            option_count=("iv", "size"),
            forward=("forward", "first"),
            spot=("spot", "first"),
            ttm_days=("ttm_days", "first"),
            parity_n=("parity_n", "first"),
            parity_iqr=("parity_iqr", "first"),
            iv_median=("iv", "median"),
            iv_mean=("iv", "mean"),
            iv_p10=("iv", lambda s: s.quantile(.10)),
            iv_p90=("iv", lambda s: s.quantile(.90)),
            atm_iv=("iv", lambda s: s.loc[(out.loc[s.index, "moneyness"] - 1).abs().idxmin()] if len(s) else np.nan),
        )
    )
    return out, surface


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
    underlying = underlying.dropna(subset=["date", "close"]).drop_duplicates("date").set_index(
        pd.to_datetime(underlying["date"]).dt.strftime("%Y-%m-%d")
    )

    rf = build_rf_daily(args.risk_free)
    lot = pd.read_csv(args.lot_master)

    files = sorted(args.options_root.rglob("normalized/*.csv"))
    if not files:
        files = sorted(args.options_root.rglob("*.csv"))
    if not files:
        raise SystemExit("No normalized option files")

    args.output.mkdir(parents=True, exist_ok=True)
    all_surface = []
    stats = {"files": 0, "input_rows": 0, "iv_rows": 0, "surface_rows": 0, "positive_settlement_rows": 0}

    for path in files:
        iv, surface = process_file(path, underlying, rf, lot)
        stats["files"] += 1
        if not iv.empty:
            stats["iv_rows"] += len(iv)
            year = pd.Timestamp(iv["trade_date"].iloc[0]).year
            out_path = args.output / f"iv_observations_{year}.csv.gz"
            iv.to_csv(out_path, index=False, compression="gzip")
        if not surface.empty:
            stats["surface_rows"] += len(surface)
            all_surface.append(surface)

    if not all_surface:
        raise SystemExit("No IV observations reconstructed")

    surface = pd.concat(all_surface, ignore_index=True).sort_values(["trade_date", "expiry"])
    surface.to_csv(args.output / "iv_surface_daily.csv.gz", index=False, compression="gzip")

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
        "output_files": sorted(p.name for p in args.output.iterdir()),
    }
    (args.output / "PHASE4B_IV_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
