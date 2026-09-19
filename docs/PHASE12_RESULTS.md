# Phase 12 — Execution Simulator Results

## Public execution-data samples acquired

Two public NIFTY Level-2/top-of-book samples are now preserved as **software-validation fixtures**:

1. TickBytes NIFTY option sample: timestamped L1 quote fields plus five visible depth levels.
2. OptionVault NIFTY Level-2 sample: timestamped five-level bid/ask depth with quantities.

Both repositories describe their public files as representative/evaluation samples rather than a complete multi-month research archive. TickBytes states that its full daily feed is a subscription product, while OptionVault states that the complete historical dataset is licensed and the repository samples are provided for evaluation. citeturn112898search0turn112898search1

The fixtures are **not** used for strategy performance, CPCV, PBO, DSR, or any profitability claim.

## Simulator correction

A real implementation bug was fixed: the simulator accepted a `max_time_gap_seconds` argument but previously ignored it and required exact timestamp equality. It now parses ISO-8601 timestamps and rejects multi-leg execution when the quote timestamp span exceeds the declared synchronization window.

The engine remains fail-closed:

- rejects non-finite, non-positive and crossed quotes;
- buys at contemporaneous ask and sells at contemporaneous bid;
- rejects insufficient displayed size;
- rejects missing legs;
- enforces the declared multi-leg timestamp window;
- computes net cash flow from actual quoted prices.

## Quote audit

The quote audit now accepts both common public schemas (`bid_px/ask_px` and `bid_price1/ask_price1`), counts rejected rows by reason, detects duplicate symbol/timestamp keys and reports median/P90/max top-of-book spread.

This is deliberately an **input-quality audit**, not a performance report.

## Critical limitation

The available public fixtures are small representative samples. They cannot provide statistically meaningful historical executable P&L for the surface strategies.

NSE's historical F&O order/trade infrastructure remains the required source for a genuine execution-grade economic backtest; ordinary EOD option records are not substituted for those observations.

## Phase 12 decision

**ENGINE PASS; ECONOMIC BACKTEST STILL DATA-BLOCKED.**

The software path is ready. The remaining serious blocker is bulk historical execution data with sufficient timestamped quote/order/trade coverage, contract identity, lot-size provenance, and PIT execution information.
