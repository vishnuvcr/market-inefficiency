#!/usr/bin/env python3
"""Acquire official NIFTY 50 price-index OHLC from NSE Indices.

Bootstrap an official reports-page session before the historical-data POST.
If the site returns an anti-bot/HTML response, fail with diagnostics rather
than attempting to parse it as JSON.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://www.nseindia.com/api/historicalOR/indicesHistory"
BOOTSTRAP_URL = "https://www.nseindia.com/reports-indices-historical-index-data"
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": "https://www.niftyindices.com",
    "Referer": BOOTSTRAP_URL,
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}


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

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    start_dt = datetime.strptime(args.start, "%Y-%m-%d")
    end_dt = datetime.strptime(args.end, "%Y-%m-%d")

    session = requests.Session()
    session.headers.update({
        "User-Agent": HEADERS["User-Agent"],
        "Accept": "application/json, text/plain, */*",
        "Referer": BOOTSTRAP_URL,
        "Origin": "https://www.nseindia.com",
        "X-Requested-With": "XMLHttpRequest",
    })

    bootstrap = session.get(BOOTSTRAP_URL, timeout=20)
    bootstrap.raise_for_status()

    rows = []
    # NSE's official historical-index endpoint accepts date-bounded requests.
    # Use yearly chunks to keep requests bounded and reproducible.
    cur = start_dt
    while cur <= end_dt:
        chunk_end = min(end_dt, datetime(cur.year, 12, 31))
        params = {
            "indexType": "NIFTY 50",
            "from": cur.strftime("%d-%m-%Y"),
            "to": chunk_end.strftime("%d-%m-%Y"),
        }
        response = session.get(URL, params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
        chunk_rows = payload.get("data", payload if isinstance(payload, list) else [])
        if not chunk_rows:
            raise SystemExit(
                f"NSE official historical index endpoint returned no rows for "
                f"{cur:%Y-%m-%d}..{chunk_end:%Y-%m-%d}; keys={list(payload) if isinstance(payload, dict) else 'list'}"
            )
        rows.extend(chunk_rows)
        cur = chunk_end + __import__("datetime").timedelta(days=1)

    if not rows:
        raise SystemExit("NSE official historical index endpoint returned no rows")

    # Normalize the NSE endpoint's field names into the Phase 4A schema.
    normalized = []
    for row in rows:
        date_value = row.get("EOD_TIMESTAMP") or row.get("CH_TIMESTAMP") or row.get("TIMESTAMP")
        close = row.get("EOD_CLOSE_INDEX_VAL") or row.get("CLOSE_INDEX_VAL") or row.get("CLOSE")
        op = row.get("EOD_OPEN_INDEX_VAL") or row.get("OPEN_INDEX_VAL") or row.get("OPEN")
        hi = row.get("EOD_HIGH_INDEX_VAL") or row.get("HIGH_INDEX_VAL") or row.get("HIGH")
        lo = row.get("EOD_LOW_INDEX_VAL") or row.get("LOW_INDEX_VAL") or row.get("LOW")
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
        raise SystemExit(
            f"NSE historical index response fields not recognized; sample keys={sorted(rows[0].keys())}"
        )

    rows = normalized
    response = session.post(
        URL,
        headers=HEADERS,
        json={"cinfo": cinfo},
        timeout=60,
    )
    response.raise_for_status()

    raw = out / "response.json"
    raw.write_text(response.text, encoding="utf-8")

    try:
        payload = response.json()
    except ValueError as exc:
        prefix = response.text[:500].replace("\n", " ")
        raise SystemExit(
            f"NIFTY historical endpoint returned non-JSON "
            f"(status={response.status_code}, "
            f"content_type={response.headers.get('content-type')}, "
            f"prefix={prefix!r})"
        ) from exc

    if "d" not in payload:
        raise SystemExit(
            f"NIFTY historical endpoint JSON lacks 'd'; "
            f"keys={sorted(payload)}"
        )

    body = payload["d"]
    try:
        rows = json.loads(body) if isinstance(body, str) else body
    except json.JSONDecodeError as exc:
        raise SystemExit(
            "NIFTY historical endpoint returned invalid 'd' JSON"
        ) from exc

    if not rows:
        raise SystemExit("NIFTY 50 historical endpoint returned no rows")

    required = {"HistoricalDate", "OPEN", "HIGH", "LOW", "CLOSE"}
    missing = required - set(rows[0])
    if missing:
        raise SystemExit(
            f"NIFTY historical rows missing fields: {sorted(missing)}"
        )

    csv_path = out / "nifty50_ohlc.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "open", "high", "low", "close"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "date": row.get("HistoricalDate"),
                    "open": row.get("OPEN"),
                    "high": row.get("HIGH"),
                    "low": row.get("LOW"),
                    "close": row.get("CLOSE"),
                }
            )

    manifest = {
        "source_url": URL,
        "bootstrap_url": BOOTSTRAP_URL,
        "index": "NIFTY 50",
        "requested_period": [args.start, args.end],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": len(rows),
        "raw_sha256": sha256(raw),
        "csv_sha256": sha256(csv_path),
        "session_cookie_names": sorted(session.cookies.keys()),
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
