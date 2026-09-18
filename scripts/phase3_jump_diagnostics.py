#!/usr/bin/env python3
"""Phase 3.4: descriptive jump diagnostics.

Implements range/return-based jump flags without fitting or trading:
- close-to-close standardized return threshold
- bipower-variation-style daily jump proxy from adjacent absolute returns
- OHLC range extension via Parkinson variance
All thresholds and sampling assumptions are explicit. Outputs are diagnostic only.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--z-threshold", type=float, default=3.0)
    args=ap.parse_args()
    if args.z_threshold <= 0:
        raise SystemExit("z-threshold must be positive")
    df=pd.read_csv(args.input)
    required={"timestamp","open","high","low","close"}
    missing=sorted(required-set(df.columns))
    if missing: raise SystemExit(f"Missing required columns: {missing}")
    df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True,errors="coerce")
    for c in ["open","high","low","close"]:
        df[c]=pd.to_numeric(df[c],errors="coerce")
    df=(df.dropna(subset=list(required)).sort_values("timestamp")
          .drop_duplicates("timestamp",keep="first"))
    if len(df)<6: raise SystemExit("At least 6 observations required")
    if (df[["open","high","low","close"]]<=0).any().any():
        raise SystemExit("Non-positive price detected")
    if (df["high"]<df[["open","close"]].max(axis=1)).any() or (df["low"]>df[["open","close"]].min(axis=1)).any():
        raise SystemExit("OHLC consistency violation")
    r=np.log(df["close"]).diff().dropna()
    med=float(r.median())
    mad=float((r-med).abs().median())
    robust_scale=1.4826*mad
    if robust_scale>0:
        robust_z=(r-med)/robust_scale
    else:
        scale=float(r.std(ddof=1))
        robust_z=(r-r.mean())/scale if scale>0 else pd.Series(np.nan,index=r.index)
    jump_mask=robust_z.abs()>args.z_threshold

    abs_r=r.abs().to_numpy()
    bv=(math.pi/2.0)*float(np.sum(abs_r[:-1]*abs_r[1:])) if len(abs_r)>1 else float("nan")
    rv=float(np.sum(r.to_numpy()**2))
    jump_variation=max(rv-bv,0.0) if np.isfinite(bv) else float("nan")

    hl=np.log(df["high"]/df["low"])
    parkinson=float(np.mean(hl.to_numpy()**2)/(4*math.log(2)))
    par_jump=max(rv-parkinson,0.0)

    out={
      "phase":"3.4","status":"BASELINE","rows":int(len(df)),
      "return_observations":int(len(r)),
      "start":df["timestamp"].iloc[0].isoformat(),"end":df["timestamp"].iloc[-1].isoformat(),
      "z_threshold":args.z_threshold,
      "return_location":{"median":med,"mad":mad,"robust_scale":robust_scale},
      "standardized_jump_proxy":{
        "flagged_observations":int(jump_mask.sum()),
        "flag_rate":float(jump_mask.mean()),
        "indices":[int(i) for i in r.index[jump_mask].tolist()]
      },
      "bipower_variation_proxy":{
        "realized_variation":rv,"bipower_variation":bv,
        "excess_variation_proxy":jump_variation
      },
      "range_jump_proxy":{
        "parkinson_variance":parkinson,
        "realized_variation":rv,
        "excess_variation_proxy":par_jump
      },
      "diagnostic_only":True,
      "execution_backtest_allowed":False,
      "notes":"Jump proxies are descriptive and sampling-sensitive. A positive excess proxy is not proof of an economically exploitable jump-risk mispricing."
    }
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
