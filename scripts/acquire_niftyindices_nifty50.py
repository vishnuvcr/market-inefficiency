#!/usr/bin/env python3
"""Acquire official NIFTY 50 daily OHLC from NSE Indices historical-data service.

This is the public historical-price service linked by NSE's historical index
data page and operated by NSE Indices Limited. It is used only as a fallback
when the NSE India historical-index API serves an HTML response in the CI
environment.

Endpoint:
  POST https://www.niftyindices.com/BackPage/getHistoricaldatatabletoString

The request uses the normal browser-style HTTP headers expected by the public
site; it does not use cloudscraper or another anti-bot bypass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.niftyindices.com/BackPage/getHistoricaldatatabletoString"
REFERER = "https://www.niftyindices.com/reports/historical-data"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)
REQUEST_RETRIES = 4
REQUEST_TIMEOUT = 90


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_rows(payload):
    if isinstance(payload, dict) and "d" in payload:
        data = payload["d"]
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise SystemExit("Nifty Indices response d-field was not valid JSON") from exc
        payload = data
    if not isinstance(payload, list):
        raise SystemExit(f"Unexpected Nifty Indices response type: {type(payload).__name__}")
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--output", default="data/phase4a/external/nifty_index")
    args = ap.parse_args()

    start = pd.Timestamp(args.start).normalize()
    end = pd.Timestamp(args.end).normalize()
    if start > end:
        raise SystemExit("--start must be <= --end")

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw_niftyindices"
    raw_dir.mkdir(exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": UA,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.niftyindices.com",
            "Referer": REFERER,
        }
    )

    cinfo = (
        "{'name':'NIFTY 50',"
        f"'startDate':'{start.strftime('%d-%b-%Y')}',"
        f"'endDate':'{end.strftime('%d-%b-%Y')}',"
        "'indexName':'NIFTY 50'}"
    )
    body = {"cinfo": cinfo}

    response = None
    last_exc = None
    for attempt in range(REQUEST_RETRIES):
        try:
            response = session.post(URL, json=body, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == REQUEST_RETRIES - 1:
                raise
            time.sleep(2.0 * (attempt + 1))
    if response is None:
        raise SystemExit(f"Nifty Indices request failed: {last_exc}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise SystemExit(
            "Nifty Indices historical endpoint returned non-JSON: "
            f"status={response.status_code}, "
            f"content_type={response.headers.get('content-type')}"
        ) from exc

    rows = parse_rows(payload)
    if not rows:
        raise SystemExit(
            f"Nifty Indices historical endpoint returned no rows for "
            f"{args.start}..{args.end}"
        )

    raw_path = raw_dir / f"nifty50_{start:%Y%m%d}_{end:%Y%m%d}.json"
    raw_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    normalized = []
    for row in rows:
        date_value = (
            row.get("HistoricalDate")
            or row.get("Date")
            or row.get("date")
        )
        op = row.get("OPEN") or row.get("Open")
        hi = row.get("HIGH") or row.get("High")
        lo = row.get("LOW") or row.get("Low")
        close = row.get("CLOSE") or row.get("Close")
        if date_value is None or close is None:
            continue
        normalized.append(
            {
                "date": pd.to_datetime(date_value, errors="coerce"),
                "open": pd.to_numeric(op, errors="coerce"),
                "high": pd.to_numeric(hi, errors="coerce"),
                "low": pd.to_numeric(lo, errors="coerce"),
                "close": pd.to_numeric(close, errors="coerce"),
            }
        )

    x = pd.DataFrame(normalized)
    if x.empty:
        raise SystemExit("No recognized NIFTY 50 OHLC rows in Nifty Indices response")

    x = x.dropna(subset=["date", "close"]).copy()
    x["date"] = pd.to_datetime(x["date"]).dt.strftime("%Y-%m-%d")
    x = x[(x["date"] >= args.start) & (x["date"] <= args.end)].copy()
    if x["date"].duplicated().any():
        dup = x.loc[x["date"].duplicated(keep=False), "date"].tolist()[:10]
        raise SystemExit(f"Duplicate NIFTY 50 dates in Nifty Indices response: {dup}")
    if x["close"].astype(float).le(0).any():
        raise SystemExit("Non-positive NIFTY 50 closes detected")

    x = x.sort_values("date").reset_index(drop=True)
    csv_path = out / "nifty50_ohlc.csv"
    x.to_csv(csv_path, index=False)

    manifest = {
        "status": "PASS",
        "source": "NSE Indices historical index data",
        "operator": "NSE Indices Limited",
        "source_url": URL,
        "page_url": REFERER,
        "index": "NIFTY 50",
        "requested_start": args.start,
        "requested_end": args.end,
        "coverage_start": str(x["date"].min()),
        "coverage_end": str(x["date"].max()),
        "rows": int(len(x)),
        "raw_sha256": sha256(raw_path),
        "normalized_sha256": sha256(csv_path),
        "response_status": int(response.status_code),
        "response_content_type": response.headers.get("content-type"),
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
