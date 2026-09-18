#!/usr/bin/env python3
"""Acquire and construct a PIT RBI Treasury-bill risk-free curve.

Source:
  RBI Innovation Hub DBIE repository, Monthly RBI Bulletin Table 26
  ("Auctions of Government of India Treasury Bills").

PIT rule:
  - preserve auction_date and issue_date from RBI;
  - an auction observation is considered available only from the *next*
    calendar day after issue_date, avoiding any assumption about same-day
    publication time;
  - for each NIFTY decision date, use the latest available observation per
    tenor strictly before that decision date;
  - construct 91/182/364-day annualized simple-yield curve points;
  - for target T in days, linearly interpolate between adjacent tenors;
    <=91d uses 91d; >364d uses 364d with an explicit extrapolation flag;
  - continuous-compounding conversion is applied later from the interpolated
    annual simple yield: ln(1+y).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

SOURCE_REPO = "Reserve-Bank-Innovation-Hub/dbie.rbihub.in"
SOURCE_REF = "main"
SOURCE_PATH = (
    "data/publications/monthly-rbi-bulletin/"
    "government-accounts-and-treasury-bills/"
    "table-26-auctions-of-government-of-india-treasury-bills.xlsx"
)
RAW_URL = (
    "https://raw.githubusercontent.com/Reserve-Bank-Innovation-Hub/"
    "dbie.rbihub.in/main/"
    + SOURCE_PATH
)
TENORS = {"91-day": 91, "182-day": 182, "364-day": 364}
TENOR_SHEETS = ["91-day", "182-day", "364-day"]
DATE_RE = re.compile(r"^\d{2}-[A-Z][a-z]{2}-\d{4}$")


def parse_rbi_date(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NaT
    if isinstance(value, (pd.Timestamp, date, datetime)):
        return pd.Timestamp(value)
    s = str(value).strip()
    if not s:
        return pd.NaT
    parsed = pd.to_datetime(s, errors="coerce")
    if pd.isna(parsed):
        parsed = pd.to_datetime(s, errors="coerce", format="%d-%b-%Y")
    return parsed


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip().replace(",", "")
    if s in {"", "-", "N/A"}:
        return None
    x = pd.to_numeric(s, errors="coerce")
    return None if pd.isna(x) else float(x)


def parse_sheet(path: Path, tenor: str) -> pd.DataFrame:
    excel = pd.ExcelFile(path)
    sheet_name = excel.sheet_names[TENOR_SHEETS.index(tenor)]
    raw = pd.read_excel(excel, sheet_name=sheet_name, header=None)
    records = []
    for _, row in raw.iterrows():
        cell1 = row.iloc[1] if len(row) > 1 else None
        auction_date = parse_rbi_date(cell1)
        if pd.isna(auction_date):
            continue
        issue_value = row.iloc[2] if len(row) > 2 else None
        issue_date = parse_rbi_date(issue_value)
        records.append(
            {
                "tenor_days": TENORS[tenor],
                "tenor_label": tenor,
                "auction_date": auction_date,
                "issue_date": issue_date,
                "notified": parse_num(row.iloc[3]),
                "cutoff_price": parse_num(row.iloc[11]),
                "yield_pct": parse_num(row.iloc[12]),
                "wavg_price": parse_num(row.iloc[13]),
            }
        )
    return pd.DataFrame.from_records(records)


def get_source_blob_sha() -> str:
    # Prefer gh CLI when running in GitHub Actions; otherwise fall back to the
    # raw URL hash only. The workflow supplies GH_TOKEN automatically.
    try:
        out = subprocess.check_output(
            [
                "gh",
                "api",
                f"repos/{SOURCE_REPO}/contents/{SOURCE_PATH}?ref={SOURCE_REF}",
                "--jq",
                ".sha",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return out
    except Exception:
        pass
    return ""


def build_daily_curve(obs: pd.DataFrame, decision_dates: pd.Series) -> pd.DataFrame:
    valid = obs.dropna(subset=["auction_date", "issue_date", "yield_pct"]).copy()
    valid["available_date"] = valid["issue_date"] + pd.Timedelta(days=1)
    valid["yield_decimal"] = valid["yield_pct"] / 100.0
    valid = valid.sort_values(["tenor_days", "available_date", "auction_date"])
    valid = valid.drop_duplicates(["tenor_days", "available_date"], keep="last")

    rows = []
    for d in sorted(pd.to_datetime(decision_dates["date"], errors="coerce").dropna().dt.normalize().unique()):
        dd = pd.Timestamp(d)
        by_tenor = {}
        for tenor in (91, 182, 364):
            x = valid[
                (valid["tenor_days"] == tenor)
                & (valid["available_date"] < dd)
            ]
            if x.empty:
                continue
            r = x.iloc[-1]
            by_tenor[tenor] = r
        if len(by_tenor) != 3:
            continue

        out = {"date": dd.strftime("%Y-%m-%d")}
        source_parts = []
        for tenor in (91, 182, 364):
            r = by_tenor[tenor]
            out[f"yield_pct_{tenor}"] = float(r["yield_pct"])
            out[f"auction_date_{tenor}"] = r["auction_date"].strftime("%Y-%m-%d")
            out[f"issue_date_{tenor}"] = r["issue_date"].strftime("%Y-%m-%d")
            out[f"available_date_{tenor}"] = r["available_date"].strftime("%Y-%m-%d")
            source_parts.append(f"{tenor}:{r['auction_date']:%Y-%m-%d}")
        out["availability_rule"] = "issue_date_plus_1_calendar_day"
        out["source_observations"] = ";".join(source_parts)
        rows.append(out)

    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--decision-dates", required=True, type=Path)
    ap.add_argument("--output", default="data/phase4a/risk_free")
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    raw_path = out / "rbi_table26_tbill_auctions.xlsx"
    csv_path = out / "rbi_tbill_auction_observations.csv"
    curve_path = out / "rbi_risk_free_daily_curve.csv"

    r = requests.get(RAW_URL, timeout=120)
    r.raise_for_status()
    raw_path.write_bytes(r.content)

    parts = [parse_sheet(raw_path, tenor) for tenor in TENOR_SHEETS]
    obs = pd.concat(parts, ignore_index=True)
    obs = obs.sort_values(["auction_date", "tenor_days"]).reset_index(drop=True)
    obs.to_csv(csv_path, index=False, date_format="%Y-%m-%d")

    decision_dates = pd.read_csv(args.decision_dates, usecols=["date"])
    decision_dates["date"] = pd.to_datetime(decision_dates["date"], errors="coerce")
    curve = build_daily_curve(obs, decision_dates)
    curve.to_csv(curve_path, index=False)

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    obs_valid = obs.dropna(subset=["auction_date", "issue_date", "yield_pct"])
    coverage_start = curve["date"].min() if not curve.empty else None
    coverage_end = curve["date"].max() if not curve.empty else None

    if coverage_start is None or pd.Timestamp(coverage_start) > start:
        raise SystemExit(f"risk-free curve starts too late: {coverage_start}")
    if coverage_end is None or pd.Timestamp(coverage_end) < end:
        raise SystemExit(f"risk-free curve ends too early: {coverage_end}")
    if len(obs_valid) < 300:
        raise SystemExit(f"too few valid RBI T-bill observations: {len(obs_valid)}")

    manifest = {
        "status": "PASS",
        "source": {
            "repository": SOURCE_REPO,
            "ref": SOURCE_REF,
            "path": SOURCE_PATH,
            "raw_url": RAW_URL,
            "source_blob_sha": get_source_blob_sha(),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "raw_sha256": sha256(raw_path),
        },
        "requested_period": [args.start, args.end],
        "availability_rule": {
            "observation_available_on": "issue_date + 1 calendar day",
            "decision_rule": "latest available observation strictly before decision date",
            "same_day_unpublished_data": "never used",
        },
        "curve_rule": {
            "tenors_days": [91, 182, 364],
            "interpolation": "linear in annual simple yield between adjacent tenors",
            "short_end": "<=91 days -> 91-day yield",
            "long_end": ">364 days -> 364-day yield with extrapolation flag",
            "day_count": "ACT/365 for TTM",
            "continuous_conversion": "ln(1 + annual_simple_yield)",
        },
        "observation_rows": int(len(obs)),
        "valid_observation_rows": int(len(obs_valid)),
        "curve_rows": int(len(curve)),
        "curve_start": str(coverage_start),
        "curve_end": str(coverage_end),
        "files": {
            "raw_xlsx": {"path": str(raw_path), "sha256": sha256(raw_path)},
            "observations_csv": {"path": str(csv_path), "sha256": sha256(csv_path)},
            "curve_csv": {"path": str(curve_path), "sha256": sha256(curve_path)},
        },
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
