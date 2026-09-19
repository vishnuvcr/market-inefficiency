# Phase 12 — Execution Simulator Results

## Public execution-data sample acquired

A 50-row public NIFTY option-feed sample from TickBytes was imported as a test fixture. The sample contains timestamped option rows with L1 quote fields (`bid_px`, `ask_px`, `bid_qty`, `ask_qty`) and five visible depth levels. It is a schema/engine validation sample, not a historical backtest dataset. TickBytes states that its full feed is a subscription product; the repository exposes representative samples under an MIT licence. citeturn435086view0turn435086view1

## Simulator completed

The engine now:

- rejects missing, zero-size, non-finite and crossed quotes;
- buys at contemporaneous ask and sells at contemporaneous bid;
- rejects legs whose displayed quantity cannot satisfy the requested size;
- requires synchronized leg timestamps in the sample mode;
- calculates strategy net cash flow from actual quoted execution prices;
- preserves a clean separation between quote-based execution and EOD settlement research.

## Key limitation

The public sample is only a representative 50-row snapshot, not a multi-month historical quote/order/trade archive. Therefore it can validate the mechanics but cannot supply statistically meaningful executable P&L.

NSE's own documentation confirms that historical F&O order/trade data is a separate paid data product, while sample archives are provided publicly. citeturn725691view0

## Phase 12 decision

**ENGINE PASS; ECONOMIC BACKTEST STILL DATA-BLOCKED.**

No historical bid/ask series has been fabricated from settlement data. The execution engine is ready to consume licensed historical quotes/order-trade files once supplied.
