#!/usr/bin/env python3
"""Audit public top-of-book/L2 fixtures without treating them as P&L data."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

from phase12_execution_simulator import Quote, top_of_book_spread_bps, validate_quote


def _float(row: dict, *names: str) -> float:
    for name in names:
        if name in row and row[name] not in ("", None):
            return float(row[name])
    raise KeyError(names)


def _field(row: dict, *names: str) -> str:
    for name in names:
        if name in row:
            return row[name]
    raise KeyError(names)


def audit(path: Path) -> dict:
    rows = []
    rejected = {}
    duplicate_keys = 0
    seen = set()

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            try:
                timestamp = _field(row, "timestamp", "datetime")
                symbol = _field(row, "symbol")
                bid = _float(row, "bid_price1", "bid_px")
                bid_qty = _float(row, "bid_qty1", "bid_qty")
                ask = _float(row, "ask_price1", "ask_px")
                ask_qty = _float(row, "ask_qty1", "ask_qty")
                key = (symbol, timestamp)
                if key in seen:
                    duplicate_keys += 1
                seen.add(key)
                q = Quote(symbol, timestamp, bid, bid_qty, ask, ask_qty)
                validate_quote(q)
                rows.append(q)
            except Exception as exc:
                reason = str(exc)
                rejected[reason] = rejected.get(reason, 0) + 1

    spreads = [top_of_book_spread_bps(q) for q in rows]
    times = []
    for q in rows:
        raw = q.timestamp.strip().replace("Z", "+00:00")
        ts = datetime.fromisoformat(raw)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        times.append(ts.astimezone(timezone.utc))

    result = {
        "file": str(path),
        "rows": len(rows) + sum(rejected.values()),
        "valid_quotes": len(rows),
        "rejected_quotes": sum(rejected.values()),
        "rejections_by_reason": rejected,
        "unique_symbols": len({q.symbol for q in rows}),
        "duplicate_symbol_timestamp_rows": duplicate_keys,
        "start_time_utc": min(times).isoformat() if times else None,
        "end_time_utc": max(times).isoformat() if times else None,
        "spread_bps_median": statistics.median(spreads) if spreads else None,
        "spread_bps_p90": statistics.quantiles(spreads, n=10)[8] if len(spreads) >= 10 else None,
        "spread_bps_max": max(spreads) if spreads else None,
        "all_finite_positive_executable_quotes": bool(rows) and not rejected,
        "audit_status": "PASS" if rows and not rejected else ("PASS_WITH_REJECTIONS" if rows else "FAIL"),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.input)
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if result["audit_status"] == "FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
