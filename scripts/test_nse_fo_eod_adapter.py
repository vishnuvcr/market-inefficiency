"""Deterministic test for the NSE F&O EOD normalization adapter."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "tests/fixtures/nse_fo_eod_sample.csv"
ADAPTER = ROOT / "scripts/ingest_nse_fo_eod.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "normalized.json"
        command = [
            sys.executable,
            str(ADAPTER),
            "--input", str(INPUT),
            "--output", str(output),
            "--available-at", "2026-09-18T16:30:00Z",
            "--source-version", "synthetic-nse-contract-wise-v1",
        ]
        subprocess.run(command, check=True, cwd=ROOT)
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["source_id"] == "DS-NSE-FO-EOD"
        assert payload["row_count"] == 2
        assert len(payload["raw_sha256"]) == 64
        assert all(r["available_at"] == "2026-09-18T16:30:00Z" for r in payload["records"])
        assert {r["option_type"] for r in payload["records"]} == {"CE", "PE"}
        assert len({(r["timestamp"], r["instrument_id"]) for r in payload["records"]}) == 2
        assert payload["records"][0]["high"] >= payload["records"][0]["low"]
    print("NSE F&O EOD adapter test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
