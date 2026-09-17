"""CI test for immutable snapshot manifest fields and hash integrity."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/nse_fo_eod_sample.csv"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "manifest.json"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/create_snapshot_manifest.py"),
            "--input", str(FIXTURE), "--output", str(out),
            "--dataset-id", "synthetic-test-v1", "--source", "NSE synthetic fixture",
            "--source-version", "synthetic-v1", "--preprocessing-version", "adapter-v1",
            "--code-commit", "test-commit",
        ], check=True)
        manifest = json.loads(out.read_text())
        expected = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        assert manifest["dataset_id"] == "synthetic-test-v1"
        assert manifest["sha256"] == expected
        assert manifest["row_count"] is None  # CSV row count is not inferred by this JSON manifest tool.
        assert len(manifest["snapshot_created_at"]) > 10
    print("PASS: immutable snapshot manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
