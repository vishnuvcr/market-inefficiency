#!/usr/bin/env python3
"""Phase 8B: fresh-forward validation of an underlying-only volatility-state model.

This is an independent reduced-feature branch. It deliberately excludes fresh
options so that the robustness of the volatility-expansion signal can be tested
on a genuinely later NIFTY period even when option acquisition is unavailable.
The Phase 5 price+volatility feature family and model hyperparameters are frozen.
"""
from __future__ import annotations
import argparse, itertools, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

GAPS={"2021-03-30","2024-03-02"}
FEATURES=["ret1","ret5","ret20","ret60","z20","drawdown_60",
          "ret_autocorr20","absret_autocorr20","rv_5","rv_20","rv_60",
          "vol_ratio_5_20"]
CANDIDATES=["highvol_trend","highvol_meanrev","state_switch"]
THRESH=0.55
COSTS=(5,10,20)

def build(path:Path):
    x=pd.read_csv(path)
    dc=next(c for c in ["date","DATE","CH_TIMESTAMP","TIMESTAMP"] if c in x)
    cc=next(c for c in ["close","CLOSE","Close"] if c in x)
    x=x.rename(columns={dc:"date",cc:"close"})[["date","close"]]
    x["date"]=pd.to_datetime(x["date"],errors="coerce")
    x["close"]=pd.to_numeric(x["close"],errors="coerce")
    x=x.dropna().query("close>0").drop_duplicates("date").sort_values("date").reset_index(drop=True)
    x=x[~x.date.dt.strftime("%Y-%m-%d").isin(GAPS)].copy()
    x["ret1"]=np.log(x.close/x.close.shift(1)); x["ret5"]=np.log(x.close/x.close.shift(5))
    x["ret20"]=np.log(x.close/x.close.shift(20)); x["ret60"]=np.log(x.close/x.close.shift(60))
    for w in (5,20,60):
        x[f"rv_{w}"]=np.sqrt(x.ret1.shift(1).rolling(w).apply(lambda z: np.sum(np.asarray(z)**2)*252.0/len(z),raw=False))
    x["vol_ratio_5_20"]=x.rv_5/x.rv_20
    x["z20"]=(x.close-x.close.shift(1).rolling(20).mean())/x.close.shift(1).rolling(20).std(ddof=0)
    x["drawdown_60"]=x.close/x.close.shift(1).rolling(60).max()-1
    x["ret_autocorr20"]=x.ret1.shift(1).rolling(20).corr(x.ret1.shift(2))
    a=x.ret1.abs(); x["absret_autocorr20"]=a.shift(1).rolling(20).corr(a.shift(2))
    x["target_ret1"]=x.ret1.shift(-1)
    f5=np.log(x.close.shift(-5)/x.close); x["target_ret5"]=f5
    rv5=x.ret1.shift(-1).rolling(5).apply(lambda z: np.sum(np.asarray(z)**2)*252.0/len(z),raw=False).shift(-4)
    x["target_vol_expand5"]=(rv5>x.rv_20**2).astype(float)
    return x

def model(): return make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(C=0.5,max_iter=3000,solver="lbfgs"))

def pos(name,row,p):
    if name=="highvol_trend": return float(np.sign(row.ret20)) if p>=THRESH else 0.
    if name=="highvol_meanrev": return float(-np.sign(row.z20)) if p>=THRESH else 0.
    if name=="state_switch":
        if p>=THRESH: return float(np.sign(row.ret20))
        if p<=1-THRESH: return float(-np.sign(row.z20))
        return 0.
    raise ValueError(name)

def metrics(r):
    r=pd.Series(r).replace([np.inf,-np.inf],np.nan).dropna()
    if len(r)<20:return {"n":int(len(r)),"sharpe":float("nan")}
    sd=float(r.std(ddof=1)); sh=float(r.mean()/sd*math.sqrt(252)) if sd>0 else float("nan")
    w=(1+r).cumprod()
    return {"n":len(r),"mean_daily":float(r.mean()),"sharpe":sh,
            "max_drawdown":float((w/w.cummax()-1).min()),
            "positive_fraction":float((r>0).mean()),
            "trade_day_fraction":float((r!=0).mean())}

def evaluate(df,p,cost):
    out={}
    z=df.reset_index(drop=True)
    for name in CANDIDATES:
        prev=0.; arr=[]
        for i,row in z.iterrows():
            q=pos(name,row,float(p[i])); turn=abs(q-prev)
            gross=q*float(row.target_ret1); net=gross-turn*cost/10000
            arr.append(net); prev=q
        m=metrics(arr); m.update({"candidate":name,"cost_bps":cost})
        out[name]=m
    return out

