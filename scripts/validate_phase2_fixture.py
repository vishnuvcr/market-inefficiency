"""Run deterministic point-in-time checks against the synthetic Phase 2 fixture."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_minimal.json"


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    decision = parse_ts(payload["decision_timestamp"])
    records = payload["records"]

    if payload["row_count"] != len(records):
        raise SystemExit("Fixture row_count mismatch")

    keys = set()
    previous = None
    for record in records:
        required = {
            "timestamp", "available_at", "instrument_id", "open",
            "high", "low", "close", "volume", "session_id",
        }
        missing = required - set(record)
        if missing:
            raise SystemExit(f"Missing fixture fields: {sorted(missing)}")

        timestamp = parse_ts(record["timestamp"])
        available_at = parse_ts(record["available_at"])
        if available_at < timestamp:
            raise SystemExit("available_at precedes observation timestamp")
        if available_at > decision:
            raise SystemExit("Fixture violates point-in-time decision rule")

        if record["high"] < max(record["open"], record["close"]):
            raise SystemExit("Invalid OHLC high")
        if record["low"] > min(record["open"], record["close"]):
            raise SystemExit("Invalid OHLC low")
        if min(record["open"], record["high"], record["low"], record["close"]) < 0:
            raise SystemExit("Negative price in fixture")

        key = (record["instrument_id"], record["timestamp"])
        if key in keys:
            raise SystemExit("Duplicate deterministic key")
        keys.add(key)

        if previous is not None and timestamp <= previous:
            raise SystemExit("Fixture timestamps are not strictly ordered")
        previous = timestamp

    print("Phase 2 fixture validation: PASS")
    print(f"Records checked: {len(records)}")
    print("PIT chronology: PASS")
    print("OHLC/price hygiene: PASS")
    print("Deterministic key uniqueness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
