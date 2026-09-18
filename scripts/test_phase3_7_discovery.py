#!/usr/bin/env python3
"""Smoke test for Phase 3.7 discovery diagnostics."""
from pathlib import Path
import json
import subprocess
import tempfile
import pandas as pd

def main():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        ts=pd.date_range("2024-01-01", periods=40, freq="D", tz="UTC")
        n=pd.DataFrame({"timestamp":ts,"open":100.0,"high":101.0,"low":99.0,"close":[100+i*0.1 for i in range(40)]})
        n.to_csv(td/"nifty.csv",index=False)
        rows=[]
        for t in ts:
            ist=t.tz_convert("Asia/Kolkata")
            for minute in range(6):
                rows.append({"date":(ist.replace(hour=9,minute=15+minute,second=0,tzinfo=None)).strftime("%Y-%m-%d %H:%M:%S"),"open":15,"high":16,"low":14,"close":15.5,"volume":0})
        pd.DataFrame(rows).to_csv(td/"vix.csv",index=False)
        out=td/"out.json"
        subprocess.run(["python","scripts/phase3_7_discovery.py","--nifty",str(td/"nifty.csv"),"--vix",str(td/"vix.csv"),"--output",str(out)],check=True)
        x=json.loads(out.read_text())
        assert x["phase"]=="3.7"
        assert x["diagnostic_only"] is True
        assert x["execution_backtest_allowed"] is False
        assert x["overlap_rows"]==40
        assert "conditional_by_vix_tercile" in x
        print("Phase 3.7 discovery test passed.")

if __name__=="__main__":
    main()
