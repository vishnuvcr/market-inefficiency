#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fixture=ROOT/"tests/fixtures/phase3_underlying_sample.csv"
out=ROOT/"tests/fixtures/phase3_2_result.json"
subprocess.run([sys.executable,str(ROOT/"scripts/phase3_realized_volatility.py"),"--input",str(fixture),"--output",str(out)],check=True)
d=json.loads(out.read_text())
assert d["phase"]=="3.2"
assert d["status"]=="BASELINE"
assert d["complete_periods"]==4
for k in ["close_to_close","parkinson","garman_klass","yang_zhang"]:
    assert k in d["variance_estimates_per_period"]
    assert d["volatility_estimates_annualized"][k] >= 0
assert d["diagnostic_only"] is True
assert d["execution_backtest_allowed"] is False
out.unlink(missing_ok=True)
print("Phase 3.2 realized-volatility diagnostics: PASS")
