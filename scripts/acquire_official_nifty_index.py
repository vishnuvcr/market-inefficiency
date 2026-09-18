#!/usr/bin/env python3
"""Acquire official NIFTY 50 price-index OHLC from NSE Indices."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime
from pathlib import Path
import requests

URL = "https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString"
HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.niftyindices.com/reports/historical-data",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36",
}
def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--start",required=True); ap.add_argument("--end",required=True)
    ap.add_argument("--output",default="data/phase4a/external/nifty_index")
    a=ap.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    s=datetime.strptime(a.start,"%Y-%m-%d").strftime("%d-%b-%Y")
    e=datetime.strptime(a.end,"%Y-%m-%d").strftime("%d-%b-%Y")
    cinfo=str({"name":"NIFTY 50","startDate":s,"endDate":e,"indexName":"NIFTY 50"}).replace('"',"'")
    r=requests.post(URL,headers=HEADERS,json={"cinfo":cinfo},timeout=60)
    r.raise_for_status()
    raw=out/"response.json"; raw.write_text(r.text)
    body=r.json().get("d","[]")
    rows=json.loads(body) if isinstance(body,str) else body
    if not rows: raise SystemExit("NIFTY 50 historical endpoint returned no rows")
    import csv
    csvp=out/"nifty50_ohlc.csv"
    with csvp.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["date","open","high","low","close"]); w.writeheader()
        for x in rows:
            w.writerow({"date":x.get("HistoricalDate"),"open":x.get("OPEN"),"high":x.get("HIGH"),"low":x.get("LOW"),"close":x.get("CLOSE")})
    meta={"source_url":URL,"index":"NIFTY 50","requested_period":[a.start,a.end],"retrieved_at_utc":datetime.utcnow().isoformat()+"Z","rows":len(rows),"raw_sha256":sha256(raw),"csv_sha256":sha256(csvp)}
    (out/"MANIFEST.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))
if __name__=="__main__": main()
