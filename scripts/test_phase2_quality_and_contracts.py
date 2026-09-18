"""Deterministic CI coverage for Phase 2 quality and PIT contract enrichment."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/nse_fo_eod_sample.csv"
MASTER = ROOT / "tests/fixtures/contract_master_sample.csv"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        normalized = tmp / "normalized.json"
        quality = tmp / "quality.json"
        reconciled = tmp / "reconciled.json"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/ingest_nse_fo_eod.py"),
            "--input", str(FIXTURE), "--output", str(normalized),
            "--available-at", "2026-09-18T16:30:00Z",
            "--source-version", "synthetic-nse-contract-wise-v1",
        ], check=True)
        subprocess.run([
            sys.executable, str(ROOT / "scripts/validate_dataset_quality.py"),
            "--input", str(normalized), "--output", str(quality),
            "--decision-timestamp", "2026-09-18T17:00:00Z",
        ], check=True)
        q = json.loads(quality.read_text())
        assert q["status"] == "PASS", q
        assert q["valid_row_count"] == 2, q
        subprocess.run([
            sys.executable, str(ROOT / "scripts/reconcile_contract_master.py"),
            "--observations", str(normalized), "--contract-master", str(MASTER),
            "--output", str(reconciled),
            "--decision-timestamp", "2026-09-18T17:00:00Z",
        ], check=True)
        r = json.loads(reconciled.read_text())
        assert r["status"] == "PASS", r
        assert r["enriched_row_count"] == 2, r
        assert {x["lot_size"] for x in r["records"]} == {65.0}, r
    print("PASS: Phase 2 quality diagnostics and PIT contract reconciliation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
