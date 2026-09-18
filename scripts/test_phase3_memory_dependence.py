#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(12345); r=rng.normal(0,0.0005,128); close=25000*np.exp(np.cumsum(r))
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp); fixture=p/'input.csv'; out=p/'result.json'
    ts=pd.date_range('2026-09-18T03:45:00Z',periods=len(close),freq='min')
    pd.DataFrame({'timestamp':ts,'close':close}).to_csv(fixture,index=False)
    subprocess.run([sys.executable,str(ROOT/'scripts/phase3_memory_dependence.py'),'--input',str(fixture),'--output',str(out),'--bootstrap','20'],check=True)
    d=json.loads(out.read_text())
    assert d['phase']=='3.5' and d['status']=='BASELINE'
    assert d['return_observations']==127 and len(d['dfa']['scales'])>=4
    assert np.isfinite(d['dfa']['hurst']) and len(d['dfa']['moving_block_bootstrap_95ci'])==2
    assert np.isfinite(d['shuffled_surrogate']['hurst'])
    assert set(d['mfdfa']['generalized_hurst'])=={'-2.0','-1.0','0.0','1.0','2.0'}
    assert np.isfinite(d['mfdfa']['multifractal_width_h_minus2_minus_h_plus2'])
    assert d['diagnostic_only'] is True and d['execution_backtest_allowed'] is False
print('Phase 3.5 memory/dependence diagnostics: PASS')