#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(24680); r=rng.normal(0,0.0007,80); close=25000*np.exp(np.cumsum(r))
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp); fixture=p/'input.csv'; out=p/'result.json'
    ts=pd.date_range('2026-09-18T03:45:00Z',periods=len(close),freq='min')
    pd.DataFrame({'timestamp':ts,'close':close}).to_csv(fixture,index=False)
    subprocess.run([sys.executable,str(ROOT/'scripts/phase3_regime_segmentation.py'),'--input',str(fixture),'--output',str(out),'--window','20'],check=True)
    d=json.loads(out.read_text())
    assert d['phase']=='3.6' and d['status']=='BASELINE'
    assert d['usable_rows']==61 and d['predictive_model'] is False
    assert len(d['regimes'])>=4 and len(d['volatility_tercile_cutoffs'])==2
    assert sum(v['observations'] for v in d['regimes'].values())==d['usable_rows']
    assert d['diagnostic_only'] is True and d['execution_backtest_allowed'] is False
print('Phase 3.6 regime segmentation: PASS')