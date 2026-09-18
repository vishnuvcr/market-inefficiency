#!/usr/bin/env python3
"""Probe NSE's public historical F&O contract-wise EOD interface.

This is a data-access probe only. It does not infer availability, completeness,
or tradability from an empty response.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPORT_URL = "https://www.nseindia.com/report-detail/fo_eq_security"
API_URL = "https://www.nseindia.com/api/historicalOR/foCPV"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": REPORT_URL,
    "Connection": "keep-alive",
}


def probe(args: argparse.Namespace) -> dict:
    session = requests.Session()
    session.headers.update(HEADERS)

    result = {
        "probe_utc": datetime.now(timezone.utc).isoformat(),
        "report_url": REPORT_URL,
        "api_url": API_URL,
        "request": {
            "from": args.date,
            "to": args.date,
            "instrumentType": "OPTIDX",
            "symbol": "NIFTY",
            "year": args.year,
            "expiryDate": args.expiry,
            "optionType": args.option_type,
            "strikePrice": str(args.strike),
        },
        "diagnostic_only": True,
        "execution_backtest_allowed": False,
    }

    try:
        landing = session.get(REPORT_URL, timeout=30)
        result["landing"] = {
            "http_status": landing.status_code,
            "content_type": landing.headers.get("content-type"),
            "bytes": len(landing.content),
        }
    except requests.RequestException as exc:
        result["landing_error"] = f"{type(exc).__name__}: {exc}"

    time.sleep(1.0)

    params = {
        "from": args.date,
        "to": args.date,
        "instrumentType": "OPTIDX",
        "symbol": "NIFTY",
        "year": str(args.year),
        "expiryDate": args.expiry,
        "optionType": args.option_type,
        "strikePrice": str(args.strike),
    }

    try:
        response = session.get(API_URL, params=params, timeout=45)
        result["response"] = {
            "http_status": response.status_code,
            "content_type": response.headers.get("content-type"),
            "url": response.url,
            "bytes": len(response.content),
        }
        text = response.text[:20000]
        try:
            payload = response.json()
            result["payload_type"] = type(payload).__name__
            if isinstance(payload, dict):
                result["payload_keys"] = sorted(payload.keys())
                data = payload.get("data")
                result["row_count"] = len(data) if isinstance(data, list) else None
                result["sample_rows"] = data[:3] if isinstance(data, list) else None
            elif isinstance(payload, list):
                result["row_count"] = len(payload)
                result["sample_rows"] = payload[:3]
        except ValueError:
            result["non_json_preview"] = text
    except requests.RequestException as exc:
        result["request_error"] = f"{type(exc).__name__}: {exc}"

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="14-05-2026")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--expiry", default="28-MAY-2026")
    parser.add_argument("--option-type", default="CE", choices=["CE", "PE"])
    parser.add_argument("--strike", type=float, default=24000)
    parser.add_argument("--output", default="data/nse_probe/nse_option_eod_probe.json")
    args = parser.parse_args()

    result = probe(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
