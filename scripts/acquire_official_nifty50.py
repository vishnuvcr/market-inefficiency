#!/usr/bin/env python3
"""Acquire official NIFTY 50 historical OHLC from NSE Indices for Phase 4A PIT work.

The source is NSE Indices' Historical Index Data interface.  This script
preserves raw responses, normalizes the official OHLC fields, assigns only the
pre-registered conservative EOD availability convention, and fails closed on
integrity problems.  It does not substitute another vendor/source.
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

REPORT_URL = "https://www.niftyindices.com/reports/historical-data"
API_URL = "https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString"
INDEX_NAME = "NIFTY 50"
IST = "Asia/Kolkata"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": "https://www.niftyindices.com",
    "Referer": REPORT_URL,
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_date(value: str) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)
    return ts.normalize()


def fmt_nse_date(ts: pd.Timestamp) -> str:
    return ts.strftime("%d-%b-%Y")


def request_chunk(session: requests.Session, start: pd.Timestamp, end: pd.Timestamp) -> list[dict]:
    # The historical-data endpoint expects cinfo as a string containing the
    # ASP.NET-style object. Keep the exact field names used by the public page.
    payload = {
        "cinfo": (
            "{'name':'"
            + INDEX_NAME
            + "','indexName':'"
            + INDEX_NAME
            + "','startDate':'"
            + fmt_nse_date(start)
            + "','endDate':'"
            + fmt_nse_date(end)
            + "'}"
        )
    }

    last_error = None
    for attempt in range(1, 5):
        try:
            # Bootstrap the public report page first so the session has the
            # current cookies/anti-bot state expected by the endpoint.
            session.get(REPORT_URL, headers=HEADERS, timeout=(10, 20))

            r = session.post(
                API_URL,
                json=payload,
                headers=HEADERS,
                timeout=(15, 45),
            )
            r.raise_for_status()
            body = r.json()
            data = body.get("d")
            if data is None:
                raise ValueError(f"response missing 'd': {str(body)[:500]}")
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, list):
                raise ValueError(f"unexpected response type: {type(data).__name__}")
            return data
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < 4:
                time.sleep(2 ** (attempt - 1))
            else:
                break
    raise RuntimeError(
        f"NSE Indices request failed for {start.date()}..{end.date()}: {last_error}"
    )


def normalize(rows: list[dict], requested_start: pd.Timestamp, requested_end: pd.Timestamp) -> pd.DataFrame:
    if not rows:
        raise ValueError("NSE Indices returned zero rows")

    df = pd.DataFrame(rows)
    required = ["HistoricalDate", "OPEN", "HIGH", "LOW", "CLOSE"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"official NIFTY response missing columns: {missing}")

    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df["HistoricalDate"], format="%d %b %Y", errors="coerce"),
            "open": pd.to_numeric(df["OPEN"].replace("-", pd.NA), errors="coerce"),
            "high": pd.to_numeric(df["HIGH"].replace("-", pd.NA), errors="coerce"),
            "low": pd.to_numeric(df["LOW"].replace("-", pd.NA), errors="coerce"),
            "close": pd.to_numeric(df["CLOSE"].replace("-", pd.NA), errors="coerce"),
        }
    )
    out = out.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)

    if out.empty:
        raise ValueError("official NIFTY response contained no usable rows")

    if out["date"].duplicated().any():
        dupes = out.loc[out["date"].duplicated(), "date"].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"duplicate official NIFTY dates: {dupes[:10]}")

    if (out["date"] < requested_start).any() or (out["date"] > requested_end).any():
        raise ValueError("official response contains dates outside requested period")

    if (out[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("official NIFTY OHLC contains non-positive values")

    bad_range = (
        (out["high"] < out["low"])
        | (out["open"] < out["low"])
        | (out["open"] > out["high"])
        | (out["close"] < out["low"])
        | (out["close"] > out["high"])
    )
    if bad_range.any():
        raise ValueError("official NIFTY OHLC violates range invariants")

    # Conservative EOD convention frozen by Phase 4A documentation. This is
    # an assumption about information availability, not a claim about exact
    # exchange publication timestamp.
    available = (
        out["date"]
        .dt.tz_localize(IST)
        + pd.Timedelta(hours=23, minutes=59, seconds=59)
    )

    out.insert(0, "instrument_id", INDEX_NAME)
    out["available_at"] = available.astype(str)
    out["source"] = "NSE Indices Historical Index Data"
    out["source_url"] = REPORT_URL
    out["available_at_rule"] = "trade_date 23:59:59 Asia/Kolkata (conservative EOD convention)"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-04-13")
    ap.add_argument("--end", default="2026-05-14")
    ap.add_argument("--output-dir", default="data/phase4a/external/nifty50_official")
    args = ap.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if start > end:
        raise SystemExit("--start must be on or before --end")

    root = Path(args.output_dir)
    raw_dir = root / "raw"
    root.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"Connection": "keep-alive"})

    chunks: list[dict] = []
    frames: list[pd.DataFrame] = []
    cur = start
    while cur <= end:
        chunk_end = min(end, pd.Timestamp(year=cur.year, month=12, day=31))
        rows = request_chunk(session, cur, chunk_end)
        raw_path = raw_dir / f"nifty50_{cur.year}.json"
        raw_path.write_text(json.dumps(rows, indent=2) + "\n")
        frame = normalize(rows, cur, chunk_end)
        frames.append(frame)
        chunks.append(
            {
                "year": cur.year,
                "requested_start": str(cur.date()),
                "requested_end": str(chunk_end.date()),
                "raw_file": str(raw_path),
                "raw_sha256": sha256(raw_path),
                "rows_returned": len(rows),
                "rows_usable": len(frame),
            }
        )
        if chunk_end < end:
            time.sleep(2)
        cur = chunk_end + pd.Timedelta(days=1)

    out = pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
    if out["date"].duplicated().any():
        raise SystemExit("duplicate dates across yearly chunks")

    csv_path = root / "nifty50_index.csv"
    out.to_csv(csv_path, index=False)

    manifest = {
        "status": "PASS",
        "source": "NSE Indices Historical Index Data",
        "source_url": REPORT_URL,
        "instrument": INDEX_NAME,
        "requested_period": [str(start.date()), str(end.date())],
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": len(out),
        "first_date": str(out["date"].min().date()),
        "last_date": str(out["date"].max().date()),
        "duplicate_dates": int(out["date"].duplicated().sum()),
        "nonpositive_close": int((out["close"] <= 0).sum()),
        "chunks": chunks,
        "csv_sha256": sha256(csv_path),
        "pit_note": (
            "available_at uses the pre-registered conservative EOD convention "
            "23:59:59 Asia/Kolkata; exact historical publication timestamp is "
            "not inferred from the observation date."
        ),
    }
    (root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
