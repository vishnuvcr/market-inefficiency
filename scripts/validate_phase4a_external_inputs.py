#!/usr/bin/env python3
"""Validate externally supplied Phase 4A PIT inputs before snapshot freeze.

This validator intentionally does not download or infer market data. It checks
the supplied files for deterministic schema/date coverage and records hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: Path, required: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--underlying", required=True, type=Path)
    ap.add_argument("--lot-map", required=True, type=Path)
    ap.add_argument("--risk-free", required=True, type=Path)
    ap.add_argument("--start", default="2020-04-13")
    ap.add_argument("--end", default="2026-05-14")
    ap.add_argument("--output", default="PHASE4A_EXTERNAL_INPUT_VALIDATION.json")
    args = ap.parse_args()

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)

    underlying = load_csv(args.underlying, ["date", "close"])
    underlying["date"] = pd.to_datetime(underlying["date"], errors="coerce")
    underlying["close"] = pd.to_numeric(underlying["close"], errors="coerce")

    lot = load_csv(args.lot_map, ["expiry", "lot_size"])
    lot["expiry"] = pd.to_datetime(lot["expiry"], errors="coerce")
    lot["lot_size"] = pd.to_numeric(lot["lot_size"], errors="coerce")

    rf = load_csv(args.risk_free, ["date", "tenor_days", "yield_pct"])
    rf["date"] = pd.to_datetime(rf["date"], errors="coerce")
    rf["tenor_days"] = pd.to_numeric(rf["tenor_days"], errors="coerce")
    rf["yield_pct"] = pd.to_numeric(rf["yield_pct"], errors="coerce")

    errors: list[str] = []

    if underlying["date"].isna().any() or underlying["close"].isna().any():
        errors.append("underlying contains invalid date/close values")
    if (underlying["close"] <= 0).any():
        errors.append("underlying contains non-positive closes")
    if underlying["date"].duplicated().any():
        errors.append("underlying contains duplicate dates")

    if lot["expiry"].isna().any() or lot["lot_size"].isna().any():
        errors.append("lot map contains invalid expiry/lot values")
    if (lot["lot_size"] <= 0).any():
        errors.append("lot map contains non-positive lot sizes")
    if lot["expiry"].duplicated().any():
        errors.append("lot map contains duplicate expiries")

    if rf["date"].isna().any() or rf["tenor_days"].isna().any() or rf["yield_pct"].isna().any():
        errors.append("risk-free input contains invalid date/tenor/yield values")
    if (rf["tenor_days"] <= 0).any():
        errors.append("risk-free input contains non-positive tenors")
    if rf.duplicated(["date", "tenor_days"]).any():
        errors.append("risk-free input contains duplicate date/tenor observations")

    umin, umax = underlying["date"].min(), underlying["date"].max()
    if pd.isna(umin) or pd.isna(umax) or umin > start or umax < end:
        errors.append(f"underlying coverage must span {start.date()} through {end.date()}")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "Phase 4A external PIT input validation",
        "requested_period": [str(start.date()), str(end.date())],
        "files": {
            "underlying": {"path": str(args.underlying), "sha256": sha256(args.underlying), "rows": len(underlying)},
            "lot_map": {"path": str(args.lot_map), "sha256": sha256(args.lot_map), "rows": len(lot)},
            "risk_free": {"path": str(args.risk_free), "sha256": sha256(args.risk_free), "rows": len(rf)},
        },
        "coverage": {
            "underlying_start": str(umin.date()) if not pd.isna(umin) else None,
            "underlying_end": str(umax.date()) if not pd.isna(umax) else None,
            "lot_expiry_start": str(lot["expiry"].min().date()) if not lot["expiry"].isna().all() else None,
            "lot_expiry_end": str(lot["expiry"].max().date()) if not lot["expiry"].isna().all() else None,
            "risk_free_start": str(rf["date"].min().date()) if not rf["date"].isna().all() else None,
            "risk_free_end": str(rf["date"].max().date()) if not rf["date"].isna().all() else None,
            "risk_free_tenors": sorted(rf["tenor_days"].dropna().unique().astype(int).tolist()),
        },
        "errors": errors,
        "pit_decision": "NOT_FROZEN" if errors else "READY_FOR_JOIN_AND_PIT_TIMESTAMP_AUDIT",
    }

    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
