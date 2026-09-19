#!/usr/bin/env python3
"""NSE FAO historical order/trade normalizer for Phase 10.

Supports NSE v1.18 trim and the historically relevant full-layout lengths.
It intentionally parses only the common fields needed for execution research
and preserves the raw line length/layout metadata so no schema boundary is
silently crossed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv
import gzip
import hashlib
import json
import re
from typing import Iterable


JIF_PER_SECOND = 65536
EPOCH_GMT = datetime(1980, 1, 1, tzinfo=timezone.utc)

ORDER_FIELDS = [
    ("record_indicator", 2),
    ("segment", 4),
    ("order_number", 16),
    ("jiffies", 14),
    ("side", 1),
    ("activity", 1),
    ("symbol", 10),
    ("instrument", 6),
    ("expiry", 9),
    ("strike_paise", 8),
    ("option_type", 2),
    ("quantity_lots", 8),
    ("limit_price_paise", 8),
    ("spread_type", 1),
    ("spread_price_sign", 1),
]

TRADE_FIELDS = [
    ("record_indicator", 2),
    ("segment", 4),
    ("jiffies", 14),
    ("symbol", 10),
    ("instrument", 6),
    ("expiry", 9),
    ("strike_paise", 8),
    ("option_type", 2),
    ("trade_price_paise", 8),
    ("quantity_lots", 8),
    ("buy_order_number", 16),
    ("sell_order_number", 16),
]

VALID_ORDER_LENGTHS = {91: "trim-v1.18", 111: "full-pre-2022-02", 112: "full-v1.18"}
VALID_TRADE_LENGTHS = {103: "trim-v1.18", 123: "full-pre-2020-09-07", 124: "full-v1.18"}


def _slices(spec):
    pos = 0
    out = []
    for name, width in spec:
        out.append((name, pos, pos + width))
        pos += width
    return out, pos


ORDER_SLICES, ORDER_COMMON_WIDTH = _slices(ORDER_FIELDS)
TRADE_SLICES, TRADE_COMMON_WIDTH = _slices(TRADE_FIELDS)


def jiffies_to_utc(jiffies: int) -> datetime:
    return EPOCH_GMT + timedelta(seconds=jiffies / JIF_PER_SECOND)


def _strip_field(x: str) -> str:
    return x.strip(" \t\r\n")


def _int_field(x: str, name: str) -> int:
    x = _strip_field(x)
    if not x or not x.isdigit():
        raise ValueError(f"invalid {name}: {x!r}")
    return int(x)


def _price_paise(x: str, name: str) -> float:
    v = _int_field(x, name)
    return v / 100.0


def _parse_fixed(line: str, slices, expected_length: int) -> dict[str, str]:
    if len(line) != expected_length:
        raise ValueError(f"record length {len(line)} != expected {expected_length}")
    return {name: line[a:b] for name, a, b in slices}


def parse_order_line(line: str, session_date: str, source_file: str = "") -> dict:
    raw = line.rstrip("\r\n")
    length = len(raw)
    if length not in VALID_ORDER_LENGTHS:
        raise ValueError(f"unsupported FAO order record length: {length}")
    f = _parse_fixed(raw, ORDER_SLICES, ORDER_COMMON_WIDTH)
    symbol = _strip_field(f["symbol"]).lstrip("b")
    j = _int_field(f["jiffies"], "jiffies")
    event = jiffies_to_utc(j)
    return {
        "source_file": source_file,
        "source_format": VALID_ORDER_LENGTHS[length],
        "raw_record_length": length,
        "session_date": session_date,
        "record_indicator": _strip_field(f["record_indicator"]),
        "segment": _strip_field(f["segment"]),
        "order_number": _int_field(f["order_number"], "order_number"),
        "event_time": event.isoformat(),
        "side": _strip_field(f["side"]),
        "activity": _int_field(f["activity"], "activity"),
        "symbol": symbol,
        "instrument": _strip_field(f["instrument"]),
        "expiry": _strip_field(f["expiry"]),
        "strike": _price_paise(f["strike_paise"], "strike"),
        "option_type": _strip_field(f["option_type"]),
        "quantity_lots": _int_field(f["quantity_lots"], "quantity_lots"),
        "limit_price": _price_paise(f["limit_price_paise"], "limit_price"),
        "spread_type": _strip_field(f["spread_type"]),
        "spread_price_sign": _strip_field(f["spread_price_sign"]),
    }


def parse_trade_line(line: str, session_date: str, source_file: str = "") -> dict:
    raw = line.rstrip("\r\n")
    length = len(raw)
    if length not in VALID_TRADE_LENGTHS:
        raise ValueError(f"unsupported FAO trade record length: {length}")
    f = _parse_fixed(raw, TRADE_SLICES, TRADE_COMMON_WIDTH)
    symbol = _strip_field(f["symbol"]).lstrip("b")
    j = _int_field(f["jiffies"], "jiffies")
    event = jiffies_to_utc(j)
    return {
        "source_file": source_file,
        "source_format": VALID_TRADE_LENGTHS[length],
        "raw_record_length": length,
        "session_date": session_date,
        "record_indicator": _strip_field(f["record_indicator"]),
        "segment": _strip_field(f["segment"]),
        "event_time": event.isoformat(),
        "symbol": symbol,
        "instrument": _strip_field(f["instrument"]),
        "expiry": _strip_field(f["expiry"]),
        "strike": _price_paise(f["strike_paise"], "strike"),
        "option_type": _strip_field(f["option_type"]),
        "trade_price": _price_paise(f["trade_price_paise"], "trade_price"),
        "quantity_lots": _int_field(f["quantity_lots"], "quantity_lots"),
        "buy_order_number": _int_field(f["buy_order_number"], "buy_order_number"),
        "sell_order_number": _int_field(f["sell_order_number"], "sell_order_number"),
    }


def contract_key(row: dict) -> tuple:
    return (
        row["symbol"],
        row["instrument"],
        row["expiry"],
        float(row["strike"]),
        row["option_type"],
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalize_gz(path: Path, kind: str, session_date: str, output: Path) -> dict:
    parser = parse_order_line if kind == "orders" else parse_trade_line
    output.parent.mkdir(parents=True, exist_ok=True)
    accepted = 0
    rejected = 0
    errors: list[str] = []
    digest = sha256_file(path)
    with gzip.open(path, "rt", encoding="utf-8", errors="strict") as fh, output.open("w", newline="", encoding="utf-8") as out:
        writer = None
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                row = parser(line, session_date, path.name)
            except Exception as exc:
                rejected += 1
                if len(errors) < 25:
                    errors.append(f"line {line_no}: {exc}")
                continue
            if writer is None:
                writer = csv.DictWriter(out, fieldnames=list(row.keys()))
                writer.writeheader()
            writer.writerow(row)
            accepted += 1
    report = {
        "status": "PASS" if rejected == 0 else "PASS_WITH_REJECTIONS",
        "kind": kind,
        "source_file": str(path),
        "sha256": digest,
        "accepted_records": accepted,
        "rejected_records": rejected,
        "errors_sample": errors,
    }
    return report


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--kind", choices=["orders", "trades"], required=True)
    ap.add_argument("--session-date", required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    a = ap.parse_args()
    r = normalize_gz(a.input, a.kind, a.session_date, a.output)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(r, indent=2))
    if r["rejected_records"]:
        raise SystemExit(2)
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
