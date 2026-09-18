#!/usr/bin/env python3
"""Acquire official NIFTY 50 daily OHLC from NSE's historical-index endpoint.

The data source is the official NSE historical index service. Raw JSON
responses are preserved and the normalized file is hashed. No third-party
market-data series is used.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

URL = "https://www.nseindia.com/api/historicalOR/indicesHistory"
BOOTSTRAP_URL = "https://www.nseindia.com/reports-indices-historical-index-data"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--output", default="data/phase4a/external/nifty_index")
    args = ap.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    if start > end:
        raise SystemExit("--start must be <= --end")

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw"
    raw_dir.mkdir(exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": BOOTSTRAP_URL,
        "Origin": "https://www.nseindia.com",
        "X-Requested-With": "XMLHttpRequest",
    })

    bootstrap = session.get(BOOTSTRAP_URL, timeout=20)
    bootstrap.raise_for_status()

    rows = []
    raw_files = []
    cur = start
    while cur <= end:
        chunk_end = min(end, datetime(cur.year, 12, 31))
        params = {
            "indexType": "NIFTY 50",
            "from": cur.strftime("%d-%m-%Y"),
            "to": chunk_end.strftime("%d-%m-%Y"),
        }
        response = session.get(URL, params=params, timeout=60)
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise SystemExit(
                f"NSE historical index endpoint returned non-JSON: "
                f"status={response.status_code}, "
                f"content_type={response.headers.get('content-type')}"
            ) from exc

        raw_path = raw_dir / f"nifty50_{cur.year}.json"
        raw_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        raw_files.append({
            "file": str(raw_path),
            "sha256": sha256(raw_path),
            "requested_start": cur.strftime("%Y-%m-%d"),
            "requested_end": chunk_end.strftime("%Y-%m-%d"),
        })

        chunk_rows = payload.get("data", payload if isinstance(payload, list) else [])
        if not chunk_rows:
            raise SystemExit(
                f"NSE historical index endpoint returned no rows for "
                f"{cur:%Y-%m-%d}..{chunk_end:%Y-%m-%d}; "
                f"keys={sorted(payload) if isinstance(payload, dict) else 'list'}"
            )
        rows.extend(chunk_rows)
        cur = chunk_end + timedelta(days=1)

    normalized = []
    for row in rows:
        date_value = (
            row.get("EOD_TIMESTAMP")
            or row.get("CH_TIMESTAMP")
            or row.get("TIMESTAMP")
        )
        close = (
            row.get("EOD_CLOSE_INDEX_VAL")
            or row.get("CLOSE_INDEX_VAL")
            or row.get("CLOSE")
        )
        op = (
            row.get("EOD_OPEN_INDEX_VAL")
            or row.get("OPEN_INDEX_VAL")
            or row.get("OPEN")
        )
        hi = (
            row.get("EOD_HIGH_INDEX_VAL")
            or row.get("HIGH_INDEX_VAL")
            or row.get("HIGH")
        )
        lo = (
            row.get("EOD_LOW_INDEX_VAL")
            or row.get("LOW_INDEX_VAL")
            or row.get("LOW")
        )
        if date_value is None or close is None:
            continue
        normalized.append({
            "date": date_value,
            "open": op,
            "high": hi,
            "low": lo,
            "close": close,
        })

    if not normalized:
        sample_keys = sorted(rows[0].keys()) if rows else []
        raise SystemExit(
            f"NSE historical index response fields not recognized; "
            f"sample keys={sample_keys}"
        )

    csv_path = out / "nifty50_ohlc.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "open", "high", "low", "close"]
        )
        writer.writeheader()
        writer.writerows(normalized)

    manifest = {
        "status": "PASS",
        "source": "NSE India Historical Index Data",
        "source_url": URL,
        "bootstrap_url": BOOTSTRAP_URL,
        "index": "NIFTY 50",
        "requested_period": [args.start, args.end],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": len(normalized),
        "raw_files": raw_files,
        "csv_sha256": sha256(csv_path),
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
