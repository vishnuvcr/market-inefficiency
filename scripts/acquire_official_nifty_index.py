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
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

URL = "https://www.nseindia.com/api/historicalOR/indicesHistory"
BOOTSTRAP_URL = "https://www.nseindia.com/reports-indices-historical-index-data"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)
CHUNK_DAYS = 60
REQUEST_RETRIES = 4
BOOTSTRAP_TIMEOUT = 60
REQUEST_TIMEOUT = 90


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

    # NSE occasionally stalls on the bootstrap page. Retry transient
    # network/server failures without bypassing the public endpoint.
    for attempt in range(REQUEST_RETRIES):
        try:
            bootstrap = session.get(BOOTSTRAP_URL, timeout=BOOTSTRAP_TIMEOUT)
            bootstrap.raise_for_status()
            break
        except requests.RequestException:
            if attempt == REQUEST_RETRIES - 1:
                raise
            time.sleep(2.0 * (attempt + 1))

    rows = []
    raw_files = []
    chunk_audits = []
    cur = start
    while cur <= end:
        chunk_end = min(end, cur + timedelta(days=CHUNK_DAYS - 1))
        params = {
            "indexType": "NIFTY 50",
            "from": cur.strftime("%d-%m-%Y"),
            "to": chunk_end.strftime("%d-%m-%Y"),
        }
        response = None
        for attempt in range(REQUEST_RETRIES):
            try:
                response = session.get(URL, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                break
            except requests.RequestException:
                if attempt == REQUEST_RETRIES - 1:
                    raise
                try:
                    session.get(BOOTSTRAP_URL, timeout=BOOTSTRAP_TIMEOUT).raise_for_status()
                except requests.RequestException:
                    pass
                time.sleep(2.0 * (attempt + 1))
        if response is None:
            raise SystemExit("NSE request failed without a response")
        try:
            payload = response.json()
        except ValueError as exc:
            raise SystemExit(
                f"NSE historical index endpoint returned non-JSON: "
                f"status={response.status_code}, "
                f"content_type={response.headers.get('content-type')}"
            ) from exc

        chunk_rows = payload.get("data", payload if isinstance(payload, list) else [])
        if not chunk_rows:
            raise SystemExit(
                f"NSE historical index endpoint returned no rows for "
                f"{cur:%Y-%m-%d}..{chunk_end:%Y-%m-%d}; "
                f"keys={sorted(payload) if isinstance(payload, dict) else 'list'}"
            )

        raw_path = raw_dir / (
            f"nifty50_{cur:%Y%m%d}_{chunk_end:%Y%m%d}.json"
        )
        raw_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        raw_files.append({
            "file": str(raw_path),
            "sha256": sha256(raw_path),
            "requested_start": cur.strftime("%Y-%m-%d"),
            "requested_end": chunk_end.strftime("%Y-%m-%d"),
            "rows_returned": len(chunk_rows),
        })
        chunk_audits.append({
            "requested_start": cur.strftime("%Y-%m-%d"),
            "requested_end": chunk_end.strftime("%Y-%m-%d"),
            "rows_returned": len(chunk_rows),
        })

        rows.extend(chunk_rows)
        cur = chunk_end + timedelta(days=1)
        time.sleep(0.25)

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

    # Canonicalize dates, remove cross-chunk duplicates, and sort chronologically.
    for row in normalized:
        row["date"] = datetime.strptime(
            row["date"], "%d-%b-%Y"
        ).strftime("%Y-%m-%d")

    by_date = {}
    for row in normalized:
        existing = by_date.get(row["date"])
        if existing is not None and existing != row:
            raise SystemExit(f"Conflicting duplicate NIFTY 50 row for {row['date']}")
        by_date[row["date"]] = row
    normalized = [by_date[d] for d in sorted(by_date)]

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
        "chunk_days": CHUNK_DAYS,
        "rows": len(normalized),
        "raw_files": raw_files,
        "chunk_audits": chunk_audits,
        "csv_sha256": sha256(csv_path),
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
