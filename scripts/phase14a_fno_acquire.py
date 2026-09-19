#!/usr/bin/env python3
"""Phase 14A.1 data acquisition — official NSE NIFTY futures + index history.

The endpoint is the NSE historical contract-wise F&O API used by the official
contract-wise price/volume page. Requests are split into <=30-day chunks to
match the public API client convention and are rate-limited deliberately.
No synthetic contracts, inferred expiries, or adjusted prices are created.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.nseindia.com/api"
FNO_ENDPOINT = f"{BASE}/historicalOR/foCPV"
INDEX_ENDPOINT = f"{BASE}/historicalOR/indicesHistory"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.8",
    "Referer": "https://www.nseindia.com/get-quotes/equity?symbol=HDFCBANK",
}


def chunks(start: date, end: date, days: int = 30):
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=days - 1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def get_json(session: requests.Session, url: str, params: dict, retries: int = 4) -> dict:
    last = None
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=45)
            if response.status_code in (429, 502, 503, 504):
                last = RuntimeError(f"retryable HTTP {response.status_code}")
                time.sleep(1.0 + attempt * 1.0)
                continue
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or "data" not in payload:
                raise ValueError("NSE response has no data field")
            return payload
        except (requests.RequestException, ValueError) as exc:
            last = exc
            time.sleep(1.0 + attempt * 1.0)
    raise RuntimeError(f"NSE request failed after {retries} attempts: {last}")


def bootstrap(session: requests.Session) -> None:
    # The public NSE client first visits option-chain to obtain session cookies.
    r = session.get("https://www.nseindia.com/option-chain", timeout=45)
    r.raise_for_status()


def fetch_futures(session: requests.Session, start: date, end: date, sleep_seconds: float) -> list[dict]:
    rows: list[dict] = []
    for a, b in chunks(start, end):
        params = {
            "instrumentType": "FUTIDX",
            "symbol": "NIFTY",
            "from": a.strftime("%d-%m-%Y"),
            "to": b.strftime("%d-%m-%Y"),
        }
        payload = get_json(session, FNO_ENDPOINT, params)
        block = payload["data"]
        if isinstance(block, list):
            rows.extend(block)
        elif isinstance(block, dict):
            rows.extend(block.get("data", []))
        time.sleep(sleep_seconds)
    return rows


def fetch_index(session: requests.Session, start: date, end: date, sleep_seconds: float) -> list[dict]:
    rows: list[dict] = []
    for a, b in chunks(start, end):
        params = {
            "indexType": "NIFTY 50",
            "from": a.strftime("%d-%m-%Y"),
            "to": b.strftime("%d-%m-%Y"),
        }
        payload = get_json(session, INDEX_ENDPOINT, params)
        block = payload["data"]
        if isinstance(block, list):
            rows.extend(block)
        elif isinstance(block, dict):
            rows.extend(block.get("data", []))
        time.sleep(sleep_seconds)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-04-13")
    ap.add_argument("--end", default="2026-05-14")
    ap.add_argument("--futures-output", required=True)
    ap.add_argument("--index-output", required=True)
    ap.add_argument("--sleep", type=float, default=0.75)
    args = ap.parse_args()

    start = pd.Timestamp(args.start).date()
    end = pd.Timestamp(args.end).date()
    session = requests.Session()
    session.headers.update(HEADERS)
    bootstrap(session)

    futures = fetch_futures(session, start, end, args.sleep)
    index = fetch_index(session, start, end, args.sleep)

    if not futures:
        raise SystemExit("NSE returned no NIFTY futures rows")
    if not index:
        raise SystemExit("NSE returned no NIFTY 50 index rows")

    f = pd.DataFrame(futures)
    i = pd.DataFrame(index)

    required_f = {"FH_INSTRUMENT", "FH_SYMBOL", "FH_EXPIRY_DT", "FH_CLOSING_PRICE", "FH_SETTLE_PRICE", "FH_TOT_TRADED_QTY", "FH_OPEN_INT", "FH_MARKET_LOT", "FH_TIMESTAMP", "FH_UNDERLYING_VALUE"}
    missing_f = sorted(required_f - set(f.columns))
    if missing_f:
        raise SystemExit(f"futures schema missing: {missing_f}")
    required_i = {"EOD_INDEX_NAME", "EOD_CLOSE_INDEX_VAL", "EOD_TIMESTAMP"}
    missing_i = sorted(required_i - set(i.columns))
    if missing_i:
        raise SystemExit(f"index schema missing: {missing_i}")

    f = f[f["FH_INSTRUMENT"].eq("FUTIDX") & f["FH_SYMBOL"].eq("NIFTY")].copy()
    i = i[i["EOD_INDEX_NAME"].astype(str).str.upper().eq("NIFTY 50")].copy()

    f.to_csv(args.futures_output, index=False)
    i.to_csv(args.index_output, index=False)

    manifest_path = Path(args.futures_output).with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps({
        "source_fno_endpoint": FNO_ENDPOINT,
        "source_index_endpoint": INDEX_ENDPOINT,
        "start": args.start,
        "end": args.end,
        "futures_rows": int(len(f)),
        "futures_expiries": int(pd.to_datetime(f["FH_EXPIRY_DT"], errors="coerce").nunique()),
        "futures_trade_dates": int(pd.to_datetime(f["FH_TIMESTAMP"], errors="coerce").nunique()),
        "market_lots": sorted(pd.to_numeric(f["FH_MARKET_LOT"], errors="coerce").dropna().unique().tolist()),
        "index_rows": int(len(i)),
        "index_dates": int(pd.to_datetime(i["EOD_TIMESTAMP"], errors="coerce").nunique()),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote futures={len(f):,} index={len(i):,}")


if __name__ == "__main__":
    main()