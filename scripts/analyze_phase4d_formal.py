#!/usr/bin/env python3
"""Phase 4D: formal, leakage-safe H-A2/H-B1/H-C1 diagnostics.

Uses only the frozen Phase 4B IV observations plus the official NIFTY underlying.
The first 80% of chronological observations is the training/calibration set;
the final 20% is a one-shot chronological holdout. All state thresholds,
standardization constants, and H-B1 calibration coefficients are estimated
using training data only.

H-A2: holdout VRP differences across LOW/MID/HIGH trailing-volatility states.
H-B1: holdout jump-variance residual from an ex-ante downside-tail IV proxy.
H-C1: holdout predictive value of surface shape for subsequent 30D shape change.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

GAP_DATES={"2021-03-30","2024-03-02"}
TRAIN_FRAC=0.80
WINDOW=20
TARGET_DAYS=(30,60)


def norm_p(t):
    if not np.isfinite(t): return np.nan
    return float(math.erfc(abs(float(t))/math.sqrt(2.0)))


def nw_se_mean(x,max_lag=10):
    x=np.asarray(x,dtype=float); x=x[np.isfinite(x)]
    n=len(x)
    if n<5: return (np.nan,np.nan,np.nan)
    mu=x.mean(); u=x-mu; L=min(max_lag,n-1)
    var=np.mean(u*u)
    for k in range(1,L+1):
        g=np.mean(u[k:]*u[:-k]); w=1-k/(L+1.0); var += 2*w*g
    se=math.sqrt(max(var,0)/n)
    return float(mu),float(se),float(mu/se if se else np.nan)


def ols_hac(X,y,max_lag=10):
    X=np.asarray(X,dtype=float); y=np.asarray(y,dtype=float)
    ok=np.isfinite(y) & np.isfinite(X).all(axis=1); X=X[ok]; y=y[ok]
    n,k=X.shape
    if n<=k+2: return {"n":int(n),"beta":[],"se":[],"t":[],"p":[],"r2":np.nan}
    xtx=X.T@X; inv=np.linalg.pinv(xtx); beta=inv@(X.T@y)
    e=y-X@beta
    S=np.zeros((k,k)); L=min(max_lag,n-1)
    xe=X*e[:,None]
    S += xe.T@xe
    for lag in range(1,L+1):
        w=1-lag/(L+1.0)
        g=xe[lag:].T@xe[:-lag]
        S += w*(g+g.T)
    cov=inv@S@inv
    se=np.sqrt(np.maximum(np.diag(cov),0))
    t=np.divide(beta,se,out=np.full_like(beta,np.nan),where=se>0)
    yy=y-y.mean(); r2=float(1-(e@e)/(yy@yy)) if yy@yy>0 else np.nan
    return {"n":int(n),"beta":beta.tolist(),"se":se.tolist(),"t":t.tolist(),"p":[norm_p(v) for v in t],"r2":r2}


def load_iv(root):
    files=sorted(root.rglob("iv_observations_*.csv.gz"))
    if not files: raise SystemExit("No Phase 4B IV observation partitions found")
    frames=[]
    for p in files:
        df=pd.read_csv(p)
        need={"trade_date","expiry","strike","option_type","moneyness","ttm_days","iv"}
        miss=need-set(df.columns)
        if miss: raise SystemExit(f"{p}: missing {sorted(miss)}")
        df["trade_date"]=pd.to_datetime(df.trade_date,errors="coerce")
        df["expiry"]=pd.to_datetime(df.expiry,errors="coerce")
        for c in ["moneyness","ttm_days","iv"]: df[c]=pd.to_numeric(df[c],errors="coerce")
        df["option_type"]=df.option_type.astype(str).str.upper()
        frames.append(df)
    x=pd.concat(frames,ignore_index=True)
    x=x[~x.trade_date.dt.strftime("%Y-%m-%d").isin(GAP_DATES)]
    x=x[(x.iv>0)&(x.iv<=5)&(x.ttm_days>0)&(x.moneyness>0)]
    return x.sort_values(["trade_date","expiry","moneyness"])


def load_underlying(path):
    u=pd.read_csv(path)
    u["date"]=pd.to_datetime(u.date,errors="coerce")
    u["close"]=pd.to_numeric(u.close,errors="coerce")
    u=u.dropna(subset=["date","close"]); u=u[u.close>0].drop_duplicates("date").sort_values("date").reset_index(drop=True)
    u["ret"]=np.log(u.close/u.close.shift(1))
    u["trailing_sigma_daily"]=u.ret.shift(1).rolling(WINDOW).std(ddof=1)
    u["trailing_vol_ann"]=u.trailing_sigma_daily*np.sqrt(252)
    u["trailing_ret20"]=u.ret.shift(1).rolling(WINDOW).sum()
    return u


def band_expiry(df,typ,lo,hi):
    mask=df["moneyness"].between(lo,hi)
    if typ: mask &= df["option_type"].eq(typ)
    z=df.loc[mask,["trade_date","expiry","ttm_days","iv"]]
    if z.empty: return pd.DataFrame(columns=["trade_date","expiry","ttm_days","iv"])
    return z.groupby(["trade_date","expiry","ttm_days"],as_index=False)["iv"].median()


def constant_maturity_band(expiry_df,target_days):
    rows=[]
    if expiry_df.empty: return pd.DataFrame(columns=["trade_date","iv"])
    for d,g in expiry_df.groupby("trade_date",sort=True):
        g=g.sort_values("ttm_days")
        t=g.ttm_days.to_numpy(float); iv=g.iv.to_numpy(float)
        ok=np.isfinite(t)&np.isfinite(iv)&(t>0)&(iv>0)
        t=t[ok]; iv=iv[ok]
        if len(t)<2: continue
        exact=np.where(t==target_days)[0]
        if len(exact): val=iv[exact[0]]
        else:
            l=np.where(t<target_days)[0]; r=np.where(t>target_days)[0]
            if len(l)==0 or len(r)==0: continue
            i=l[-1]; j=r[0]
            wi=(target_days-t[i])/(t[j]-t[i])
            w1=iv[i]**2*t[i]/365.0; w2=iv[j]**2*t[j]/365.0
            val=math.sqrt(max((w1+wi*(w2-w1))/(target_days/365.0),0))
        rows.append({"trade_date":d,"iv":float(val)})
    return pd.DataFrame(rows)


def build_surface_features(iv):
    frames=[]
    atm=band_expiry(iv,None,0.97,1.03)
    down=band_expiry(iv,"PE",0.85,0.95)
    up=band_expiry(iv,"CE",1.05,1.15)
    for h in TARGET_DAYS:
        a=constant_maturity_band(atm,h).rename(columns={"iv":f"atm_iv_{h}"})
        d=constant_maturity_band(down,h).rename(columns={"iv":f"down_iv_{h}"})
        q=constant_maturity_band(up,h).rename(columns={"iv":f"up_iv_{h}"})
        x=a.merge(d,on="trade_date",how="inner").merge(q,on="trade_date",how="inner")
        x[f"down_skew_{h}"]=x[f"down_iv_{h}"]-x[f"atm_iv_{h}"]
        x[f"up_skew_{h}"]=x[f"up_iv_{h}"]-x[f"atm_iv_{h}"]
        x[f"down_var_premium_{h}"]=np.maximum(x[f"down_iv_{h}"]**2-x[f"atm_iv_{h}"]**2,0.0)
        x[f"up_var_premium_{h}"]=np.maximum(x[f"up_iv_{h}"]**2-x[f"atm_iv_{h}"]**2,0.0)
        frames.append(x)
    x=frames[0]
    for f in frames[1:]: x=x.merge(f,on="trade_date",how="inner")
    x["term_slope_30_60"]=x["atm_iv_60"]-x["atm_iv_30"]
    return x.sort_values("trade_date").reset_index(drop=True)


def realized_variance(u,target_days):
    dates=u.date.to_numpy(dtype="datetime64[ns]"); r=u.ret.to_numpy(float); out=[]
    for i,d in enumerate(dates):
        j=int(np.searchsorted(dates,d+np.timedelta64(target_days,'D'),side='left'))
        if j>=len(dates) or j<=i: continue
        rr=r[i+1:j+1]; rr=rr[np.isfinite(rr)]
        if len(rr)<5: continue
        actual=int((dates[j]-d)/np.timedelta64(1,'D'))
        if actual<=0: continue
        out.append({"trade_date":pd.Timestamp(d),"rv":float(np.sum(rr*rr)*365/actual)})
    return pd.DataFrame(out)


def jump_outcome(u,target_days):
    dates=u.date.to_numpy(dtype="datetime64[ns]"); r=u.ret.to_numpy(float); sig=u.trailing_sigma_daily.to_numpy(float); out=[]
    for i,d in enumerate(dates):
        j=int(np.searchsorted(dates,d+np.timedelta64(target_days,'D'),side='left'))
        if j>=len(dates) or j<=i or not np.isfinite(sig[i]) or sig[i]<=0: continue
        rr=r[i+1:j+1]; rr=rr[np.isfinite(rr)]
        if len(rr)<5: continue
        actual=int((dates[j]-d)/np.timedelta64(1,'D'))
        if actual<=0: continue
        th=3*sig[i]
        jump=rr[np.abs(rr)>th]
        jump_rv=float(np.sum(jump*jump)*365/actual)
        total_rv=float(np.sum(rr*rr)*365/actual)
        out.append({"trade_date":pd.Timestamp(d),"jump_rv":jump_rv,"total_rv":total_rv,"jump_count":int(len(jump)),"threshold_daily":float(th)})
    return pd.DataFrame(out)


def split_idx(df):
    n=len(df); cut=max(1,min(n-1,int(math.floor(n*TRAIN_FRAC))))
    return df.iloc[:cut].copy(),df.iloc[cut:].copy()


def freeze_z(train,col):
    mu=float(train[col].mean()); sd=float(train[col].std(ddof=0)); sd=sd if sd>0 else 1.0
    return mu,sd


def make_atm_iv(iv,target_days):
    return constant_maturity_band(band_expiry(iv,None,0.97,1.03),target_days).rename(columns={"iv":"atm_iv"})


def do_ha2(iv,u):
    out=[]
    for h in TARGET_DAYS:
        imp=make_atm_iv(iv,h); rv=realized_variance(u,h)
        x=imp.merge(rv,on="trade_date",how="inner")
        state=u[["date","trailing_vol_ann"]].rename(columns={"date":"trade_date"})
        x=x.merge(state,on="trade_date",how="left")
        x["vrp"] = x.atm_iv**2-x.rv
        x=x.dropna(subset=["vrp","trailing_vol_ann"]).sort_values("trade_date").reset_index(drop=True)
        train,hold=split_idx(x)
        q1,q2=train.trailing_vol_ann.quantile([1/3,2/3]).to_numpy()
        for g in [train,hold]:
            g["regime"]=pd.cut(g.trailing_vol_ann,bins=[-np.inf,q1,q2,np.inf],labels=["LOW","MID","HIGH"])
        means={k:float(hold.loc[hold.regime==k,"vrp"].mean()) for k in ["LOW","MID","HIGH"]}
        ns={k:int((hold.regime==k).sum()) for k in ["LOW","MID","HIGH"]}
        reg=pd.get_dummies(hold.regime,drop_first=False).reindex(columns=["MID","HIGH"],fill_value=False).astype(float)
        X=np.column_stack([np.ones(len(hold)),reg[["MID","HIGH"]].to_numpy(float)])
        fit=ols_hac(X,hold.vrp.to_numpy(float),max_lag=max(10,h//4))
        out.append({
            "horizon_days":h,
            "train_n":len(train),
            "holdout_n":len(hold),
            "train_start":train.trade_date.min().strftime('%Y-%m-%d'),
            "holdout_start":hold.trade_date.min().strftime('%Y-%m-%d'),
            "q1_training_vol":float(q1),
            "q2_training_vol":float(q2),
            "holdout_group_means":means,
            "holdout_group_n":ns,
            "holdout_contrasts":{
                "MID_minus_LOW":fit["beta"][1],"MID_minus_LOW_se":fit["se"][1],
                "MID_minus_LOW_t":fit["t"][1],"MID_minus_LOW_p_normal":fit["p"][1],
                "HIGH_minus_LOW":fit["beta"][2],"HIGH_minus_LOW_se":fit["se"][2],
                "HIGH_minus_LOW_t":fit["t"][2],"HIGH_minus_LOW_p_normal":fit["p"][2]
            },
            "holdout_hac_regression":fit
        })
    return out


def do_hb1(features,u):
    j=jump_outcome(u,30)
    x=features.merge(j,on="trade_date",how="inner")
    x=x.merge(u[["date","trailing_vol_ann"]].rename(columns={"date":"trade_date"}),on="trade_date",how="left")
    x=x.dropna(subset=["jump_rv","down_var_premium_30","atm_iv_30","trailing_vol_ann"]).sort_values("trade_date").reset_index(drop=True)
    x["atm_var_30"]=x.atm_iv_30**2
    x["trail_var"]=(x.trailing_vol_ann/np.sqrt(252))**2
    train,hold=split_idx(x)
    predictors=["down_var_premium_30","atm_var_30","trail_var"]
    scalers={}
    for c in predictors:
        mu,sd=freeze_z(train,c); scalers[c]={"mean":mu,"std":sd}
    def X_from(g,include_tail=True):
        cols=predictors if include_tail else predictors[1:]
        arr=[np.ones(len(g))]
        arr.extend([(g[c].to_numpy(float)-scalers[c]["mean"])/scalers[c]["std"] for c in cols])
        return np.column_stack(arr)
    fit=ols_hac(X_from(train),train.jump_rv.to_numpy(float),max_lag=10)
    beta=np.asarray(fit["beta"]); pred=X_from(hold)@beta
    hold=hold.copy(); hold["pred_jump_rv"]=pred; hold["residual"]=hold.jump_rv-hold.pred_jump_rv
    mu,se,t=nw_se_mean(hold.residual.to_numpy(),max_lag=10)
    fit0=ols_hac(X_from(train,include_tail=False),train.jump_rv.to_numpy(float),max_lag=10)
    pred0=X_from(hold,include_tail=False)@np.asarray(fit0["beta"])
    rmse1=float(np.sqrt(np.mean((hold.jump_rv-pred)**2)))
    rmse0=float(np.sqrt(np.mean((hold.jump_rv-pred0)**2)))
    return {
        "train_n":len(train),"holdout_n":len(hold),
        "train_start":train.trade_date.min().strftime('%Y-%m-%d'),
        "holdout_start":hold.trade_date.min().strftime('%Y-%m-%d'),
        "jump_definition":"future daily squared log returns exceeding 3x decision-day 20-session daily sigma",
        "implied_tail_proxy":"30D downside-wing implied variance above 30D ATM implied variance; max(IV_down^2-IV_ATM^2,0)",
        "training_predictor_standardization":scalers,
        "training_calibration":fit,
        "holdout_residual_mean":{
            "mean":mu,"se":se,"t":t,"p_normal":norm_p(t),
            "ci95_low":mu-1.96*se,"ci95_high":mu+1.96*se
        },
        "holdout_rmse_with_tail":rmse1,
        "holdout_rmse_control_only":rmse0,
        "oos_rmse_delta":rmse0-rmse1,
        "holdout_mean_jump_rv":float(hold.jump_rv.mean()),
        "holdout_mean_tail_proxy":float(hold.down_var_premium_30.mean())
    }


def future_value(df,col,days):
    d=df[["trade_date",col]].dropna().sort_values("trade_date")
    dates=d.trade_date.to_numpy(dtype='datetime64[ns]'); vals=d[col].to_numpy(float); out=[]
    for i,dt in enumerate(dates):
        j=int(np.searchsorted(dates,dt+np.timedelta64(days,'D'),side='left'))
        if j>=len(dates): continue
        out.append((pd.Timestamp(dt),vals[i],vals[j]))
    return pd.DataFrame(out,columns=["trade_date","value_now","value_future"])


def do_hc1(features,u):
    x=features.copy()
    fut=future_value(x,"down_skew_30",30).rename(columns={"value_now":"down_skew_now","value_future":"down_skew_future"})
    x=x.merge(fut[["trade_date","down_skew_future"]],on="trade_date",how="inner")
    x["down_skew_change"]=x.down_skew_future-x.down_skew_30
    ctrl=u[["date","trailing_vol_ann","trailing_ret20"]].rename(columns={"date":"trade_date"})
    x=x.merge(ctrl,on="trade_date",how="inner")
    x=x.dropna(subset=["down_skew_change","down_skew_30","up_skew_30","term_slope_30_60","atm_iv_30","trailing_vol_ann","trailing_ret20"]).sort_values("trade_date").reset_index(drop=True)
    train,hold=split_idx(x)
    feature_names=["down_skew_30","up_skew_30","term_slope_30_60"]
    results=[]
    predictor_names=["atm_iv_30","trailing_vol_ann","trailing_ret20"]
    for f in feature_names:
        cols=[f]+predictor_names
        scalers={}
        for c in cols:
            mu,sd=freeze_z(train,c); scalers[c]={"mean":mu,"std":sd}
        def zframe(g):
            return np.column_stack([np.ones(len(g))]+[((g[c].to_numpy(float)-scalers[c]["mean"])/scalers[c]["std"]) for c in cols])
        Xtr=zframe(train); fit=ols_hac(Xtr,train.down_skew_change.to_numpy(float),max_lag=10)
        Xh=zframe(hold); pred=Xh@np.asarray(fit["beta"])
        null=float(train.down_skew_change.mean()); baseline=np.full(len(hold),null)
        sse=float(np.sum((hold.down_skew_change-pred)**2))
        sse0=float(np.sum((hold.down_skew_change-baseline)**2))
        oos_r2=float(1-sse/sse0) if sse0>0 else np.nan
        hold_fit=ols_hac(Xh,hold.down_skew_change.to_numpy(float),max_lag=10)
        results.append({
            "feature":f,
            "predictor_standardization":"training mean/std; coefficients are per training SD",
            "training_scalers":scalers,
            "training_model":fit,
            "holdout_descriptive_model":hold_fit,
            "oos_r2_vs_train_mean":oos_r2
        })
    return {
        "train_n":len(train),"holdout_n":len(hold),
        "train_start":train.trade_date.min().strftime('%Y-%m-%d'),
        "holdout_start":hold.trade_date.min().strftime('%Y-%m-%d'),
        "target":"change in subsequent 30D downside IV skew over the next >=30 calendar days",
        "results":results
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--iv-root',type=Path,required=True)
    ap.add_argument('--underlying',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    iv=load_iv(args.iv_root)
    u=load_underlying(args.underlying)
    features=build_surface_features(iv)
    ha2=do_ha2(iv,u)
    hb1=do_hb1(features,u)
    hc1=do_hc1(features,u)
    manifest_path=args.iv_root/'PHASE4B_IV_MANIFEST.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    report={
        "status":"PASS",
        "phase":"4D",
        "objective":"Formal leakage-safe H-A2/H-B1/H-C1 diagnostics",
        "frozen_inputs":{
            "phase4b_manifest_status":manifest.get("status"),
            "phase4b_manifest_model":manifest.get("model"),
            "input_iv_rows":int(len(iv)),
            "iv_trade_dates":int(iv.trade_date.nunique())
        },
        "holdout_rule":"first 80% chronological calibration/training; final 20% untouched chronological holdout",
        "ha2_state_rule":"20-session trailing annualized realized volatility; LOW/MID/HIGH cutpoints frozen from training terciles",
        "H-A2":ha2,
        "H-B1":hb1,
        "H-C1":hc1,
        "multiple_testing":"H-A2 has four holdout state contrasts; interpret each p-value with Bonferroni alpha=0.05/4. H-C1 has three preregistered shape features; interpret holdout coefficient p-values with Bonferroni alpha=0.05/3 only as descriptive diagnostics; primary OOS metric is OOS R2.",
        "interpretation_guardrail":"These are formal diagnostics on a single chronological holdout, not a net-of-cost trading strategy. H-B1 tail proxy is a wing-skew proxy, not a pure option-model jump measure. H-C1 uses subsequent change in 30D downside skew as the primary outcome; OOS R2 is predictive evidence, not a trading return."
    }
    (args.output/'PHASE4D_FORMAL_REPORT.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
    audit=features.merge(
        u[["date","trailing_vol_ann","trailing_ret20"]].rename(columns={"date":"trade_date"}),
        on='trade_date',how='left'
    )
    audit.to_csv(args.output/'phase4d_surface_features.csv.gz',index=False,compression='gzip')
    print(json.dumps(report,indent=2,default=str))


if __name__=='__main__':
    main()
