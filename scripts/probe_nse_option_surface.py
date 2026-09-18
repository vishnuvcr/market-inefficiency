#!/usr/bin/env python3
"""Probe whether NSE contract-wise historical API can return a NIFTY option cross-section."""
from __future__ import annotations
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path
import requests

API_URL="https://www.nseindia.com/api/historicalOR/foCPV"
REPORT_URL="https://www.nseindia.com/report-detail/fo_eq_security"
HEADERS={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36","Accept":"application/json,text/plain,*/*","Accept-Language":"en-US,en;q=0.9","Referer":REPORT_URL}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",default="14-05-2026")
    ap.add_argument("--output",default="data/nse_probe/nse_surface_probe.json")
    args=ap.parse_args()
    s=requests.Session(); s.headers.update(HEADERS)
    out={"probe_utc":datetime.now(timezone.utc).isoformat(),"request":{"from":args.date,"to":args.date,"instrumentType":"OPTIDX","symbol":"NIFTY","year":int(args.date[-4:])},"diagnostic_only":True,"execution_backtest_allowed":False}
    try:
        land=s.get(REPORT_URL,timeout=30)
        out["landing_status"]=land.status_code
        time.sleep(1)
        r=s.get(API_URL,params={"from":args.date,"to":args.date,"instrumentType":"OPTIDX","symbol":"NIFTY","year":int(args.date[-4:])},timeout=60)
        out["response"]={"status":r.status_code,"url":r.url,"content_type":r.headers.get("content-type"),"bytes":len(r.content)}
        p=r.json()
        data=p.get("data") if isinstance(p,dict) else p
        out["payload_keys"]=sorted(p.keys()) if isinstance(p,dict) else []
        out["row_count"]=len(data) if isinstance(data,list) else None
        out["sample_rows"]=data[:5] if isinstance(data,list) else None
    except Exception as e:
        out["error"]=f"{type(e).__name__}: {e}"
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(out,indent=2,default=str)+"\n")
    print(json.dumps(out,indent=2,default=str))
if __name__=="__main__": main()
