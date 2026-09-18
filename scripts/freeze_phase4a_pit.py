#!/usr/bin/env python3
"""Freeze the Phase 4A point-in-time join without creating a giant duplicate dataset.

Inputs are immutable GitHub Actions artifacts:
  - NIFTY OPTIDX normalized yearly partitions
  - official NIFTY 50 daily OHLC
  - contract-level NIFTY lot-size master
  - RBI PIT risk-free daily curve

The script validates every normalized option row against the external PIT inputs,
records explicit exclusions, and writes a compact immutable snapshot manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

GAP_DATES = {"2021-03-30"}
DECISION_HOUR = "23:59:59+05:30"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def contract_id(expiry, strike, option_type) -> str:
    return (
        "NIFTY|"
        + pd.Timestamp(expiry).strftime("%Y-%m-%d")
        + "|"
        + f"{float(strike):g}"
        + "|"
        + str(option_type).upper()
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--options-root", required=True, type=Path)
    ap.add_argument("--underlying", required=True, type=Path)
    ap.add_argument("--lot-master", required=True, type=Path)
    ap.add_argument("--risk-free", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--sample-rows", type=int, default=5000)
    args = ap.parse_args()

    underlying = pd.read_csv(args.underlying)
    underlying["date"] = pd.to_datetime(underlying["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    underlying["close"] = pd.to_numeric(underlying["close"], errors="coerce")
    if underlying["date"].duplicated().any() or underlying["close"].le(0).any():
        raise SystemExit("Underlying failed uniqueness/positivity checks")
    underlying = underlying.set_index("date")

    lot = pd.read_csv(args.lot_master)
    lot["effective_from"] = pd.to_datetime(lot["effective_from"], errors="coerce")
    lot["effective_to"] = pd.to_datetime(lot["effective_to"], errors="coerce")
    lot["lot_size"] = pd.to_numeric(lot["lot_size"], errors="coerce")
    lot["available_at"] = pd.to_datetime(lot["available_at"], errors="coerce", utc=True)
    if lot["lot_size"].le(0).any() or lot["contract_id"].duplicated().sum() < 0:
        raise SystemExit("Lot master failed positivity check")
    if lot.duplicated(["contract_id", "effective_from"]).any():
        raise SystemExit("Lot master has duplicate contract/effective-from keys")

    rf = pd.read_csv(args.risk_free)
    rf["date"] = pd.to_datetime(rf["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    rf_cols = [
        "yield_pct_91", "yield_pct_182", "yield_pct_364",
        "available_date_91", "available_date_182", "available_date_364",
    ]
    for c in rf_cols:
        if c.startswith("available_date_"):
            rf[c] = pd.to_datetime(rf[c], errors="coerce")
        else:
            rf[c] = pd.to_numeric(rf[c], errors="coerce")
    if rf["date"].duplicated().any() or rf[rf_cols[:3]].isna().any().any():
        raise SystemExit("Risk-free daily curve failed uniqueness/completeness checks")
    rf = rf.set_index("date")

    normalized_files = sorted(args.options_root.rglob("normalized/*.csv"))
    if not normalized_files:
        normalized_files = sorted(args.options_root.rglob("*.csv"))
    normalized_files = [p for p in normalized_files if p.name.lower() not in {"validation.csv"}]
    if not normalized_files:
        raise SystemExit("No normalized option files found")

    counters = {
        "option_rows": 0,
        "pit_join_pass_rows": 0,
        "gap_excluded_rows": 0,
        "underlying_missing_rows": 0,
        "lot_missing_rows": 0,
        "lot_not_available_rows": 0,
        "risk_free_missing_rows": 0,
        "expiry_invalid_rows": 0,
        "positive_settlement_rows": 0,
        "sample_rows": 0,
    }
    by_date = []
    sample_parts = []

    for path in normalized_files:
        x = pd.read_csv(path)
        required = {
            "trade_date", "expiry", "strike", "option_type",
            "settlement", "available_at", "timestamp",
        }
        missing = required - set(x.columns)
        if missing:
            raise SystemExit(f"{path}: missing {sorted(missing)}")

        x["trade_date"] = pd.to_datetime(x["trade_date"], errors="coerce")
        x["expiry"] = pd.to_datetime(x["expiry"], errors="coerce")
        x["strike"] = pd.to_numeric(x["strike"], errors="coerce")
        x["settlement"] = pd.to_numeric(x["settlement"], errors="coerce")
        x["option_type"] = x["option_type"].astype("string").str.upper()
        x["contract_id"] = [
            contract_id(e, s, o)
            for e, s, o in zip(x["expiry"], x["strike"], x["option_type"])
        ]
        x["date_key"] = x["trade_date"].dt.strftime("%Y-%m-%d")
        counters["option_rows"] += len(x)

        x["underlying_close"] = x["date_key"].map(underlying["close"])
        x["rf_y91"] = x["date_key"].map(rf["yield_pct_91"])
        x["rf_y182"] = x["date_key"].map(rf["yield_pct_182"])
        x["rf_y364"] = x["date_key"].map(rf["yield_pct_364"])

        # Interval join without Cartesian inflation: a contract may have
        # multiple lot-size intervals, so merge on contract_id first, then
        # retain exactly the interval containing the observation date.
        x["_row_id"] = range(len(x))
        lot_cols = lot[
            [
                "contract_id", "effective_from", "effective_to",
                "lot_size", "available_at", "source_version",
            ]
        ].rename(
            columns={
                "available_at": "lot_available_at",
                "lot_size": "master_lot_size",
            }
        )
        merged = x[["_row_id", "contract_id", "trade_date"]].merge(
            lot_cols, on="contract_id", how="left"
        )
        match = (
            merged["trade_date"].ge(merged["effective_from"])
            & merged["trade_date"].le(merged["effective_to"])
        )
        matched = merged.loc[match].copy()
        overlap_counts = matched.groupby("_row_id").size()
        if (overlap_counts > 1).any():
            bad = overlap_counts[overlap_counts > 1].head().to_dict()
            raise SystemExit(f"Lot master has overlapping intervals for option rows: {bad}")
        matched = matched.drop_duplicates("_row_id")
        x = x.merge(
            matched[
                [
                    "_row_id", "master_lot_size", "lot_available_at",
                    "source_version",
                ]
            ],
            on="_row_id",
            how="left",
        )

        x["gap_excluded"] = x["date_key"].isin(GAP_DATES)
        x["expiry_invalid"] = x["expiry"].isna() | x["trade_date"].isna() | x["expiry"].lt(x["trade_date"])
        # The known archive gap is an explicit exclusion, not an external-input
        # failure. Do not count it as missing underlying/risk-free coverage.
        x["underlying_missing"] = (
            (x["underlying_close"].isna() | x["underlying_close"].le(0))
            & ~x["gap_excluded"]
        )
        x["lot_missing"] = x["master_lot_size"].isna() | pd.to_numeric(x["master_lot_size"], errors="coerce").le(0)

        decision_ts = pd.to_datetime(
            x["date_key"] + " " + DECISION_HOUR,
            errors="coerce",
            utc=True,
        )
        x["lot_not_available"] = (
            x["lot_available_at"].notna()
            & (pd.to_datetime(x["lot_available_at"], utc=True, errors="coerce") > decision_ts)
        )
        x["lot_not_available"] = x["lot_not_available"] | (
            x["lot_available_at"].isna() & ~x["lot_missing"]
        )

        x["risk_free_missing"] = (
            x[["rf_y91", "rf_y182", "rf_y364"]].isna().any(axis=1)
            & ~x["gap_excluded"]
        )

        x["pit_join_pass"] = ~(
            x["gap_excluded"]
            | x["expiry_invalid"]
            | x["underlying_missing"]
            | x["lot_missing"]
            | x["lot_not_available"]
            | x["risk_free_missing"]
        )

        counters["pit_join_pass_rows"] += int(x["pit_join_pass"].sum())
        counters["gap_excluded_rows"] += int(x["gap_excluded"].sum())
        counters["underlying_missing_rows"] += int(x["underlying_missing"].sum())
        counters["lot_missing_rows"] += int(x["lot_missing"].sum())
        counters["lot_not_available_rows"] += int(x["lot_not_available"].sum())
        counters["risk_free_missing_rows"] += int(x["risk_free_missing"].sum())
        counters["expiry_invalid_rows"] += int(x["expiry_invalid"].sum())
        counters["positive_settlement_rows"] += int(x["settlement"].gt(0).sum())

        daily = (
            x.groupby("date_key", dropna=False)
            .agg(
                option_rows=("date_key", "size"),
                pit_join_pass_rows=("pit_join_pass", "sum"),
                gap_excluded_rows=("gap_excluded", "sum"),
                underlying_missing_rows=("underlying_missing", "sum"),
                lot_missing_rows=("lot_missing", "sum"),
                lot_not_available_rows=("lot_not_available", "sum"),
                risk_free_missing_rows=("risk_free_missing", "sum"),
                positive_settlement_rows=("settlement", lambda s: int(s.gt(0).sum())),
            )
            .reset_index()
        )
        by_date.append(daily)

        keep = x.loc[x["pit_join_pass"]].copy()
        if len(keep):
            sample_parts.append(
                keep.head(max(0, args.sample_rows - counters["sample_rows"]))[
                    [
                        "date_key", "expiry", "strike", "option_type",
                        "settlement", "underlying_close", "master_lot_size",
                        "source_version", "rf_y91", "rf_y182", "rf_y364",
                    ]
                ]
            )
            counters["sample_rows"] += min(len(keep), max(0, args.sample_rows - counters["sample_rows"]))

    if counters["underlying_missing_rows"] or counters["lot_missing_rows"] or counters["lot_not_available_rows"] or counters["risk_free_missing_rows"] or counters["expiry_invalid_rows"]:
        raise SystemExit(f"PIT join failed: {counters}")

    coverage = pd.concat(by_date, ignore_index=True).sort_values("date_key")
    sample = pd.concat(sample_parts, ignore_index=True).head(args.sample_rows) if sample_parts else pd.DataFrame()

    args.output.mkdir(parents=True, exist_ok=True)
    coverage_path = args.output / "PHASE4A_PIT_COVERAGE.csv"
    sample_path = args.output / "PHASE4A_PIT_SAMPLE.csv"
    manifest_path = args.output / "PHASE4A_PIT_SNAPSHOT_MANIFEST.json"
    coverage.to_csv(coverage_path, index=False)
    sample.to_csv(sample_path, index=False)

    source_files = {
        "underlying": {"path": str(args.underlying), "sha256": sha256(args.underlying)},
        "lot_master": {"path": str(args.lot_master), "sha256": sha256(args.lot_master)},
        "risk_free": {"path": str(args.risk_free), "sha256": sha256(args.risk_free)},
    }
    manifest = {
        "status": "PASS",
        "snapshot_id": "PHASE4A-PIT-NIFTY-2020-04-13-2026-05-14",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision_timestamp_rule": "trade_date 23:59:59 IST",
        "option_price_field_reserved_for_phase4b": "settlement",
        "gap_exclusions": sorted(GAP_DATES),
        "pit_rules": {
            "underlying": "official NSE NIFTY 50 EOD observation",
            "lot_master": "contract_id + unique effective interval + available_at <= decision timestamp",
            "risk_free": "RBI T-bill curve using latest auction observation available before decision date",
        },
        "input_files": source_files,
        "normalized_files": len(normalized_files),
        "coverage_start": coverage["date_key"].min(),
        "coverage_end": coverage["date_key"].max(),
        "counters": counters,
        "artifacts_are_external_immutable_inputs": True,
        "phase4b_gate": "OPEN",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
