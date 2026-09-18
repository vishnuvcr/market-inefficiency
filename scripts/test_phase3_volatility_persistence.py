#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fixture = ROOT / "tests/fixtures/phase3_underlying_sample.csv"
out = ROOT / "tests/fixtures/phase3_3_result.json"

subprocess.run(
    [
        sys.executable,
        str(ROOT / "scripts/phase3_volatility_persistence.py"),
        "--input",
        str(fixture),
        "--output",
        str(out),
        "--max-lag",
        "2",
        "--rolling-window",
        "3",
    ],
    check=True,
)

d = json.loads(out.read_text())
assert d["phase"] == "3.3"
assert d["status"] == "BASELINE"
assert d["return_observations"] == 4
assert "1" in d["absolute_return_acf"]
assert "1" in d["return_pacf"]
assert d["rolling_volatility"]["window_periods"] == 3
assert d["rolling_volatility"]["observations"] == 2
assert d["diagnostic_only"] is True
assert d["execution_backtest_allowed"] is False
out.unlink(missing_ok=True)
print("Phase 3.3 volatility-persistence diagnostics: PASS")
