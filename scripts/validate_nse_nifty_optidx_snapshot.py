#!/usr/bin/env python3
"""Validate normalized NSE NIFTY OPTIDX EOD snapshot files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

KEY = ["trade_date", "expiry", "strike", "option_type"]
REQUIRED = KEY + [
    "open", "high", "low", "close", "last_price", "settlement",
    "volume", "turnover", "open_interest", "change_in_oi",
    "underlying_price", "lot_size", "timestamp",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/nse_option_snapshot")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    root = Path(args.root)
    files = sorted((root / "normalized").glob("*.csv"))
    if not files:
        raise SystemExit("No normalized snapshot files found")

    frames = []
    file_errors = []
    for p in files:
        try:
            df = pd.read_csv(p)
            missing = sorted(set(REQUIRED) - set(df.columns))
            if missing:
                file_errors.append({"file": str(p), "error": "missing_columns", "columns": missing})
                continue
            df["_source_file"] = p.name
            frames.append(df)
        except Exception as exc:
            file_errors.append({"file": str(p), "error": f"{type(exc).__name__}: {exc}"})

    if not frames:
        raise SystemExit(json.dumps({"file_errors": file_errors}, indent=2))
    x = pd.concat(frames, ignore_index=True)

    for c in ["trade_date", "expiry"]:
        x[c] = pd.to_datetime(x[c], errors="coerce")
    for c in ["strike", "open", "high", "low", "close", "last_price",
              "settlement", "volume", "turnover", "open_interest",
              "change_in_oi", "underlying_price", "lot_size"]:
        x[c] = pd.to_numeric(x[c], errors="coerce")

    checks = {
        "rows": int(len(x)),
        "files": int(len(files)),
        "file_errors": file_errors,
        "non_nifty_option_type": int((~x["option_type"].isin(["CE", "PE"])).sum()),
        "missing_trade_date": int(x["trade_date"].isna().sum()),
        "missing_expiry": int(x["expiry"].isna().sum()),
        "nonpositive_strike": int((x["strike"] <= 0).sum()),
        "expiry_before_trade": int((x["expiry"] < x["trade_date"]).sum()),
        "duplicate_contract_keys": int(x.duplicated(KEY).sum()),
        "negative_prices": int((x[["open","high","low","close","last_price","settlement"]] < 0).any(axis=1).sum()),
        "negative_volume": int((x["volume"] < 0).sum()),
        "negative_open_interest": int((x["open_interest"] < 0).sum()),
        "negative_lot_size": int((x["lot_size"] < 0).sum()),
        "zero_volume_rows": int((x["volume"] == 0).sum()),
        "zero_oi_rows": int((x["open_interest"] == 0).sum()),
        "missing_underlying": int(x["underlying_price"].isna().sum()),
        "missing_lot_size": int(x["lot_size"].isna().sum()),
        "ce_rows": int((x["option_type"] == "CE").sum()),
        "pe_rows": int((x["option_type"] == "PE").sum()),
        "unique_expiries": int(x["expiry"].nunique()),
        "unique_trade_dates": int(x["trade_date"].nunique()),
    }

    hard_fail = [
        "file_errors", "non_nifty_option_type", "missing_trade_date",
        "missing_expiry", "nonpositive_strike", "expiry_before_trade",
        "duplicate_contract_keys", "negative_prices", "negative_volume",
        "negative_open_interest", "negative_lot_size",
    ]
    failures = {k: checks[k] for k in hard_fail if checks[k] not in (0, [])}
    result = {"status": "PASS" if not failures else "FAIL", "checks": checks, "failures": failures}
    print(json.dumps(result, indent=2, default=str))
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, default=str) + "\n")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
