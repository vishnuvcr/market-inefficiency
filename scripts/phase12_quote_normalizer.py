#!/usr/bin/env python3
"""Normalize common public NIFTY L1/L2 quote schemas into one fail-closed form.

The adapter intentionally does not infer expiry, strike or lot size from a
provider-specific symbol string. Contract identity must come from the PIT
contract master in the economic dataset.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from phase12_execution_simulator import Quote, validate_quote


@dataclass(frozen=True)
class NormalizedQuote:
    source_schema: str
    symbol: str
    timestamp: str
    bid: float
    bid_qty: float
    ask: float
    ask_qty: float
    depth: tuple[tuple[float, float, float, float], ...]
    ltp: float | None
    volume: float | None


def _pick(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    raise KeyError("|".join(names))


def _float(row: dict[str, str], *names: str) -> float:
    return float(_pick(row, *names))


def detect_schema(fieldnames: list[str]) -> str:
    fields = set(fieldnames)
    if {"bid_px", "ask_px", "bid_qty", "ask_qty"} <= fields:
        return "tickbytes_l1"
    if {"bid_price1", "ask_price1", "bid_qty1", "ask_qty1"} <= fields:
        return "optionvault_l2"
    raise ValueError("unsupported quote schema")


def normalize_row(row: dict[str, str], schema: str) -> NormalizedQuote:
    symbol = _pick(row, "symbol")
    timestamp = _pick(row, "datetime", "timestamp")
    bid = _float(row, "bid_px", "bid_price1")
    bid_qty = _float(row, "bid_qty", "bid_qty1")
    ask = _float(row, "ask_px", "ask_price1")
    ask_qty = _float(row, "ask_qty", "ask_qty1")

    depth = []
    for level in range(1, 6):
        if schema == "tickbytes_l1":
            if level == 1:
                bp, bq, ap, aq = "bid_px", "bid_qty", "ask_px", "ask_qty"
            else:
                bp = f"bid_px_{level}"
                bq = f"bid_qty_{level}"
                ap = f"ask_px_{level}"
                aq = f"ask_qty_{level}"
        else:
            bp = f"bid_price{level}"
            bq = f"bid_qty{level}"
            ap = f"ask_price{level}"
            aq = f"ask_qty{level}"

        values = (row.get(bp, ""), row.get(bq, ""), row.get(ap, ""), row.get(aq, ""))
        if any(v in ("", None) for v in values):
            depth.append((float("nan"), float("nan"), float("nan"), float("nan")))
        else:
            depth.append(tuple(float(v) for v in values))

    ltp = float(row["ltp"]) if row.get("ltp") not in ("", None) else None
    volume = float(row["volume"]) if row.get("volume") not in ("", None) else None

    q = Quote(symbol, timestamp, bid, bid_qty, ask, ask_qty)
    validate_quote(q)
    return NormalizedQuote(
        schema, symbol, timestamp, bid, bid_qty, ask, ask_qty,
        tuple(depth), ltp, volume
    )


def load(path: Path) -> tuple[str, list[NormalizedQuote], list[str]]:
    normalized = []
    errors = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        schema = detect_schema(reader.fieldnames or [])
        for line_no, row in enumerate(reader, start=2):
            try:
                normalized.append(normalize_row(row, schema))
            except Exception as exc:
                errors.append(f"line {line_no}: {exc}")
    return schema, normalized, errors


def main() -> None:
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    args = ap.parse_args()
    schema, rows, errors = load(args.input)
    print(json.dumps({"schema": schema, "rows": len(rows), "errors": errors[:25]}, indent=2))
    if not rows:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
