#!/usr/bin/env python3
"""Audit Phase 4A weekday NO_ARCHIVE dates against the frozen gap registry."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reconciliation", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--output", default="PHASE4A_CALENDAR_AUDIT.json")
    args = ap.parse_args()

    recon = json.loads(Path(args.reconciliation).read_text())
    gaps = set(recon["checks"]["weekday_no_archive_days"])

    registry = {}
    with Path(args.registry).open(newline="") as fh:
        for row in csv.DictReader(fh):
            registry[row["trade_date"]] = row

    unregistered = sorted(gaps - set(registry))
    registry_not_gap = sorted(
        d for d in registry
        if registry[d]["status"] == "HOLIDAY_VERIFIED" and d not in gaps
    )
    holiday_verified = sorted(
        d for d in gaps if registry.get(d, {}).get("status") == "HOLIDAY_VERIFIED"
    )
    trading_day_archive_missing = sorted(
        d for d in gaps if registry.get(d, {}).get("status") == "TRADING_DAY_ARCHIVE_MISSING"
    )

    hard_failures = {}
    if unregistered:
        hard_failures["unregistered_weekday_no_archive"] = unregistered

    result = {
        "status": "PASS" if not hard_failures else "FAIL",
        "scope": "Phase 4A weekday NO_ARCHIVE calendar audit",
        "weekday_no_archive_count": len(gaps),
        "holiday_verified_count": len(holiday_verified),
        "trading_day_archive_missing_count": len(trading_day_archive_missing),
        "holiday_verified_dates": holiday_verified,
        "trading_day_archive_missing_dates": trading_day_archive_missing,
        "unregistered_dates": unregistered,
        "registry_extra_holiday_dates": registry_not_gap,
        "hard_failures": hard_failures,
        "interpretation": {
            "calendar_gate": "PASS only when every weekday NO_ARCHIVE date has an explicit classification",
            "data_completeness": "TRADING_DAY_ARCHIVE_MISSING dates remain dataset coverage gaps and must be excluded or separately sourced before any analysis requiring complete daily coverage",
        },
    }

    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if hard_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
