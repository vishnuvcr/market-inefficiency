#!/usr/bin/env python3
"""Acquire and validate a bounded NSE NIFTY OPTIDX daily bhavcopy snapshot.

The downloader preserves the original NSE ZIP, extracts only NIFTY option rows
for the normalized research artifact, and records a SHA-256 manifest. Weekends
and NSE 404 dates are recorded as non-session dates rather than treated as
failures. No market-data inference is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
import zipfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://archives.nseindia.com"
FALLBACK_BASE = "https://nsearchives.nseindia.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36",
    "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.8",
    "Referer": "https://www.nseindia.com/all-reports-derivatives",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}
LEGACY_REQUIRED = ["TIMESTAMP", "INSTRUMENT", "SYMBOL", "EXPIRY_DT", "STRIKE_PR",
                   "OPTION_TYP", "OPEN", "HIGH", "LOW", "CLOSE", "LTP",
                   "SETTLE_PR", "CONTRACTS", "VAL_INLAKH", "OPEN_INT", "CHG_IN_OI"]
UDIFF_REQUIRED = ["TradDt", "FinInstrmTp", "TckrSymb", "XpryDt", "StrkPric",
                  "OptnTp", "OpnPric", "HghPric", "LwPric", "ClsPric", "LastPric",
                  "SttlmPric", "TtlTradgVol", "TtlTrfVal", "OpnIntrst",
                  "ChngInOpnIntrst", "UndrlygPric", "NewBrdLotQty"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def url_for(d: date) -> tuple[str, str]:
    if d >= date(2024, 7, 8):
        return ("udiff", f"{BASE}/content/fo/BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv.zip")
    month = d.strftime("%b").upper()
    filename = f"fo{d:%d}{month}{d:%Y}bhav.csv.zip"
    return ("legacy", f"{BASE}/content/historical/DERIVATIVES/{d:%Y}/{month}/{filename}")


REQUEST_LOCK = threading.Lock()
LAST_REQUEST_AT = 0.0


def rate_limited_get(session: requests.Session, url: str, timeout: int, delay_seconds: float):
    global LAST_REQUEST_AT
    with REQUEST_LOCK:
        wait = delay_seconds - (time.monotonic() - LAST_REQUEST_AT)
        if wait > 0:
            time.sleep(wait)
        response = session.get(url, timeout=timeout)
        LAST_REQUEST_AT = time.monotonic()
        return response


def fetch_one(d: date, raw_dir: Path, norm_dir: Path, retries: int, delay_seconds: float) -> dict:
    route, url = url_for(d)
    s = requests.Session()
    s.headers.update(HEADERS)
    candidate_urls = [url]
    if route == "legacy":
        candidate_urls.append(url.replace(BASE, FALLBACK_BASE, 1))
    rec = {"date": d.isoformat(), "route": route, "url": url, "candidate_urls": candidate_urls}

    for attempt in range(retries + 1):
        try:
            last_status = None
            last_error = None
            r = None
            for candidate in candidate_urls:
                try:
                    rr = rate_limited_get(s, candidate, timeout=60, delay_seconds=delay_seconds)
                    last_status = rr.status_code
                    if rr.status_code == 200:
                        r = rr
                        rec["url"] = candidate
                        break
                    last_error = f"HTTP {rr.status_code}"
                except requests.RequestException as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
            rec["http_status"] = last_status
            if r is None:
                if last_status == 404:
                    rec["status"] = "NO_ARCHIVE"
                    return rec
                raise requests.HTTPError(last_error or "all archive hosts failed")
            r.raise_for_status()
            raw = r.content
            rec["bytes"] = len(raw)
            rec["sha256"] = sha256_bytes(raw)

            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
                if not csvs:
                    raise ValueError("archive contains no CSV")
                member = csvs[0]
                csv_bytes = z.read(member)

            raw_path = raw_dir / f"{d:%Y%m%d}.zip"
            raw_path.write_bytes(raw)

            if route == "udiff":
                df = pd.read_csv(io.BytesIO(csv_bytes), low_memory=False)
                missing = [c for c in UDIFF_REQUIRED if c not in df.columns]
                if missing:
                    raise ValueError(f"missing UDiFF columns: {missing}")
                df = df[df["TckrSymb"].astype(str).str.upper().eq("NIFTY")]
                df = df[df["OptnTp"].astype(str).isin(["CE", "PE"])]
                df = df.copy()
                out = pd.DataFrame({
                    "trade_date": pd.to_datetime(df["TradDt"], errors="coerce").dt.date.astype("string"),
                    "instrument_id": df["FinInstrmId"],
                    "underlying_id": df["TckrSymb"],
                    "expiry": pd.to_datetime(df["XpryDt"], errors="coerce").dt.date.astype("string"),
                    "strike": pd.to_numeric(df["StrkPric"], errors="coerce"),
                    "option_type": df["OptnTp"],
                    "open": pd.to_numeric(df["OpnPric"], errors="coerce"),
                    "high": pd.to_numeric(df["HghPric"], errors="coerce"),
                    "low": pd.to_numeric(df["LwPric"], errors="coerce"),
                    "close": pd.to_numeric(df["ClsPric"], errors="coerce"),
                    "last_price": pd.to_numeric(df["LastPric"], errors="coerce"),
                    "settlement": pd.to_numeric(df["SttlmPric"], errors="coerce"),
                    "volume": pd.to_numeric(df["TtlTradgVol"], errors="coerce"),
                    "turnover": pd.to_numeric(df["TtlTrfVal"], errors="coerce"),
                    "open_interest": pd.to_numeric(df["OpnIntrst"], errors="coerce"),
                    "change_in_oi": pd.to_numeric(df["ChngInOpnIntrst"], errors="coerce"),
                    "underlying_price": pd.to_numeric(df["UndrlygPric"], errors="coerce"),
                    "lot_size": pd.to_numeric(df["NewBrdLotQty"], errors="coerce"),
                })
            else:
                df = pd.read_csv(io.BytesIO(csv_bytes))
                missing = [c for c in LEGACY_REQUIRED if c not in df.columns]
                if missing:
                    raise ValueError(f"missing legacy columns: {missing}")
                df = df[df["SYMBOL"].astype(str).str.upper().eq("NIFTY")]
                df = df[df["OPTION_TYP"].astype(str).isin(["CE", "PE"])]
                df = df.copy()
                out = pd.DataFrame({
                    "trade_date": pd.to_datetime(df["TIMESTAMP"], errors="coerce", format="mixed").dt.date.astype("string"),
                    "instrument_id": pd.NA,
                    "underlying_id": df["SYMBOL"],
                    "expiry": pd.to_datetime(df["EXPIRY_DT"], errors="coerce", format="mixed").dt.date.astype("string"),
                    "strike": pd.to_numeric(df["STRIKE_PR"], errors="coerce"),
                    "option_type": df["OPTION_TYP"],
                    "open": pd.to_numeric(df["OPEN"], errors="coerce"),
                    "high": pd.to_numeric(df["HIGH"], errors="coerce"),
                    "low": pd.to_numeric(df["LOW"], errors="coerce"),
                    "close": pd.to_numeric(df["CLOSE"], errors="coerce"),
                    "last_price": pd.to_numeric(df["LTP"], errors="coerce"),
                    "settlement": pd.to_numeric(df["SETTLE_PR"], errors="coerce"),
                    "volume": pd.to_numeric(df["CONTRACTS"], errors="coerce"),
                    "turnover": pd.to_numeric(df["VAL_INLAKH"], errors="coerce") * 100000,
                    "open_interest": pd.to_numeric(df["OPEN_INT"], errors="coerce"),
                    "change_in_oi": pd.to_numeric(df["CHG_IN_OI"], errors="coerce"),
                    "underlying_price": pd.NA,
                    "lot_size": pd.NA,
                })

            out["available_at"] = f"{d.isoformat()}T23:59:59+05:30"
            out["timestamp"] = pd.Timestamp(d, tz="Asia/Kolkata").tz_convert("UTC").isoformat()
            norm_path = norm_dir / f"{d:%Y%m%d}.csv"
            out.to_csv(norm_path, index=False)
            rec.update({
                "status": "VALIDATED",
                "csv_member": member,
                "nifty_option_rows": int(len(out)),
                "raw_path": str(raw_path),
                "normalized_path": str(norm_path),
            })
            return rec
        except Exception as exc:
            rec["error"] = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                status = rec.get("http_status")
                if status in (403, 429):
                    time.sleep(5 * (attempt + 1))
                elif isinstance(status, int) and status >= 500:
                    time.sleep(3 * (attempt + 1))
                else:
                    time.sleep(2 ** attempt)
            else:
                rec["status"] = "ERROR"
                return rec
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-05-01")
    ap.add_argument("--end", default="2026-05-14")
    ap.add_argument("--output", default="data/nse_option_snapshot")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--delay-seconds", type=float, default=1.25,
                    help="Minimum delay between NSE archive HTTP requests in this process.")
    args = ap.parse_args()

    root = Path(args.output)
    raw_dir, norm_dir = root / "raw", root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    norm_dir.mkdir(parents=True, exist_ok=True)

    dates = list(daterange(date.fromisoformat(args.start), date.fromisoformat(args.end)))
    records = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(fetch_one, d, raw_dir, norm_dir, args.retries, args.delay_seconds): d for d in dates}
        for fut in as_completed(futs):
            records.append(fut.result())
    records.sort(key=lambda x: x["date"])

    manifest = {
        "dataset_id": "NSE-NIFTY-OPTIDX-EOD-" + hashlib.sha256(
            json.dumps(records, sort_keys=True).encode()
        ).hexdigest()[:16],
        "snapshot_created_at": datetime.now(timezone.utc).isoformat(),
        "source": "NSE F&O daily bhavcopy archives",
        "source_version": "legacy+UDiFF route by official format boundary",
        "preprocessing_version": "phase4a-nifty-optidx-v2-rate-limited",
        "start": args.start,
        "end": args.end,
        "records": records,
        "validated_days": sum(r.get("status") == "VALIDATED" for r in records),
        "no_archive_days": sum(r.get("status") == "NO_ARCHIVE" for r in records),
        "error_days": sum(r.get("status") == "ERROR" for r in records),
        "raw_preserved": True,
        "diagnostic_only": False,
        "execution_backtest_allowed": False,
    }
    (root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
