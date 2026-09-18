#!/usr/bin/env python3
"""Probe NSE legacy and UDiFF F&O bhavcopy archive routes around the format boundary."""
from __future__ import annotations
import argparse, hashlib, io, json, zipfile
from datetime import datetime, timezone
from pathlib import Path
import requests

H={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36","Accept":"*/*","Referer":"https://www.nseindia.com/all-reports-derivatives"}
BASE="https://archives.nseindia.com"

def inspect(url, s):
    r=s.get(url,headers=H,timeout=60)
    x={"url":url,"http_status":r.status_code,"content_type":r.headers.get("content-type"),"bytes":len(r.content),"sha256":hashlib.sha256(r.content).hexdigest()}
    if r.status_code==200:
        try:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                names=z.namelist(); x["zip_members"]=names
                csvs=[n for n in names if n.lower().endswith(".csv")]
                if csvs:
                    raw=z.read(csvs[0]); x["csv_member"]=csvs[0]; x["csv_bytes"]=len(raw)
                    head=raw.splitlines()[0].decode("utf-8",errors="replace")
                    x["header"]=head
        except zipfile.BadZipFile:
            x["status"]="BAD_ZIP"
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",default="2024-05-14")
    ap.add_argument("--output",default="data/nse_probe/archive_boundary_probe.json")
    a=ap.parse_args(); d=datetime.strptime(a.date,"%Y-%m-%d")
    stamp=d.strftime("%d%b%Y").upper(); y=d.strftime("%Y"); m=d.strftime("%b").upper()
    urls={
      "legacy":f"{BASE}/content/historical/DERIVATIVES/{y}/{m}/fo{stamp}bhav.csv.zip",
      "udiff":f"{BASE}/content/fo/BhavCopy_NSE_FO_0_0_0_{d.strftime('%Y%m%d')}_F_0000.csv.zip",
    }
    s=requests.Session()
    out={"probe_utc":datetime.now(timezone.utc).isoformat(),"trade_date":a.date,"diagnostic_only":True,"execution_backtest_allowed":False,"routes":{}}
    for k,u in urls.items():
        try: out["routes"][k]=inspect(u,s)
        except Exception as e: out["routes"][k]={"url":u,"error":f"{type(e).__name__}: {e}"}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
