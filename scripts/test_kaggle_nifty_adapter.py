"""Deterministic test for the Kaggle NIFTY normalization boundary."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/kaggle_nifty_sample.csv"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / "normalized.json"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/ingest_kaggle_nifty.py"),
            "--input", str(FIXTURE),
            "--output", str(output),
            "--instrument-id", "NIFTY50",
            "--source-version", "debashis74017/nifty-50-minute-data@synthetic-fixture",
            "--downloaded-at", "2026-09-18T10:00:00Z",
            "--available-at", "2026-09-18T10:00:00Z",
        ], check=True)
        payload = json.loads(output.read_text())
        assert payload["source_id"] == "DS-KAGGLE-NIFTY"
        assert payload["row_count"] == 3
        assert payload["execution_backtest_allowed"] is False
        assert len(payload["raw_sha256"]) == 64
        assert payload["records"][0]["timestamp"] == "2026-09-18T09:15:00Z"
    print("PASS: Kaggle NIFTY normalization adapter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
