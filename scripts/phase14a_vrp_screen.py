#!/usr/bin/env python3
"""Phase 14A.1 — NIFTY variance-risk-premium discovery screen.

Frozen implementation:
- signal = 30-day ATM implied volatility minus 20-session trailing realised volatility;
- choose the expiry closest to 30 calendar days within a fixed 25–35 day window;
- choose the strike closest to spot;
- when signal is positive, short one ATM straddle to expiry;
- accept the earliest non-overlapping eligible trade only;
- settlement prices are used only as a non-executable economic proxy.

No threshold/lookback/expiry/strike optimisation is performed.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

COSTS=(0.0,5.0,10.0,20.0,40.0)
N_GROUPS=8
N_TEST=2
RNG_SEED=20260919


def annualised_event_sharpe(x: np.ndarray) -> float | None:
    if len(x)<2 or np.std(x,ddof=1)<=0:
        return None
    return float(np.mean(x)/np.std(x,ddof=1)*math.sqrt(252/30))


def cpcv(x: np.ndarray) -> np.ndarray:
    n=len(x); groups=np.floor(np.arange(n)*N_GROUPS/n).astype(int); out=[]
    for tg in combinations(range(N_GROUPS),N_TEST):
        y=x[np.isin(groups,tg)]
        s=annualised_event_sharpe(y)
        if s is not None: out.append(s)
    return np.asarray(out,dtype=float)


def one_sided_p(x: np.ndarray)->float:
    t,p2=stats.ttest_1samp(x,0.0)
    return float(p2/2 if t>0 else 1-p2/2)


def nonoverlap(df: pd.DataFrame)->pd.DataFrame:
    out=[]; next_allowed=pd.Timestamp.min
    for _,r in df.sort_values('entry').iterrows():
        if r.entry>next_allowed:
            out.append(r); next_allowed=r.expiry
    return pd.DataFrame(out)


def load_data(surface_path:str, obs_glob:str, ohlc_path:str)->tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    surf=pd.read_csv(surface_path,usecols=['trade_date','expiry','ttm_days','atm_iv','spot'],parse_dates=['trade_date','expiry'])
    surf=surf[(surf.ttm_days>=25)&(surf.ttm_days<=35)].copy()
    surf['dist']=(surf.ttm_days-30).abs()
    surf=surf.sort_values(['trade_date','dist','expiry']).groupby('trade_date',sort=False).head(1)
    ohlc=pd.read_csv(ohlc_path,usecols=['date','close'],parse_dates=['date']).sort_values('date')
    ohlc['rv20']=np.log(ohlc.close).diff().rolling(20).std()*np.sqrt(252)
    base=surf.merge(ohlc[['date','rv20']],left_on='trade_date',right_on='date',how='left').drop(columns='date')
    base=base[(base.trade_date<'2026-05-15')&base.rv20.notna()].copy()
    targets=base[['trade_date','expiry','atm_iv','rv20','spot']].drop_duplicates()
    frames=[]
    for path in glob.glob(obs_glob):
        obs=pd.read_csv(path,usecols=['trade_date','expiry','strike','option_type','settlement'],parse_dates=['trade_date','expiry'])
        m=obs.merge(targets,on=['trade_date','expiry'],how='inner')
        m=m[m.option_type.isin(['CE','PE'])]
        if not m.empty: frames.append(m)
    obs=pd.concat(frames,ignore_index=True)
    piv=obs.pivot_table(index=['trade_date','expiry','strike','spot','atm_iv','rv20'],columns='option_type',values='settlement',aggfunc='last').reset_index()
    piv=piv.dropna(subset=['CE','PE'])
    piv['dist']=(piv.strike-piv.spot).abs()
    piv=piv.sort_values(['trade_date','expiry','dist','strike']).groupby(['trade_date','expiry'],sort=False).head(1)
    expiry_spot=ohlc.rename(columns={'date':'expiry','close':'expiry_close'})[['expiry','expiry_close']]
    alltr=targets.merge(piv[['trade_date','expiry','strike','CE','PE']],on=['trade_date','expiry'],how='inner').merge(expiry_spot,on='expiry',how='inner')
    alltr['premium']=alltr.CE+alltr.PE
    alltr['payoff']=(alltr.expiry_close-alltr.strike).abs()
    alltr['short_pnl']=alltr.premium-alltr.payoff
    alltr['ret']=alltr.short_pnl/alltr.spot
    alltr['signal_value']=alltr.atm_iv-alltr.rv20
    return targets,alltr,ohlc


def summarize(x:np.ndarray, premium_ratio:np.ndarray)->dict:
    grid={}
    for c in COSTS:
        y=x-2*c/1e4*premium_ratio
        wealth=np.cumprod(1+y); dd=wealth/np.maximum.accumulate(wealth)-1
        paths=cpcv(y)
        grid[str(c)]={
          'n_events':int(len(y)),
          'mean_event_return':float(np.mean(y)),
          'median_event_return':float(np.median(y)),
          'event_sharpe':annualised_event_sharpe(y),
          'win_rate':float(np.mean(y>0)),
          'max_drawdown':float(np.min(dd)),
          'one_sided_t_p':one_sided_p(y),
          'cpcv_median_sharpe':float(np.median(paths)),
          'cpcv_q10_sharpe':float(np.quantile(paths,.10)),
          'cpcv_positive_path_fraction':float(np.mean(paths>0)),
        }
    return {'cost_grid':grid}


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--surface',required=True); ap.add_argument('--obs-glob',required=True)
    ap.add_argument('--ohlc',required=True); ap.add_argument('--output',required=True)
    args=ap.parse_args()
    _,alltr,_=load_data(args.surface,args.obs_glob,args.ohlc)
    primary=nonoverlap(alltr[alltr.signal_value>0].copy())
    long_control=primary.copy(); long_control['ret']=-long_control['ret']
    rng=np.random.default_rng(RNG_SEED)
    shuffled_signal=alltr.copy()
    shuffled_signal['random_signal']=rng.random(len(shuffled_signal))
    random_rows=[]
    next_allowed=pd.Timestamp.min
    for _, row in shuffled_signal.sort_values('entry').iterrows():
        if row.entry>next_allowed and row.random_signal>0.5:
            random_rows.append(row)
            next_allowed=row.expiry
    random_control=pd.DataFrame(random_rows)
    results={
      'VRP_SHORT_STRADDLE':summarize(primary.ret.to_numpy(float),(primary.premium/primary.spot).to_numpy(float)),
      'SIGN_FLIP_LONG_STRADDLE':summarize(long_control.ret.to_numpy(float),(long_control.premium/long_control.spot).to_numpy(float)),
      'RANDOM_ENTRY':summarize(random_control.ret.to_numpy(float),(random_control.premium/random_control.spot).to_numpy(float)),
    }
    events=primary[['trade_date','expiry','strike','premium','payoff','short_pnl','ret','signal_value','atm_iv','rv20']].copy()
    events.to_csv(Path(args.output).with_suffix('.events.csv'),index=False)
    p={k:results[k]['cost_grid']['0.0']['one_sided_t_p'] for k in results}
    out={
      'phase':'14A.1','track':'options_variance_risk_premium',
      'development_end':'2026-05-14','forward_period_excluded':'2026-05-15_to_2026-09-18',
      'signal':'30D ATM IV > trailing 20-session realised volatility',
      'entry':'closest 30D expiry in fixed 25-35 day window, closest-to-spot strike, close-to-close settlement proxy',
      'exit':'option expiry intrinsic payoff',
      'overlap':'earliest eligible trade only; next entry must be after prior expiry',
      'cost_grid_bps_per_side':list(COSTS),'rng_seed':RNG_SEED,
      'results':results,
      'primary_zero_cost_pvalue':p['VRP_SHORT_STRADDLE'],
      'multiple_testing_not_finalised':True,
      'execution_label':'settlement_proxy_only',
      'decision':'DISCOVERY_POSITIVE_ONLY_UNTIL_LATER_UNTOUCHED_HOLDOUT_AND_EXECUTION_TEST',
    }
    Path(args.output).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()