#!/usr/bin/env python3
"""Download and inventory the public NSE F&O historical order/trade sample archive.

This is a sample-data validator, not the licensed economic archive required for
strategy research. It records URL, byte count and SHA-256 so the acquisition is
reproducible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import requests

DEFAULT_URL = "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Sample_FOsegment.zip"


def download(url: str, output: Path) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 market-inefficiency research sample validator"}
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(response.content)

    sha256 = hashlib.sha256(response.content).hexdigest()
    info = {
        "url": url,
        "output": str(output),
        "bytes": len(response.content),
        "sha256": sha256,
        "content_type": response.headers.get("content-type"),
    }

    try:
        with ZipFile(output) as zf:
            info["archive_entries"] = zf.namelist()
    except Exception as exc:
        info["archive_error"] = str(exc)
    return info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--output", type=Path, default=Path("artifacts/nse_sample/Sample_FOsegment.zip"))
    ap.add_argument("--manifest", type=Path, default=Path("artifacts/nse_sample/manifest.json"))
    args = ap.parse_args()

    result = download(args.url, args.output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

    if "archive_entries" not in result:
        raise SystemExit("downloaded file is not a readable ZIP archive")


if __name__ == "__main__":
    main()
