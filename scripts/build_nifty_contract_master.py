#!/usr/bin/env python3
"""Build a contract-level NIFTY lot-size master for Phase 4A.

Legacy NSE bhavcopies do not carry NewBrdLotQty, so legacy observations are
mapped from the frozen NSE circular regimes. UDiFF observations carry
NewBrdLotQty and are preserved as source-observed values.

The implementation is vectorized over each daily normalized file because the
full historical snapshot contains millions of option rows.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

JULY_2021_WEEKLY = {
    pd.Timestamp("2021-07-01"),
    pd.Timestamp("2021-07-08"),
    pd.Timestamp("2021-07-15"),
    pd.Timestamp("2021-07-22"),
}


def legacy_map(df: pd.DataFrame) -> pd.DataFrame:
    """Map legacy rows to a uniquely identified NSE lot regime."""
    t = pd.to_datetime(df["trade_date"], errors="coerce").dt.normalize()
    e = pd.to_datetime(df["expiry"], errors="coerce").dt.normalize()

    lot = pd.Series(pd.NA, index=df.index, dtype="Int64")
    source = pd.Series(pd.NA, index=df.index, dtype="string")
    available = pd.Series(pd.NA, index=df.index, dtype="string")

    # NIFTY remained at 75 under FAOP44039, published 2020-03-31.
    m = t < pd.Timestamp("2021-04-30")
    lot[m] = 75
    source[m] = "NSE_FAOP44039"
    available[m] = "2020-03-31T23:59:59+00:00"

    # FAOP47854: May/June 2021 monthly expiries retain 75.
    m = (t >= pd.Timestamp("2021-04-30")) & (t <= pd.Timestamp("2021-06-25"))
    lot[m] = 75
    source[m] = "NSE_FAOP47854"
    available[m] = "2021-03-31T23:59:59+00:00"

    # July 2021 weekly expiries remain in the pre-revision 75 regime;
    # July 29 is the revised monthly expiry.
    m = e.isin(JULY_2021_WEEKLY)
    lot[m] = 75
    source[m] = "NSE_FAOP47854"
    available[m] = "2021-03-31T23:59:59+00:00"

    # From July 2021 monthly / August 2021 weekly onward, and existing
    # long-term contracts after the June expiry, lot size is 50.
    m = lot.isna() & (t < pd.Timestamp("2024-04-26"))
    lot[m] = 50
    source[m] = "NSE_FAOP47854"
    available[m] = "2021-03-31T23:59:59+00:00"

    # FAOP61415: April 25 2024 monthly expiry remains 50; every NIFTY
    # contract available for trading from April 26 onward is 25.
    m = t >= pd.Timestamp("2024-04-26")
    lot[m] = 25
    source[m] = "NSE_FAOP61415"
    available[m] = "2024-04-02T23:59:59+00:00"
    m = m & (e == pd.Timestamp("2024-04-25"))
    lot[m] = 50

    if lot.isna().any():
        bad = df.loc[lot.isna(), ["trade_date", "expiry"]].head().to_dict("records")
        raise ValueError(f"Unmapped legacy NIFTY lot rows: {bad}")

    return pd.DataFrame(
        {
            "lot_size": lot.astype("int64"),
            "source_version": source,
            "available_at": available,
        },
        index=df.index,
    )


def process_file(path: Path) -> pd.DataFrame:
    cols = [
        "trade_date", "expiry", "strike", "option_type", "lot_size",
        "available_at",
    ]
    df = pd.read_csv(path, usecols=lambda c: c in cols)
    required = set(cols[:5])
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{path}: missing columns {sorted(missing)}")

    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.normalize()
    df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce").dt.normalize()
    df["strike"] = pd.to_numeric(df["strike"], errors="coerce")
    df["lot_size"] = pd.to_numeric(df["lot_size"], errors="coerce")
    df["option_type"] = df["option_type"].astype("string").str.strip().str.upper()
    df = df[
        df["trade_date"].notna()
        & df["expiry"].notna()
        & df["strike"].gt(0)
        & df["option_type"].isin(["CE", "PE"])
        & df["expiry"].ge(df["trade_date"])
    ].copy()

    legacy = df["lot_size"].isna()
    if legacy.any():
        mapped = legacy_map(df.loc[legacy])
        df.loc[legacy, ["lot_size", "source_version", "available_at"]] = mapped

    observed = ~legacy
    df.loc[observed, "lot_size"] = df.loc[observed, "lot_size"].astype("int64")
    df.loc[observed, "source_version"] = "NSE_UDIFF_NewBrdLotQty"
    if "available_at" not in df.columns:
        df["available_at"] = pd.NA
    df.loc[observed & df["available_at"].isna(), "available_at"] = (
        df.loc[observed & df["available_at"].isna(), "trade_date"]
        .dt.tz_localize("Asia/Kolkata")
        .dt.tz_convert("UTC")
        .map(lambda x: x.isoformat())
    )

    # Canonical contract key. String strike is stable across daily files.
    df["contract_id"] = (
        "NIFTY|"
        + df["expiry"].dt.strftime("%Y-%m-%d")
        + "|"
        + df["strike"].map(lambda x: f"{x:g}")
        + "|"
        + df["option_type"]
    )
    return df[
        [
            "contract_id", "expiry", "strike", "option_type", "trade_date",
            "lot_size", "source_version", "available_at",
        ]
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized-dir", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    files = sorted(args.normalized_dir.rglob("normalized/*.csv"))
    if not files:
        # Also support a directory whose immediate contents are daily CSVs.
        files = sorted(args.normalized_dir.rglob("*.csv"))
    if not files:
        raise SystemExit(f"No normalized CSV files under {args.normalized_dir}")

    parts = [process_file(p) for p in files]
    x = pd.concat(parts, ignore_index=True)
    x = x.sort_values(["contract_id", "trade_date"]).reset_index(drop=True)

    # Collapse identical lot regimes to intervals. UDiFF available_at is an
    # observation-level timestamp and is therefore not part of the regime key.
    state_cols = ["lot_size", "source_version"]
    prev = x.groupby("contract_id")[state_cols].shift(1)
    changed = x[state_cols].ne(prev).any(axis=1)
    interval = changed.groupby(x["contract_id"]).cumsum()
    x["_interval"] = interval

    master = (
        x.groupby(["contract_id", "_interval"], sort=True, as_index=False)
        .agg(
            underlying_id=("contract_id", lambda _: "NIFTY50"),
            expiry=("expiry", "first"),
            strike=("strike", "first"),
            option_type=("option_type", "first"),
            lot_size=("lot_size", "first"),
            effective_from=("trade_date", "first"),
            effective_to=("trade_date", "last"),
            source_version=("source_version", "first"),
            available_at=("available_at", "first"),
        )
    )

    master["expiry"] = pd.to_datetime(master["expiry"]).dt.strftime("%Y-%m-%d")
    master["effective_from"] = pd.to_datetime(master["effective_from"]).dt.strftime("%Y-%m-%d")
    master["effective_to"] = pd.to_datetime(master["effective_to"]).dt.strftime("%Y-%m-%d")
    master["lot_size"] = master["lot_size"].astype(int)
    master = master[
        [
            "contract_id", "underlying_id", "expiry", "strike", "option_type",
            "lot_size", "effective_from", "effective_to", "available_at",
            "source_version",
        ]
    ]

    # Hard checks.
    assert master["lot_size"].gt(0).all()
    assert master["contract_id"].notna().all()
    assert not master.duplicated(["contract_id", "effective_from"]).any()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(args.output, index=False, quoting=csv.QUOTE_MINIMAL)
    print(
        f"Contract master: {len(master)} intervals from {len(x)} observations "
        f"across {len(files)} normalized files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
