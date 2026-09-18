"""Run deterministic quality diagnostics on a normalized Phase 2 dataset.

The report is deliberately conservative: it never repairs observations. Rows that
violate canonical quality rules receive explicit exclusion reason codes so later
research can audit exactly why an observation was removed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = (
    "timestamp", "available_at", "instrument_id", "underlying_id", "expiry",
    "strike", "open", "high", "low", "close", "volume", "open_interest",
)


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def check_row(row: dict, decision_ts: datetime) -> list[str]:
    reasons: list[str] = []
    missing = [field for field in REQUIRED if row.get(field) in (None, "")]
    if missing:
        reasons.append("MISSING_REQUIRED_FIELD")
        return reasons
    try:
        timestamp = parse_ts(row["timestamp"])
        available_at = parse_ts(row["available_at"])
        expiry = parse_ts(row["expiry"])
    except (TypeError, ValueError):
        reasons.append("INVALID_TIMESTAMP")
        return reasons
    if available_at < timestamp:
        reasons.append("AVAILABLE_BEFORE_OBSERVATION")
    if available_at > decision_ts:
        reasons.append("LOOKAHEAD_AVAILABLE_AFTER_DECISION")
    if expiry < timestamp:
        reasons.append("EXPIRY_BEFORE_OBSERVATION")
    for field in ("open", "high", "low", "close", "strike", "volume", "open_interest"):
        try:
            value = float(row[field])
        except (TypeError, ValueError):
            reasons.append("NON_NUMERIC_VALUE")
            break
        if value < 0:
            reasons.append("NEGATIVE_VALUE")
            break
    try:
        low, high = float(row["low"]), float(row["high"])
        op, cl = float(row["open"]), float(row["close"])
        if high < low or op < low or op > high or cl < low or cl > high:
            reasons.append("INVALID_OHLC_RANGE")
    except (TypeError, ValueError):
        pass
    if float(row["strike"]) <= 0:
        reasons.append("NON_POSITIVE_STRIKE")
    if float(row["volume"]) < 0 or float(row["open_interest"]) < 0:
        reasons.append("NEGATIVE_ACTIVITY")
    if row.get("option_type") not in ("CE", "PE"):
        reasons.append("INVALID_OPTION_TYPE")
    return reasons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--decision-timestamp", required=True)
    args = parser.parse_args()

    decision_ts = parse_ts(args.decision_timestamp)
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    reasons = Counter()
    exclusions = []
    valid = 0
    seen = set()

    for idx, row in enumerate(records):
        row_reasons = check_row(row, decision_ts)
        key = (row.get("timestamp"), row.get("instrument_id"))
        if key in seen:
            row_reasons.append("DUPLICATE_CANONICAL_KEY")
        seen.add(key)
        row_reasons = sorted(set(row_reasons))
        if row_reasons:
            for reason in row_reasons:
                reasons[reason] += 1
            exclusions.append({"record_index": idx, "instrument_id": row.get("instrument_id"), "timestamp": row.get("timestamp"), "reason_codes": row_reasons})
        else:
            valid += 1

    report = {
        "dataset_id": payload.get("dataset_id"),
        "source_id": payload.get("source_id"),
        "decision_timestamp": args.decision_timestamp,
        "input_row_count": len(records),
        "valid_row_count": valid,
        "excluded_row_count": len(exclusions),
        "exclusion_reason_counts": dict(sorted(reasons.items())),
        "exclusions": exclusions,
        "status": "PASS" if not exclusions else "REJECT_ROWS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Quality report: {valid}/{len(records)} valid rows")
    print(f"Status: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
