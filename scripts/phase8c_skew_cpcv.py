#!/usr/bin/env python3
"""Phase 8C: CPCV robustness of the Phase 4D volatility-surface skew signal.

No trading returns are inferred. This tests whether the preregistered H-C1
surface-shape predictors retain out-of-sample information under repeated
chronological combinatorial splits with a conservative 30-calendar-day purge.
"""
from __future__ import annotations
import argparse, itertools, json, math
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TARGET="down_skew_change"
SHAPES=["down_skew_30","up_skew_30","term_slope_30_60"]
CONTROLS=["atm_iv_30","trailing_vol_ann","trailing_ret20"]

def load_iv(root):
    fs=sorted(root.rglob("iv_observations_*.csv.gz"))
    if not fs: raise SystemExit("No IV partitions")
    frames=[]
    for p in fs:
        x=pd.read_csv(p)
        x["trade_date"]=pd.to_datetime(x.trade_date,errors="coerce")
        x["expiry"]=pd.to_datetime(x.expiry,errors="coerce")
        for c in ["moneyness","ttm_days","iv"]: x[c]=pd.to_numeric(x[c],errors="coerce")
        x["option_type"]=x.option_type.astype(str).str.upper()
        frames.append(x)
    x=pd.concat(frames,ignore_index=True)
    x=x[(x.iv>0)&(x.iv<=5)&(x.ttm_days>0)&(x.moneyness>0)].copy()
    return x

def band(iv,typ,lo,hi):
    m=iv.moneyness.between(lo,hi)
    if typ: m &= iv.option_type.eq(typ)
    z=iv.loc[m,["trade_date","expiry","ttm_days","iv"]]
    return z.groupby(["trade_date","expiry","ttm_days"],as_index=False).iv.median()

def const(b,target):
    rows=[]
    for d,g in b.groupby("trade_date",sort=True):
        g=g.sort_values("ttm_days"); t=g.ttm_days.to_numpy(float); v=g.iv.to_numpy(float)
        if len(t)<2: continue
        ex=np.where(t==target)[0]
        if len(ex): val=v[ex[0]]
        else:
            l=np.where(t<target)[0]; r=np.where(t>target)[0]
            if not len(l) or not len(r): continue
            i,j=l[-1],r[0]; w=(target-t[i])/(t[j]-t[i])
            a=v[i]**2*t[i]/365; b2=v[j]**2*t[j]/365
            val=math.sqrt(max((a+w*(b2-a))/(target/365),0))
        rows.append((pd.Timestamp(d),float(val)))
    return pd.DataFrame(rows,columns=["date","iv"])

def surface(iv):
    atm=band(iv,None,.97,1.03); down=band(iv,"PE",.85,.95); up=band(iv,"CE",1.05,1.15)
    out=[]
    for h in (30,60):
        a=const(atm,h).rename(columns={"iv":f"atm_iv_{h}"})
        d=const(down,h).rename(columns={"iv":f"down_iv_{h}"})
        u=const(up,h).rename(columns={"iv":f"up_iv_{h}"})
        q=a.merge(d,on="date").merge(u,on="date")
        q[f"down_skew_{h}"]=q[f"down_iv_{h}"]-q[f"atm_iv_{h}"]
        q[f"up_skew_{h}"]=q[f"up_iv_{h}"]-q[f"atm_iv_{h}"]
        out.append(q)
    x=out[0].merge(out[1],on="date")
    x["term_slope_30_60"]=x.atm_iv_60-x.atm_iv_30
    return x.sort_values("date").reset_index(drop=True)

def target_change(s):
    d=s[["date","down_skew_30"]].dropna().sort_values("date")
    dates=d.date.to_numpy(dtype="datetime64[ns]"); vals=d.down_skew_30.to_numpy(float)
    rows=[]
    for i,dt in enumerate(dates):
        j=int(np.searchsorted(dates,dt+np.timedelta64(30,"D"),side="left"))
        if j<len(dates):
            rows.append((pd.Timestamp(dt),vals[j]-vals[i]))
    return pd.DataFrame(rows,columns=["date",TARGET])

