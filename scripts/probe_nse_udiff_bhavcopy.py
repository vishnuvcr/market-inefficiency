#!/usr/bin/env python3
"""Validate one official NSE F&O UDiFF Common Bhavcopy archive.

The URL pattern is tested against a fixed historical trading date. The script
validates the ZIP/CSV container and records the observed schema and NIFTY
option-row counts; it does not infer completeness from a single day.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://archives.nseindia.com/content/fo"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/all-reports-derivatives",
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--date", default="2026-05-14")
    p.add_argument("--output", default="data/nse_probe/udiff_bhavcopy_probe.json")
    args = p.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d")
    stamp = dt.strftime("%Y%m%d")
    filename = f"BhavCopy_NSE_FO_0_0_0_{stamp}_F_0000.csv.zip"
    url = f"{BASE}/{filename}"

    result = {
        "probe_utc": datetime.now(timezone.utc).isoformat(),
        "trade_date": args.date,
        "url": url,
        "diagnostic_only": True,
        "execution_backtest_allowed": False,
    }

    try:
        response = requests.get(url, headers=HEADERS, timeout=60)
        result["http_status"] = response.status_code
        result["content_type"] = response.headers.get("content-type")
        result["bytes"] = len(response.content)
        result["sha256"] = hashlib.sha256(response.content).hexdigest()

        if response.status_code != 200:
            result["status"] = "HTTP_NOT_OK"
        else:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                names = zf.namelist()
                result["zip_members"] = names
                csv_names = [n for n in names if n.lower().endswith(".csv")]
                if not csv_names:
                    result["status"] = "NO_CSV_MEMBER"
                else:
                    member = csv_names[0]
                    raw = zf.read(member)
                    result["csv_member"] = member
                    result["csv_bytes"] = len(raw)
                    df = pd.read_csv(io.BytesIO(raw), nrows=1000)
                    result["columns"] = df.columns.tolist()
                    result["sample_rows"] = len(df)

                    required = [
                        "TradDt", "FinInstrmTp", "TckrSymb", "XpryDt",
                        "StrkPric", "OptnTp", "OpnPric", "HghPric",
                        "LwPric", "ClsPric", "SttlmPric", "OpnIntrst",
                    ]
                    result["required_columns_present"] = {
                        c: c in df.columns for c in required
                    }

                    # Read only the columns needed for a full NIFTY count.
                    usecols = [c for c in required if c in df.columns]
                    full = pd.read_csv(io.BytesIO(raw), usecols=usecols)
                    if "TckrSymb" in full.columns:
                        nifty = full[full["TckrSymb"].astype(str).str.upper().eq("NIFTY")]
                        result["nifty_rows"] = int(len(nifty))
                        if "OptnTp" in nifty.columns:
                            result["nifty_option_rows"] = int(
                                nifty["OptnTp"].astype(str).isin(["CE", "PE"]).sum()
                            )
                    result["status"] = "VALIDATED_CONTAINER_AND_SCHEMA"
    except (requests.RequestException, zipfile.BadZipFile, pd.errors.ParserError) as exc:
        result["status"] = "ERROR"
        result["error"] = f"{type(exc).__name__}: {exc}"

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
