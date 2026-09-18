#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
fixture=ROOT/"tests/fixtures/phase3_jump_sample.csv"
out=ROOT/"tests/fixtures/phase3_4_result.json"

subprocess.run(
    [
        sys.executable,
        str(ROOT/"scripts/phase3_jump_diagnostics.py"),
        "--input",
        str(fixture),
        "--output",
        str(out),
    ],
    check=True,
)

d=json.loads(out.read_text())
assert d["phase"]=="3.4"
assert d["status"]=="BASELINE"
assert d["rows"]==6
assert d["return_observations"]==5
assert "flagged_observations" in d["standardized_jump_proxy"]
assert 0.0 <= d["standardized_jump_proxy"]["flag_rate"] <= 1.0
assert d["bipower_variation_proxy"]["realized_variation"]>=0
assert d["bipower_variation_proxy"]["bipower_variation"]>=0
assert d["range_jump_proxy"]["parkinson_variance"]>=0
assert d["range_jump_proxy"]["realized_variation"]>=0
assert d["diagnostic_only"] is True
assert d["execution_backtest_allowed"] is False
out.unlink(missing_ok=True)
print("Phase 3.4 jump diagnostics: PASS")
