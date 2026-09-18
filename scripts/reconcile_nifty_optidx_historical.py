#!/usr/bin/env python3
"""Reconcile the immutable yearly NIFTY OPTIDX Phase 4A artifacts."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

KEY = ["trade_date", "expiry", "strike", "option_type"]
REQUIRED = KEY + [
    "open", "high", "low", "close", "last_price", "settlement",
    "volume", "turnover", "open_interest", "change_in_oi",
    "underlying_price", "lot_size", "available_at", "timestamp",
]


def load_manifests(root: Path) -> list[tuple[Path, dict]]:
    found = []
    for p in sorted(root.rglob("MANIFEST.json")):
        m = json.loads(p.read_text())
        if str(m.get("source", "")).startswith("NSE F&O"):
            found.append((p, m))
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Directory containing downloaded yearly artifacts")
    ap.add_argument("--output", default="phase4a_reconciliation.json")
    args = ap.parse_args()

    root = Path(args.root)
    manifests = load_manifests(root)
    if not manifests:
        raise SystemExit("No NSE NIFTY OPTIDX manifests found")

    years = {}
    records = []
    normalized_files = []
    for mp, m in manifests:
        year = int(str(m["start"])[:4])
        if year in years:
            raise SystemExit(f"Duplicate yearly manifest: {year}")
        years[year] = mp
        records.extend(m.get("records", []))
        base = mp.parent / "normalized"
        normalized_files.extend(sorted(base.glob("*.csv")))

    errors = []
    expected_years = list(range(2020, 2027))
    missing_years = [y for y in expected_years if y not in years]
    extra_years = [y for y in years if y not in expected_years]
    if missing_years:
        errors.append({"type": "missing_year_manifest", "years": missing_years})
    if extra_years:
        errors.append({"type": "unexpected_year_manifest", "years": extra_years})

    route_errors = []
    source_tiers = Counter()
    status_counts = Counter()
    weekday_no_archive = []
    validated_dates = set()
    expected_dates = set()

    for r in records:
        d = date.fromisoformat(r["date"])
        expected_dates.add(d)
        status_counts[r.get("status", "MISSING")] += 1
        source_tiers[r.get("source_tier", "missing")] += 1
        expected_route = "udiff" if d >= date(2024, 7, 8) else "legacy"
        if r.get("route") != expected_route:
            route_errors.append({"date": r["date"], "route": r.get("route"), "expected": expected_route})
        if r.get("status") == "VALIDATED":
            validated_dates.add(d)
        elif r.get("status") == "NO_ARCHIVE" and d.weekday() < 5:
            weekday_no_archive.append(r["date"])

    frames = []
    file_errors = []
    for p in normalized_files:
        try:
            df = pd.read_csv(p)
            missing = sorted(set(REQUIRED) - set(df.columns))
            if missing:
                file_errors.append({"file": str(p), "missing_columns": missing})
                continue
            df["_source_file"] = p.name
            frames.append(df)
        except Exception as exc:
            file_errors.append({"file": str(p), "error": f"{type(exc).__name__}: {exc}"})

    if not frames:
        raise SystemExit("No normalized CSV files found")

    x = pd.concat(frames, ignore_index=True)
    for c in ["trade_date", "expiry", "available_at", "timestamp"]:
        x[c] = pd.to_datetime(x[c], errors="coerce")
    for c in [
        "strike", "open", "high", "low", "close", "last_price",
        "settlement", "volume", "turnover", "open_interest",
        "change_in_oi", "underlying_price", "lot_size",
    ]:
        x[c] = pd.to_numeric(x[c], errors="coerce")

    duplicate_keys = int(x.duplicated(KEY).sum())
    file_dates = set(x["trade_date"].dt.date.dropna())
    missing_normalized_dates = sorted(validated_dates - file_dates)
    unexpected_normalized_dates = sorted(file_dates - validated_dates)

    boundary = x[(x["trade_date"] >= "2024-07-01") & (x["trade_date"] <= "2024-07-15")]
    boundary_dates = sorted(boundary["trade_date"].dropna().dt.date.astype(str).unique())

    legacy = x[x["trade_date"] < "2024-07-08"]
    udiff = x[x["trade_date"] >= "2024-07-08"]

    available_at_missing = int(x["available_at"].isna().sum())
    # trade_date is a calendar date (naive), while available_at may carry an
    # explicit timezone.  Compare calendar dates for the PIT gate so that an
    # EOD publication timestamp such as 23:59:59+05:30 is not compared to
    # naive midnight and does not trigger a false timezone error.
    trade_calendar_day = x["trade_date"].dt.date
    available_calendar_day = x["available_at"].dt.date
    available_at_before_trade = int(
        (available_calendar_day < trade_calendar_day).fillna(False).sum()
    )
    available_at_present_pct = float(x["available_at"].notna().mean() * 100)

    checks = {
        "manifest_count": len(manifests),
        "expected_years": expected_years,
        "years_found": sorted(years),
        "missing_year_manifests": missing_years,
        "unexpected_year_manifests": extra_years,
        "manifest_records": len(records),
        "status_counts": dict(status_counts),
        "source_tiers": dict(source_tiers),
        "validated_days_from_manifests": len(validated_dates),
        "normalized_files": len(normalized_files),
        "normalized_trade_dates": len(file_dates),
        "normalized_rows": int(len(x)),
        "duplicate_contract_keys": duplicate_keys,
        "file_errors": file_errors,
        "route_errors": route_errors,
        "missing_normalized_dates": [str(d) for d in missing_normalized_dates],
        "unexpected_normalized_dates": [str(d) for d in unexpected_normalized_dates],
        "weekday_no_archive_days": weekday_no_archive,
        "weekday_no_archive_count": len(weekday_no_archive),
        "legacy_rows": int(len(legacy)),
        "udiff_rows": int(len(udiff)),
        "legacy_missing_last_price_pct": float(legacy["last_price"].isna().mean() * 100) if len(legacy) else None,
        "udiff_missing_last_price_pct": float(udiff["last_price"].isna().mean() * 100) if len(udiff) else None,
        "legacy_missing_underlying_pct": float(legacy["underlying_price"].isna().mean() * 100) if len(legacy) else None,
        "udiff_missing_underlying_pct": float(udiff["underlying_price"].isna().mean() * 100) if len(udiff) else None,
        "legacy_missing_lot_size_pct": float(legacy["lot_size"].isna().mean() * 100) if len(legacy) else None,
        "udiff_missing_lot_size_pct": float(udiff["lot_size"].isna().mean() * 100) if len(udiff) else None,
        "available_at_present_pct": available_at_present_pct,
        "available_at_missing_rows": available_at_missing,
        "available_at_before_trade_rows": available_at_before_trade,
        "zero_volume_rows": int((x["volume"] == 0).sum()),
        "zero_open_interest_rows": int((x["open_interest"] == 0).sum()),
        "negative_price_rows": int((x[["open","high","low","close","last_price","settlement"]] < 0).any(axis=1).sum()),
        "expiry_before_trade": int((x["expiry"] < x["trade_date"]).sum()),
        "nonpositive_strike": int((x["strike"] <= 0).sum()),
        "ce_rows": int((x["option_type"] == "CE").sum()),
        "pe_rows": int((x["option_type"] == "PE").sum()),
        "unique_expiries": int(x["expiry"].nunique()),
        "boundary_trade_dates_2024_07_01_to_07_15": boundary_dates,
    }

    hard_failures = {}
    for k in [
        "missing_year_manifests", "unexpected_year_manifests", "duplicate_contract_keys",
        "file_errors", "route_errors", "missing_normalized_dates",
        "unexpected_normalized_dates", "negative_price_rows",
        "expiry_before_trade", "nonpositive_strike", "available_at_missing_rows",
        "available_at_before_trade_rows",
    ]:
        if checks[k]:
            hard_failures[k] = checks[k]

    result = {
        "status": "PASS" if not hard_failures else "FAIL",
        "scope": "Phase 4A NIFTY OPTIDX historical reconciliation",
        "checks": checks,
        "hard_failures": hard_failures,
        "interpretation": {
            "weekday_no_archive_days": "reported for calendar reconciliation; not treated as errors",
            "legacy_last_price": "NA is preserved when the legacy source lacks LTP; no CLOSE substitution",
            "available_at": "required for PIT gating; current value is a conservative EOD availability assumption and is not yet independently verified against NSE publication timing",
            "pit_status": "reconciliation PASS does not constitute final PIT validation; lot-size history, underlying availability and risk-free inputs still require source-level audit",
        },
    }

    out = Path(args.output)
    out.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result, indent=2, default=str))
    if hard_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
