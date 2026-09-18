"""Normalize Kaggle NIFTY/India-VIX CSVs into the canonical observation contract.

This adapter intentionally accepts an operator-supplied local Kaggle file. It does
not download data or infer original exchange publication times. Kaggle is treated as
an external research snapshot and its provenance must be recorded separately.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ALIASES = {
    "timestamp": ["timestamp", "datetime", "date time", "date_time", "DateTime", "Datetime"],
    "date": ["date", "Date", "DATE"],
    "time": ["time", "Time", "TIME"],
    "open": ["open", "Open", "OPEN"],
    "high": ["high", "High", "HIGH"],
    "low": ["low", "Low", "LOW"],
    "close": ["close", "Close", "CLOSE"],
    "volume": ["volume", "Volume", "VOLUME"],
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def resolve(headers: list[str], names: list[str]) -> str | None:
    normalized = {clean(h): h for h in headers}
    for name in names:
        if clean(name) in normalized:
            return normalized[clean(name)]
    return None


def number(value: str | None) -> float | None:
    if value is None or value.strip() in {"", "-", "NA", "N/A", "null", "None"}:
        return None
    return float(value.replace(",", "").strip())


def parse_timestamp(row: dict, mapping: dict[str, str | None]) -> str:
    raw = row.get(mapping["timestamp"]) if mapping["timestamp"] else None
    if raw:
        text = raw.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            pass
    date = row.get(mapping["date"]) if mapping["date"] else None
    time = row.get(mapping["time"]) if mapping["time"] else "00:00:00"
    if not date:
        raise ValueError("No timestamp or date column found")
    text = f"{date.strip()} {time.strip()}"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    raise ValueError(f"Unsupported timestamp: {text!r}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--instrument-id", default="NIFTY50")
    parser.add_argument("--source-version", required=True, help="Exact Kaggle dataset/version identifier")
    parser.add_argument("--downloaded-at", required=True, help="UTC timestamp when the research copy was obtained")
    parser.add_argument("--available-at", required=True, help="UTC timestamp at which this research snapshot is treated as available")
    args = parser.parse_args()

    for value, label in ((args.downloaded_at, "downloaded-at"), (args.available_at, "available-at")):
        if not value.endswith("Z"):
            raise SystemExit(f"--{label} must be an explicit UTC timestamp ending in Z")
        datetime.fromisoformat(value.replace("Z", "+00:00"))

    raw_hash = sha256(args.input)
    with args.input.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise SystemExit("Input CSV has no header")
        mapping = {key: resolve(reader.fieldnames, aliases) for key, aliases in ALIASES.items()}
        for required in ("open", "high", "low", "close"):
            if not mapping[required]:
                raise SystemExit(f"Missing required OHLC column: {required}")
        records = []
        for row_no, row in enumerate(reader, start=2):
            timestamp = parse_timestamp(row, mapping)
            record = {
                "timestamp": timestamp,
                "available_at": args.available_at,
                "instrument_id": args.instrument_id,
                "open": number(row.get(mapping["open"])),
                "high": number(row.get(mapping["high"])),
                "low": number(row.get(mapping["low"])),
                "close": number(row.get(mapping["close"])),
                "volume": number(row.get(mapping["volume"])) if mapping["volume"] else None,
                "source_id": "DS-KAGGLE-NIFTY",
                "source_version": args.source_version,
                "source_row": row_no,
            }
            records.append(record)

    keys = [(r["timestamp"], r["instrument_id"]) for r in records]
    if len(keys) != len(set(keys)):
        raise SystemExit("Duplicate canonical keys detected")

    output = {
        "dataset_id": "KAGGLE-NIFTY-" + raw_hash[:16],
        "source": "Kaggle research snapshot",
        "source_id": "DS-KAGGLE-NIFTY",
        "source_version": args.source_version,
        "downloaded_at": args.downloaded_at,
        "available_at": args.available_at,
        "raw_sha256": raw_hash,
        "row_count": len(records),
        "records": records,
        "research_use": "stylized_facts_and_descriptive_analysis",
        "execution_backtest_allowed": False,
        "execution_backtest_reason": "Kaggle snapshot does not establish original historical exchange availability or bid/ask/depth provenance.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Normalized {len(records)} rows -> {args.output}")
    print(f"Immutable dataset_id: {output['dataset_id']}")
    print("Research classification: stylized-facts/descriptive only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
