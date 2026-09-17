"""Normalize a bounded NSE F&O EOD CSV slice into the canonical option_eod contract.

This adapter accepts an operator-supplied NSE historical CSV. It does not fetch the
exchange directly and never infers historical bid/ask data. Point-in-time
availability must be supplied explicitly because publication/availability time
cannot safely be inferred from trade date alone.
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
    "symbol": ["SYMBOL", "Symbol", "Underlying", "UNDERLYING"],
    "instrument": ["INSTRUMENT", "Instrument"],
    "trade_date": ["TIMESTAMP", "Trade Date", "TRADE_DATE", "Date", "DATE"],
    "expiry": ["Expiry", "EXPIRY_DT", "Expiry Date", "EXPIRY"],
    "option_type": ["Option Type", "OPTION_TYPE", "OptionType", "OPT_TYPE"],
    "strike": ["Strike Price", "STRIKE_PRICE", "Strike", "STRIKE"],
    "open": ["Open", "OPEN", "Open Price", "OPEN_PRICE"],
    "high": ["High", "HIGH", "High Price", "HIGH_PRICE"],
    "low": ["Low", "LOW", "Low Price", "LOW_PRICE"],
    "close": ["Close", "CLOSE", "Close Price", "CLOSE_PRICE"],
    "settlement": ["Settle Price", "SETTLE_PRICE", "Daily Settlement Price", "SETTLEMENT_PRICE"],
    "ltp": ["LTP", "Last Price", "LAST_PRICE"],
    "volume": ["No. of contracts", "No of contracts", "Volume", "VOLUME", "Contracts"],
    "oi": ["Open Int", "Open Interest", "Open Interest(OI)", "OI", "OPEN_INT"],
    "change_oi": ["Change in OI", "Change OI", "CHANGE_IN_OI"],
    "underlying_value": ["Underlying Value", "UNDERLYING_VALUE"],
}

REQUIRED = ["symbol", "trade_date", "expiry", "strike", "open", "high", "low", "close", "volume", "oi"]


def clean_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def resolve_headers(headers: list[str]) -> dict[str, str]:
    normalized = {clean_key(h).lower(): h for h in headers}
    result: dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            hit = normalized.get(clean_key(alias).lower())
            if hit:
                result[canonical] = hit
                break
    missing = [x for x in REQUIRED if x not in result]
    if missing:
        raise ValueError(f"Missing required NSE fields: {missing}")
    return result


def parse_number(value: str | None) -> float | int | None:
    if value is None or value.strip() in {"", "-", "NA", "N/A"}:
        return None
    text = value.replace(",", "").strip()
    number = float(text)
    return int(number) if number.is_integer() else number


def parse_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {value!r}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--available-at", required=True, help="Explicit PIT availability timestamp, ISO-8601 UTC")
    parser.add_argument("--source-version", default="nse-historical-report")
    args = parser.parse_args()

    available_at = args.available_at
    if not available_at.endswith("Z"):
        raise SystemExit("--available-at must be an explicit UTC timestamp ending in Z")
    datetime.fromisoformat(available_at.replace("Z", "+00:00"))

    with args.input.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise SystemExit("Input CSV has no header")
        mapping = resolve_headers(reader.fieldnames)
        records = []
        for row_no, row in enumerate(reader, start=2):
            symbol = row[mapping["symbol"]].strip()
            trade_ts = parse_date(row[mapping["trade_date"]])
            expiry = parse_date(row[mapping["expiry"]])
            option_type = row.get(mapping.get("option_type", ""), "").strip().upper() if "option_type" in mapping else ""
            instrument = row.get(mapping.get("instrument", ""), "").strip().upper() if "instrument" in mapping else ""
            contract_type = "option" if option_type in {"CE", "PE"} else "future_or_other"
            instrument_id = "|".join([symbol, expiry[:10], option_type or instrument, str(parse_number(row[mapping["strike"]]))])
            record = {
                "timestamp": trade_ts,
                "available_at": available_at,
                "instrument_id": instrument_id,
                "underlying_id": symbol,
                "expiry": expiry,
                "option_type": option_type or None,
                "strike": parse_number(row[mapping["strike"]]),
                "open": parse_number(row[mapping["open"]]),
                "high": parse_number(row[mapping["high"]]),
                "low": parse_number(row[mapping["low"]]),
                "close": parse_number(row[mapping["close"]]),
                "settlement": parse_number(row[mapping["settlement"]]) if "settlement" in mapping else None,
                "ltp": parse_number(row[mapping["ltp"]]) if "ltp" in mapping else None,
                "volume": parse_number(row[mapping["volume"]]),
                "open_interest": parse_number(row[mapping["oi"]]),
                "change_in_oi": parse_number(row[mapping["change_oi"]]) if "change_oi" in mapping else None,
                "underlying_value": parse_number(row[mapping["underlying_value"]]) if "underlying_value" in mapping else None,
                "contract_type": contract_type,
                "source_id": "DS-NSE-FO-EOD",
                "source_row": row_no,
            }
            records.append(record)

    if not records:
        raise SystemExit("Input CSV contains no data rows")

    keys = [(r["timestamp"], r["instrument_id"]) for r in records]
    if len(keys) != len(set(keys)):
        raise SystemExit("Duplicate canonical keys detected")

    output = {
        "dataset_id": "NSE-FO-EOD-" + sha256_file(args.input)[:16],
        "source": "NSE historical F&O EOD",
        "source_id": "DS-NSE-FO-EOD",
        "source_version": args.source_version,
        "raw_sha256": sha256_file(args.input),
        "available_at": available_at,
        "row_count": len(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Normalized {len(records)} rows -> {args.output}")
    print(f"Immutable dataset_id: {output['dataset_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
