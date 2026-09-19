#!/usr/bin/env python3
"""Phase 14A.0 — acquire a survivorship-safe historical NIFTY-50 price union from NSE daily cash bhavcopies.

The input membership history is a secondary point-in-time reconstruction. Prices are kept for every
security that was ever a NIFTY-50 member during the requested period, while `active_nifty50` marks
membership only on the observation date. This prevents a constituent leaving the index from causing
an artificial look-ahead when a position is exited after the membership change.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

URL = "https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{ddmmyyyy}.csv"  # official NSE daily cash bhavcopy
KEEP_SERIES = {"EQ", "SM", "BE", "BZ", "ST"}


def load_membership(path: str) -> pd.DataFrame:
    m = pd.read_csv(path, parse_dates=["valid_from", "valid_to"])
    m = m[m["index_name"].eq("Nifty 50")].copy()
    required = {"symbol", "valid_from", "valid_to"}
    missing = sorted(required - set(m.columns))
    if missing:
        raise ValueError(f"membership missing columns: {missing}")
    return m


def load_renames(path: str) -> list[dict]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(obj.get("renames", []))


def actual_symbol(canonical: str, trade_date: pd.Timestamp, renames: list[dict]) -> str:
    current = canonical
    rules = sorted(
        [r for r in renames if r.get("old") and r.get("new") and r.get("old") != r.get("new")],
        key=lambda r: r.get("effective_date") or "1900-01-01",
        reverse=True,
    )
    changed = True
    while changed:
        changed = False
        for rule in rules:
            effective = rule.get("effective_date")
            if not effective or str(effective).endswith("XX"):
                continue
            effective_ts = pd.Timestamp(effective)
            if trade_date < effective_ts and current == rule["new"]:
                current = rule["old"]
                changed = True
    return current


def members_on(membership: pd.DataFrame, trade_date: pd.Timestamp, renames: list[dict]) -> dict[str, str]:
    active = membership[
        (membership["valid_from"] <= trade_date)
        & (membership["valid_to"].isna() | (trade_date < membership["valid_to"]))
    ]
    out: dict[str, str] = {}
    for canonical in sorted(active["symbol"].dropna().astype(str).unique()):
        out[actual_symbol(canonical, trade_date, renames)] = canonical
    return out


def parse_bhavcopy(content: bytes, trade_date: pd.Timestamp, universe_raw_to_canonical: dict[str, str], active_raw_symbols: set[str]) -> pd.DataFrame:
    raw = pd.read_csv(BytesIO(content))
    raw.columns = [str(c).strip() for c in raw.columns]
    required = {
        "SYMBOL", "SERIES", "DATE1", "OPEN_PRICE", "HIGH_PRICE", "LOW_PRICE",
        "CLOSE_PRICE", "PREV_CLOSE", "TTL_TRD_QNTY", "TURNOVER_LACS"
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"bhavcopy missing columns: {missing}")
    raw["SYMBOL"] = raw["SYMBOL"].astype(str).str.strip()
    raw["SERIES"] = raw["SERIES"].astype(str).str.strip()
    raw = raw[raw["SERIES"].isin(KEEP_SERIES)]
    raw = raw[raw["SYMBOL"].isin(universe_raw_to_canonical)].copy()
    if raw.empty:
        return pd.DataFrame()
    raw["date"] = trade_date.date().isoformat()
    raw["symbol_raw"] = raw["SYMBOL"]
    raw["symbol"] = raw["SYMBOL"].map(universe_raw_to_canonical)
    raw["active_nifty50"] = raw["SYMBOL"].isin(active_raw_symbols)
    for source, target in (
        ("OPEN_PRICE", "open"), ("HIGH_PRICE", "high"), ("LOW_PRICE", "low"),
        ("CLOSE_PRICE", "close"), ("PREV_CLOSE", "prev_close"),
        ("TTL_TRD_QNTY", "volume_shares"), ("TURNOVER_LACS", "turnover_inr"),
    ):
        raw[target] = pd.to_numeric(raw[source], errors="coerce")
    raw["turnover_inr"] = raw["turnover_inr"] * 1e5
    return raw[[
        "date", "symbol", "symbol_raw", "active_nifty50", "SERIES", "open", "high",
        "low", "close", "prev_close", "volume_shares", "turnover_inr"
    ]].rename(columns={"SERIES": "series"})


def date_range(start: date, end: date):
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            yield cur
        cur += timedelta(days=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--membership", required=True)
    ap.add_argument("--renames", required=True)
    ap.add_argument("--start", default="2020-04-13")
    ap.add_argument("--end", default="2026-05-14")
    ap.add_argument("--output", required=True)
    ap.add_argument("--sleep", type=float, default=0.25)
    args = ap.parse_args()

    start = pd.Timestamp(args.start).date()
    end = pd.Timestamp(args.end).date()
    membership = load_membership(args.membership)
    renames = load_renames(args.renames)
    canonical_universe = sorted(set(membership["symbol"].dropna().astype(str)))

    raw_to_canonical: dict[str, str] = {}
    for d in pd.date_range(start, end, freq="D"):
        for canonical in canonical_universe:
            raw_symbol = actual_symbol(canonical, d, renames)
            if raw_symbol and not raw_symbol.startswith("_DUMMY"):
                raw_to_canonical[raw_symbol] = canonical

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/"})
    rows: list[pd.DataFrame] = []
    failures: list[dict] = []
    hits = 0

    for d in date_range(start, end):
        trade_date = pd.Timestamp(d)
        active_map = members_on(membership, trade_date, renames)
        active_raw_symbols = set(active_map)
        if not active_raw_symbols:
            continue
        url = URL.format(ddmmyyyy=d.strftime("%d%m%Y"))
        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as exc:
            failures.append({"date": d.isoformat(), "status": "request_error", "error": str(exc)[:120]})
            continue
        if resp.status_code == 404:
            continue
        if resp.status_code != 200 or len(resp.content) < 5000:
            failures.append({"date": d.isoformat(), "status": int(resp.status_code), "size": len(resp.content)})
            continue
        try:
            parsed = parse_bhavcopy(resp.content, trade_date, raw_to_canonical, active_raw_symbols)
        except Exception as exc:
            failures.append({"date": d.isoformat(), "status": "parse_error", "error": str(exc)[:120]})
            continue
        if not parsed.empty:
            rows.append(parsed)
            hits += 1
        if args.sleep > 0:
            time.sleep(args.sleep)
        if hits and hits % 50 == 0:
            print(f"processed {hits} files through {d}", flush=True)

    if not rows:
        raise SystemExit("no NIFTY-50 rows acquired")
    df = pd.concat(rows, ignore_index=True).sort_values(["date", "symbol_raw"]).reset_index(drop=True)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    manifest = out.with_suffix(".manifest.json")
    manifest.write_text(
        json.dumps({
            "source_url_template": URL,
            "start": args.start,
            "end": args.end,
            "trading_files_with_rows": int(hits),
            "rows": int(len(df)),
            "unique_raw_symbols": int(df["symbol_raw"].nunique()),
            "unique_canonical_symbols": int(df["symbol"].nunique()),
            "active_rows": int(df["active_nifty50"].sum()),
            "min_date": str(df["date"].min()),
            "max_date": str(df["date"].max()),
            "n_failures": len(failures),
            "failures": failures[:200],
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out} with {len(df):,} rows; failures={len(failures)}")


if __name__ == "__main__":
    main()