#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fixture = ROOT / "tests/fixtures/phase3_underlying_sample.csv"
out = ROOT / "tests/fixtures/phase3_result.json"
subprocess.run([sys.executable, str(ROOT / "scripts/phase3_stylized_facts.py"), "--input", str(fixture), "--output", str(out)], check=True)
data = json.loads(out.read_text())
assert data["phase"] == "3.1"
assert data["status"] == "BASELINE"
assert data["rows"] == 5
assert data["return_observations"] == 4
assert data["diagnostic_only"] is True
assert data["execution_backtest_allowed"] is False
out.unlink(missing_ok=True)
print("Phase 3.1 stylized-fact diagnostics: PASS")
