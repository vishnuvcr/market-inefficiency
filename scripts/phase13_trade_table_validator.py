#!/usr/bin/env python3
"""Phase 13 executable-trade input validator.

This validates the minimum trade-level schema before CPCV/PBO/DSR runs.
It does not estimate profitability and it never fabricates missing fills.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = {
    "candidate",
    "decision_time",
    "entry_time",
    "exit_time",
    "contract_id",
    "side",
    "quantity",
    "entry_fill",
    "exit_fill",
    "gross_pnl",
    "fees",
    "taxes",
    "net_pnl",
    "capital_at_risk",
}


def parse_time(value: str) -> datetime:
    raw = value.strip().replace("Z", "+00:00")
    ts = datetime.fromisoformat(raw)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def finite_positive(value: str, name: str) -> float:
    x = float(value)
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f"{name} must be finite and > 0")
    return x


def validate(path: Path) -> dict:
    errors: list[str] = []
    rows = 0
    intervals_by_candidate: dict[str, list[tuple[datetime, datetime]]] = {}

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - fields)
        if missing:
            return {
                "status": "FAIL",
                "rows": 0,
                "errors": ["missing_columns:" + ",".join(missing)],
            }

        for line_no, row in enumerate(reader, start=2):
            rows += 1
            try:
                candidate = str(row["candidate"]).strip()
                decision = parse_time(row["decision_time"])
                entry = parse_time(row["entry_time"])
                exit_ = parse_time(row["exit_time"])
                if not candidate:
                    raise ValueError("empty candidate")
                if not (decision <= entry <= exit_):
                    raise ValueError("decision/entry/exit ordering invalid")
                side = int(row["side"])
                if side not in (-1, 1):
                    raise ValueError("side must be -1 or +1")
                finite_positive(row["quantity"], "quantity")
                finite_positive(row["entry_fill"], "entry_fill")
                finite_positive(row["exit_fill"], "exit_fill")
                finite_positive(row["capital_at_risk"], "capital_at_risk")
                for name in ("gross_pnl", "fees", "taxes", "net_pnl"):
                    x = float(row[name])
                    if not math.isfinite(x):
                        raise ValueError(f"{name} must be finite")
                intervals_by_candidate.setdefault(candidate, []).append((entry, exit_))
            except Exception as exc:
                errors.append(f"line {line_no}: {exc}")

    overlaps = 0
    for intervals in intervals_by_candidate.values():
        intervals.sort()
        prior_end = None
        for start, end in intervals:
            if prior_end is not None and start < prior_end:
                overlaps += 1
            if prior_end is None or end > prior_end:
                prior_end = end

    status = "PASS" if rows > 0 and not errors and overlaps == 0 else "FAIL"
    return {
        "status": status,
        "rows": rows,
        "candidate_count": len(intervals_by_candidate),
        "overlapping_same_candidate_rows": overlaps,
        "errors_sample": errors[:25],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = validate(args.input)
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
