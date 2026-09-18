#!/usr/bin/env python3
"""Phase 3.5 descriptive Hurst and MFDFA diagnostics."""
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

def slope(x, y):
    c = np.polyfit(x, y, 1)
    fit = np.polyval(c, x)
    ssr = float(np.sum((y-fit)**2))
    sst = float(np.sum((y-np.mean(y))**2))
    r2 = 1.0-ssr/sst if sst > 0 else float('nan')
    return float(c[0]), r2

def scales_for(n):
    s = [8,12,16,24,32,48,64]
    s = [v for v in s if v <= n//4]
    if len(s) < 4: raise ValueError('At least 64 returns required')
    return s

def variances(profile, scale, order):
    n = len(profile); count = n//scale
    if count < 2: return np.array([], dtype=float)
    out=[]; x=np.arange(scale,dtype=float)
    for offset in (0, n-count*scale):
        for i in range(count):
            seg=profile[offset+i*scale:offset+(i+1)*scale]
            coef=np.polyfit(x,seg,order)
            d=seg-np.polyval(coef,x)
            out.append(float(np.mean(d*d)))
    return np.asarray(out)

def dfa(x, scales, order):
    profile=np.cumsum(x-np.mean(x)); f=[]; used=[]
    for s in scales:
        v=variances(profile,s,order); v=v[np.isfinite(v)&(v>0)]
        if len(v)>=2: used.append(s); f.append(float(np.sqrt(np.mean(v))))
    if len(f)<4: raise ValueError('Insufficient valid DFA scales')
    return slope(np.log(used),np.log(f))

def mfdfa(x, scales, qs, order):
    profile=np.cumsum(x-np.mean(x)); result={}
    for q in qs:
        f=[]; used=[]
        for s in scales:
            v=variances(profile,s,order); v=v[np.isfinite(v)&(v>0)]
            if len(v)<2: continue
            if q==0: fq=float(np.exp(0.5*np.mean(np.log(v))))
            else: fq=float(np.mean(v**(q/2.0))**(1.0/q))
            if np.isfinite(fq) and fq>0: used.append(s); f.append(math.log(fq))
        if len(f)<4: raise ValueError('Insufficient MFDFA scales')
        h,r2=slope(np.log(used),np.asarray(f)); result[str(q)]={'h':h,'r2':r2,'scales_used':len(used)}
    return result

def bootstrap(x,scales,order,reps,seed):
    if reps<=0: return [float('nan'),float('nan')]
    n=len(x); block=max(4,int(round(math.sqrt(n)))); starts=np.arange(n-block+1); rng=np.random.default_rng(seed); vals=[]
    for _ in range(reps):
        a=[]
        while len(a)<n:
            st=int(rng.choice(starts)); a.extend(x[st:st+block].tolist())
        try:
            h,_=dfa(np.asarray(a[:n]),scales,order)
            if np.isfinite(h): vals.append(h)
        except ValueError: pass
    if len(vals)<max(5,reps//4): return [float('nan'),float('nan')]
    return [float(v) for v in np.quantile(vals,[0.025,0.975])]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--output',required=True); ap.add_argument('--dfa-order',type=int,default=1); ap.add_argument('--bootstrap',type=int,default=100); ap.add_argument('--seed',type=int,default=20260918); a=ap.parse_args()
    if a.dfa_order<0 or a.dfa_order>3: raise SystemExit('dfa-order must be 0..3')
    df=pd.read_csv(a.input)
    if not {'timestamp','close'}.issubset(df.columns): raise SystemExit('timestamp and close required')
    df['timestamp']=pd.to_datetime(df['timestamp'],utc=True,errors='coerce'); df['close']=pd.to_numeric(df['close'],errors='coerce')
    df=df.dropna(subset=['timestamp','close']).sort_values('timestamp').drop_duplicates('timestamp')
    if len(df)<65: raise SystemExit('At least 65 price observations required')
    if (df['close']<=0).any(): raise SystemExit('Non-positive close detected')
    r=np.log(df['close']).diff().dropna().to_numpy(dtype=float)
    if len(r)<64: raise SystemExit('At least 64 return observations required')
    scales=scales_for(len(r)); qs=[-2.0,-1.0,0.0,1.0,2.0]
    h,r2=dfa(r,scales,a.dfa_order); ci=bootstrap(r,scales,a.dfa_order,a.bootstrap,a.seed)
    surrogate=r.copy(); np.random.default_rng(a.seed).shuffle(surrogate); sh,sr2=dfa(surrogate,scales,a.dfa_order)
    gen=mfdfa(r,scales,qs,a.dfa_order); width=float(gen['-2.0']['h']-gen['2.0']['h'])
    out={'phase':'3.5','status':'BASELINE','rows':int(len(df)),'return_observations':int(len(r)),'start':df['timestamp'].iloc[0].isoformat(),'end':df['timestamp'].iloc[-1].isoformat(),'dfa':{'hurst':h,'r2':r2,'order':a.dfa_order,'scales':scales,'moving_block_bootstrap_95ci':ci,'bootstrap_replicates_requested':a.bootstrap,'bootstrap_seed':a.seed},'shuffled_surrogate':{'hurst':sh,'r2':sr2,'seed':a.seed},'mfdfa':{'q_values':qs,'generalized_hurst':gen,'multifractal_width_h_minus2_minus_h_plus2':width},'diagnostic_only':True,'execution_backtest_allowed':False,'notes':'Hurst and MFDFA are estimator- and scale-dependent. Deviation from 0.5 is not evidence of inefficiency or tradability; real-data use requires pre-specified sampling, sessionization, scale ranges, surrogate controls and uncertainty assessment.'}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')

if __name__=='__main__': main()