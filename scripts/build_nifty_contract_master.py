#!/usr/bin/env python3
"""Build a contract-level NIFTY lot-size master for Phase 4A.

Legacy NSE bhavcopies do not carry NewBrdLotQty, so legacy observations are
mapped only where the frozen NSE circular rules identify a unique lot size.
UDiFF observations carry NewBrdLotQty and are preserved as source-observed
values.

The output is an interval master keyed by:
    NIFTY|expiry|strike|option_type
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date, datetime, time, timezone
from pathlib import Path

import pandas as pd


def d(value: object) -> date | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    return pd.to_datetime(value, errors="coerce").date()


def contract_id(expiry: date, strike: float, option_type: str) -> str:
    return f"NIFTY|{expiry.isoformat()}|{strike:g}|{option_type}"


def legacy_rule(trade_date: date, expiry: date) -> tuple[int, str, str]:
    """Return lot, source version, source publication date for legacy rows."""
    # NSE FAOP47854: 75 through June 2021; July monthly and later monthly
    # contracts are 50; August 2021 weekly and later are 50. The July 2021
    # weekly expiries are the only transitional weekly observations and remain
    # under the pre-revision 75 regime.
    july_weekly = {
        date(2021, 7, 1),
        date(2021, 7, 8),
        date(2021, 7, 15),
        date(2021, 7, 22),
    }
    if trade_date <= date(2021, 6, 25):
        return 75, "NSE_FAOP47854", "2021-03-31"
    if expiry in july_weekly:
        return 75, "NSE_FAOP47854", "2021-03-31"
    if expiry >= date(2021, 7, 29):
        return 50, "NSE_FAOP47854", "2021-03-31"
    # Existing long-term contracts were revised after June 25 EOD.
    if trade_date >= date(2021, 6, 28) and expiry > date(2021, 6, 25):
        return 50, "NSE_FAOP47854", "2021-03-31"
    raise ValueError(
        f"Ambiguous legacy NIFTY lot regime: trade_date={trade_date}, "
        f"expiry={expiry}"
    )


def legacy_lot(trade_date: date, expiry: date) -> tuple[int, str, str]:
    # FAOP61415: the April 25 2024 monthly expiry remains 50; every NIFTY
    # contract available for trading from April 26 onward uses 25.
    if trade_date >= date(2024, 4, 26):
        if expiry == date(2024, 4, 25):
            return 50, "NSE_FAOP61415", "2024-04-02"
        return 25, "NSE_FAOP61415", "2024-04-02"
    return legacy_rule(trade_date, expiry)


def iso_eod_utc(publication_date: str) -> str:
    dt = datetime.combine(
        date.fromisoformat(publication_date), time(23, 59, 59)
    ).replace(tzinfo=timezone.utc)
    return dt.isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized-dir", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    files = sorted(args.normalized_dir.rglob("*.csv"))
    if not files:
        raise SystemExit(f"No normalized CSV files under {args.normalized_dir}")

    intervals = defaultdict(list)
    row_count = 0
    legacy_count = 0
    observed_count = 0

    for path in files:
        df = pd.read_csv(path)
        required = {"trade_date", "expiry", "strike", "option_type", "lot_size"}
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"{path}: missing columns {sorted(missing)}")

        for row in df.itertuples(index=False):
            trade_date = d(getattr(row, "trade_date"))
            expiry = d(getattr(row, "expiry"))
            strike = float(getattr(row, "strike"))
            option_type = str(getattr(row, "option_type")).strip().upper()
            if trade_date is None or expiry is None or strike <= 0 or option_type not in {"CE", "PE"}:
                continue
            if expiry < trade_date:
                raise SystemExit(f"{path}: expiry before trade date")

            raw_lot = getattr(row, "lot_size")
            if pd.notna(raw_lot) and float(raw_lot) > 0:
                lot = int(float(raw_lot))
                source_version = "NSE_UDIFF_NewBrdLotQty"
                source_available = getattr(row, "available_at", None)
                if pd.isna(source_available) or str(source_available).strip() == "":
                    source_available = (
                        pd.Timestamp(trade_date, tz="Asia/Kolkata")
                        .tz_convert("UTC")
                        .isoformat()
                    )
                observed_count += 1
            else:
                lot, source_version, pub_date = legacy_lot(trade_date, expiry)
                source_available = iso_eod_utc(pub_date)
                legacy_count += 1

            key = contract_id(expiry, strike, option_type)
            intervals[key].append({
                "trade_date": trade_date,
                "lot_size": lot,
                "source_version": source_version,
                "available_at": str(source_available),
                "expiry": expiry,
                "strike": strike,
                "option_type": option_type,
            })
            row_count += 1

    output = []
    for key, records in sorted(intervals.items()):
        records.sort(key=lambda x: x["trade_date"])
        current = None
        for rec in records:
            state = (rec["lot_size"], rec["source_version"], rec["available_at"])
            if current is None or state != current["state"]:
                if current is not None:
                    current["effective_to"] = (rec["trade_date"] - pd.Timedelta(days=1)).date().isoformat()
                    output.append(current["row"])
                current = {
                    "state": state,
                    "row": {
                        "contract_id": key,
                        "underlying_id": "NIFTY50",
                        "expiry": rec["expiry"].isoformat(),
                        "strike": rec["strike"],
                        "option_type": rec["option_type"],
                        "lot_size": rec["lot_size"],
                        "effective_from": rec["trade_date"].isoformat(),
                        "effective_to": None,
                        "available_at": rec["available_at"],
                        "source_version": rec["source_version"],
                    },
                }
        if current is not None:
            current["row"]["effective_to"] = records[-1]["trade_date"].isoformat()
            output.append(current["row"])

    # Reject contradictory overlapping source states.
    seen = set()
    for row in output:
        key = (row["contract_id"], row["effective_from"])
        if key in seen:
            raise SystemExit(f"Duplicate master interval: {key}")
        seen.add(key)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "contract_id", "underlying_id", "expiry", "strike", "option_type",
        "lot_size", "effective_from", "effective_to", "available_at",
        "source_version",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    print(
        f"Contract master: {len(output)} intervals from {row_count} observations "
        f"(legacy={legacy_count}, UDiFF-observed={observed_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