def cpcv(dev,cost):
    n=len(dev); edges=np.linspace(0,n,9,dtype=int)
    blocks=[np.arange(edges[i],edges[i+1]) for i in range(8)]
    rows=[]
    for pair in itertools.combinations(range(8),2):
        test=np.concatenate([blocks[i] for i in pair]); mask=np.ones(n,dtype=bool); mask[test]=False
        train=dev.iloc[np.where(mask)[0]].copy(); testdf=dev.iloc[test].copy()
        if len(train)<200 or len(testdf)<30: continue
        m=model(); m.fit(train[FEATURES],train.target_vol_expand5.astype(int))
        pt=m.predict_proba(testdf[FEATURES])[:,1]
        mt=evaluate(testdf,pt,cost)
        for name in CANDIDATES: rows.append({"pair":str(pair),"candidate":name,"sharpe":mt[name]["sharpe"]})
    d=pd.DataFrame(rows); s={}
    for name in CANDIDATES:
        q=d.loc[d.candidate.eq(name),"sharpe"]
        s[name]={"paths":len(q),"median_sharpe":float(q.median()),"mean_sharpe":float(q.mean()),
                 "positive_path_fraction":float((q>0).mean())}
    return {"paths":int(d.pair.nunique()),"candidate_summaries":s}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--old",type=Path,required=True); ap.add_argument("--new",type=Path,required=True); ap.add_argument("--forward-start",required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); old=build(a.old); new=build(a.new)
    u=pd.concat([old,new]).drop_duplicates("date").sort_values("date").reset_index(drop=True)
    fs=pd.Timestamp(a.forward_start); data=u.dropna(subset=FEATURES+["target_ret1","target_vol_expand5"]).copy()
    dev=data[data.date<fs].copy(); fwd=data[data.date>=fs].copy()
    m=model(); m.fit(dev[FEATURES],dev.target_vol_expand5.astype(int))
    p=m.predict_proba(fwd[FEATURES])[:,1]
    auc=float(roc_auc_score(fwd.target_vol_expand5.astype(int),p)) if fwd.target_vol_expand5.nunique()==2 else float("nan")
    forward={str(c):evaluate(fwd,p,c) for c in COSTS}
    missing_forward={k:int(fwd[k].isna().sum()) for k in FEATURES+["target_ret1","target_vol_expand5"]}
    devc={str(c):cpcv(dev,c) for c in COSTS}
    promo={}
    for n in CANDIDATES:
        s=devc["20"]["candidate_summaries"][n]; q=forward["20"][n]
        promo[n]={"promotable":bool(s["median_sharpe"]>0 and s["positive_path_fraction"]>=.60 and q["sharpe"]>0 and q["mean_daily"]>0),
                  "dev_median_cpcv_sharpe":s["median_sharpe"],"dev_positive_path_fraction":s["positive_path_fraction"],
                  "forward_sharpe":q["sharpe"],"forward_mean_daily":q["mean_daily"]}
    out={"status":"PASS","phase":"8B","objective":"fresh-forward reduced price+volatility test of five-session volatility expansion",
         "data":{"dev_rows":len(dev),"dev_end":str(dev.date.max().date()),"forward_rows":len(fwd),"forward_start":str(fwd.date.min().date()),"forward_end":str(fwd.date.max().date()),"fresh_rows_before_feature_filter":int((u.date>=fs).sum()),"feature_missing_counts_in_forward_pre_filter":missing_forward},
         "model":{"features":FEATURES,"logistic_C":.5,"threshold":THRESH,"specification_frozen_from_phase5_price_vol":True},
         "forward_volatility_prediction":{"auc":auc,"accuracy":float(accuracy_score(fwd.target_vol_expand5.astype(int),p>=.5)),"brier":float(brier_score_loss(fwd.target_vol_expand5.astype(int),p)),"expansion_rate":float(fwd.target_vol_expand5.mean())},
         "forward_cost_sensitivity":forward,"development_cpcv":devc,"promotion_gates":promo,
         "decision":{"promotable_candidates":[n for n,v in promo.items() if v["promotable"]],"gate":"20bps: median CPCV Sharpe>0, positive-path>=60%, positive forward mean and Sharpe"},
         "guardrails":{"execution":"NIFTY close-to-close settlement proxy","costs":"fixed bps per side","options":"not used in 8B","status":"research-only"}}
    a.out.mkdir(parents=True,exist_ok=True); (a.out/"PHASE8B_UNDERLYING_VOL_REPORT.json").write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))

if __name__=="__main__": main()
