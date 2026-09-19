#!/usr/bin/env python3
from __future__ import annotations
import csv, statistics, sys
from pathlib import Path
from phase12_execution_simulator import Quote, validate_quote, top_of_book_spread_bps

def load(path: Path):
    rows=[]
    with path.open(newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                q=Quote(r["symbol"],r["datetime"],float(r["bid_px"]),float(r["bid_qty"]),float(r["ask_px"]),float(r["ask_qty"]))
                validate_quote(q)
            except Exception:
                continue
            rows.append((r,q))
    return rows

def main():
    path=Path(sys.argv[1])
    rows=load(path)
    spreads=[top_of_book_spread_bps(q) for _,q in rows]
    print({
        "valid_quotes":len(rows),
        "unique_symbols":len({r["name"] for r,_ in rows}),
        "spread_bps_median":statistics.median(spreads) if spreads else None,
        "spread_bps_p90":statistics.quantiles(spreads,n=10)[8] if len(spreads)>=10 else None,
        "spread_bps_max":max(spreads) if spreads else None,
    })

if __name__=="__main__":
    main()