def underlying_controls(path):
    u=pd.read_csv(path)
    u["date"]=pd.to_datetime(u.date,errors="coerce"); u["close"]=pd.to_numeric(u.close,errors="coerce")
    u=u.dropna().query("close>0").drop_duplicates("date").sort_values("date").reset_index(drop=True)
    u["ret1"]=np.log(u.close/u.close.shift(1))
    u["trailing_vol_ann"]=u.ret1.shift(1).rolling(20).std(ddof=1)*math.sqrt(252)
    u["trailing_ret20"]=u.ret1.shift(1).rolling(20).sum()
    return u[["date","trailing_vol_ann","trailing_ret20"]]

def fit_eval(train,test,feature):
    cols=[feature]+CONTROLS
    pipe=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),Ridge(alpha=10.0))
    pipe.fit(train[cols],train[TARGET])
    pred=pipe.predict(test[cols]); y=test[TARGET].to_numpy(float); base=np.full(len(y),train[TARGET].mean())
    sse=float(np.sum((y-pred)**2)); sse0=float(np.sum((y-base)**2))
    return float(1-sse/sse0) if sse0>0 else np.nan

def cpcv(df,purge_days=30,embargo_days=5):
    df=df.sort_values("date").reset_index(drop=True); n=len(df); edges=np.linspace(0,n,9,dtype=int)
    blocks=[np.arange(edges[i],edges[i+1]) for i in range(8)]
    rows=[]
    for pair in itertools.combinations(range(8),2):
        test_idx=np.concatenate([blocks[i] for i in pair]); test=df.iloc[test_idx].copy()
        test_min,test_max=test.date.min(),test.date.max()
        train=df.drop(test_idx).copy()
        # Purge only observations whose label window can overlap a test-date
        # observation. This preserves valid CPCV paths when test blocks are
        # separated in time (e.g. blocks 0 and 7).
        bad=np.zeros(len(train),dtype=bool)
        for td in test.date.to_numpy():
            bad |= train.date.between(
                td-pd.Timedelta(days=int(purge_days)),
                td+pd.Timedelta(days=int(embargo_days))
            ).to_numpy()
        train=train.loc[~bad].copy()
        if len(train)<200 or len(test)<20: continue
        for f in SHAPES:
            rows.append({"pair":str(pair),"feature":f,"oos_r2":fit_eval(train,test,f),
                         "train_n":len(train),"test_n":len(test)})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--iv-root",type=Path,required=True); ap.add_argument("--underlying",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    iv=load_iv(a.iv_root); sf=surface(iv); y=target_change(sf); uc=underlying_controls(a.underlying)
    x=sf.merge(y,on="date").merge(uc,on="date")
    x=x.dropna(subset=SHAPES+CONTROLS+[TARGET]).sort_values("date").reset_index(drop=True)
    res=cpcv(x)
    summary={}
    for f in SHAPES:
        q=res.loc[res.feature.eq(f),"oos_r2"].replace([np.inf,-np.inf],np.nan).dropna()
        summary[f]={"paths":int(len(q)),"median_oos_r2":float(q.median()),"mean_oos_r2":float(q.mean()),
                    "positive_path_fraction":float((q>0).mean()),"q10":float(q.quantile(.10)),"q90":float(q.quantile(.90))}
    out={"status":"PASS","phase":"8C","objective":"CPCV robustness of preregistered H-C1 volatility-surface predictors",
         "sample":{"rows":len(x),"start":x.date.min().strftime("%Y-%m-%d"),"end":x.date.max().strftime("%Y-%m-%d")},
         "target":"subsequent change in 30D downside IV skew at the first observation >=30 calendar days later",
         "model":{"ridge_alpha":10.0,"controls":CONTROLS,"shape_features":SHAPES,"purge_calendar_days":30,"embargo_calendar_days":5,"blocks":8,"test_blocks_per_path":2},
         "cpcv_paths":int(res.pair.nunique()),"summary":summary,
         "decision":{"robust_shape_features":[f for f,s in summary.items() if s["median_oos_r2"]>0 and s["positive_path_fraction"]>=.60],
                     "gate":"median CPCV OOS R2 > 0 and positive-path fraction >= 60%; research diagnostic only; no trading-return claim"}}
    a.out.mkdir(parents=True,exist_ok=True); (a.out/"PHASE8C_SKEW_CPCV_REPORT.json").write_text(json.dumps(out,indent=2))
    res.to_csv(a.out/"phase8c_cpcv_paths.csv",index=False)
    print(json.dumps(out,indent=2))

if __name__=="__main__": main()
