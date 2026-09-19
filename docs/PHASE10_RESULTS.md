# Phase 10 Results — Execution Data Audit

## External source verification

NSE's current historical-data documentation confirms that F&O historical trade data and historical order-and-trade data are separate products from ordinary EOD data. NSE also documents complete timestamped historical order-book events and executed trades, delivered through its historical-data infrastructure. The v1.18 specification explicitly defines F&O order and trade record layouts and jiffy-time conversion. citeturn518668view0turn565377view0turn565377view1turn772539view0

## Repository audit

A repository search found no licensed historical F&O order/trade/quote dataset. The existing research data are EOD option records and reconstructed IV surfaces. Therefore an execution-realistic backtest cannot honestly be declared DATA-READY from the current repository alone.

## Engineering completed

Phase 10 now contains:

- a parser for the current 2026-05-18+ F&O trim order/trade layouts;
- support for historically relevant full-layout record lengths used during the existing research period;
- exact jiffy-to-UTC conversion;
- SHA-256 source hashing;
- deterministic record-length/layout detection;
- normalization of common NIFTY OPTIDX contract fields;
- hard failure on unsupported record lengths;
- explicit rejection accounting;
- unit tests using synthetic records only for parser correctness.

Synthetic records are used only for software tests; they are not market observations and are never used for strategy performance estimates.

## Critical conclusion

**Phase 10 is software-ready but DATA-BLOCKED.** The exchange/vendor execution dataset must be acquired/licensed before Phase 11 can produce genuine executable P&L.

NSE's current specification also states that the current trim FAO layout is 91 bytes for orders and 103 bytes for trades, while historical full layouts changed at documented dates. The parser therefore does not assume one fixed record length across the entire history. citeturn999730view0turn772539view0

## What can proceed without fabrication

The next code stage can build the complete multi-strategy execution simulator and exposure engine against this normalized schema. Once one licensed sample day is supplied, the simulator can be validated end-to-end without changing the frozen signal logic.

No bid/ask or depth has been fabricated from EOD settlement prices, and no new strategy has been selected from the rejected 2026 forward sample.
