#!/usr/bin/env python3
"""Phase 3.6 descriptive regime segmentation.

Transparent, non-predictive segmentation using rolling return volatility
terciles and return direction. No model fitting or forecasting is performed.
"""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--window',type=int,default=20)
    a=ap.parse_args()
    if a.window<5: raise SystemExit('window must be >=5')
    df=pd.read_csv(a.input)
    if not {'timestamp','close'}.issubset(df.columns): raise SystemExit('timestamp and close required')
    df['timestamp']=pd.to_datetime(df['timestamp'],utc=True,errors='coerce')
    df['close']=pd.to_numeric(df['close'],errors='coerce')
    df=df.dropna(subset=['timestamp','close']).sort_values('timestamp').drop_duplicates('timestamp')
    if len(df)<a.window+10: raise SystemExit('Insufficient observations for regime segmentation')
    if (df['close']<=0).any(): raise SystemExit('Non-positive close detected')
    df['return']=np.log(df['close']).diff()
    df['rolling_vol']=df['return'].rolling(a.window,min_periods=a.window).std(ddof=1)
    work=df.dropna(subset=['return','rolling_vol']).copy()
    if len(work)<10: raise SystemExit('Insufficient valid rolling observations')
    q1,q2=[float(x) for x in work['rolling_vol'].quantile([1/3,2/3]).to_numpy()]
    if not q1<q2: raise SystemExit('Volatility quantiles are not distinct')
    def label(row):
        vol='LOW_VOL' if row.rolling_vol<=q1 else ('MID_VOL' if row.rolling_vol<=q2 else 'HIGH_VOL')
        direction='UP' if row['return']>0 else ('DOWN' if row['return']<0 else 'FLAT')
        return vol+'_'+direction
    work['regime']=work.apply(label,axis=1)
    counts=work['regime'].value_counts().sort_index()
    regimes={}
    for name,g in work.groupby('regime',sort=True):
        regimes[name]={'observations':int(len(g)),'fraction':float(len(g)/len(work)),'mean_return':float(g['return'].mean()),'mean_abs_return':float(g['return'].abs().mean()),'mean_rolling_vol':float(g['rolling_vol'].mean())}
    labels=work['regime'].to_numpy()
    transitions={}
    for x,y in zip(labels[:-1],labels[1:]): transitions[x+'->'+y]=transitions.get(x+'->'+y,0)+1
    runs=[]; start=0
    for i in range(1,len(labels)):
        if labels[i]!=labels[i-1]: runs.append((labels[i-1],i-start)); start=i
    runs.append((labels[-1],len(labels)-start))
    run_summary={}
    for name in sorted(set(labels)):
        vals=[n for lab,n in runs if lab==name]
        run_summary[name]={'runs':len(vals),'mean_run_length':float(np.mean(vals)),'max_run_length':int(max(vals))}
    out={'phase':'3.6','status':'BASELINE','rows':int(len(df)),'usable_rows':int(len(work)),'start':df['timestamp'].iloc[0].isoformat(),'end':df['timestamp'].iloc[-1].isoformat(),'window':a.window,'volatility_tercile_cutoffs':{'q1':q1,'q2':q2},'regimes':regimes,'transition_counts':dict(sorted(transitions.items())),'run_length_summary':run_summary,'diagnostic_only':True,'predictive_model':False,'execution_backtest_allowed':False,'notes':'Regimes are descriptive labels based on full-sample rolling volatility terciles and contemporaneous return direction. They are not forecasts and must not be used as leakage-safe predictive states without a separate training-only specification.'}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')

if __name__=='__main__': main()