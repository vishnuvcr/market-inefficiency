# Phase 10 — Historical Execution Data Protocol

## Objective

Build an execution-grade NIFTY OPTIDX research layer using genuine historical NSE order/trade data or an equivalent licensed quote source. EOD settlement data remain a separate research layer and must never be relabelled as bid/ask history.

## External-data finding

NSE currently exposes paid historical F&O trade data and historical order-and-trade data. The current NSE specification states that historical order/trade files contain timestamped order-book events and executed trades. The current F&O trim format contains all order ticks and all trade ticks; current trim records are fixed-length 91 bytes for orders and 103 bytes for trades. The specification also documents older full-format record sizes and their effective-date changes.

Phase 10 therefore has a two-part gate:

1. software/schema readiness inside this repository;
2. acquisition of actual licensed historical files into a private research environment.

The second part cannot be completed honestly without the licensed data itself.

## Accepted historical layouts

| Data | Format | Record length | Effective boundary |
|---|---|---:|---|
| FAO orders | Trim | 91 | 2026-05-18 onward |
| FAO trades | Trim | 103 | 2026-05-18 onward |
| FAO orders | Full | 111 / 112 | 112 from 2022-02-01 |
| FAO trades | Full | 123 / 124 | 124 from 2020-09-07 |

The parser infers layout from the supplied format/record length and preserves the source specification version in the manifest.

## Normalized order schema

`source_file`, `source_format`, `schema_version`, `session_date`, `order_number`, `event_time`, `side`, `activity`, `symbol`, `instrument`, `expiry`, `strike`, `option_type`, `quantity_lots`, `limit_price`, `spread_type`, `spread_price_sign`, `available_at`

## Normalized trade schema

`source_file`, `source_format`, `schema_version`, `session_date`, `trade_time`, `symbol`, `instrument`, `expiry`, `strike`, `option_type`, `trade_price`, `quantity_lots`, `buy_order_number`, `sell_order_number`, `available_at`

## Jiffy conversion

Jiffies are converted using the NSE specification: 65,536 jiffies per second, with the epoch at 1980-01-01 00:00:00 GMT. The normalized timestamp is stored in UTC and an Asia/Kolkata presentation timestamp may be derived. Microsecond precision is retained; conversion must not round timestamps before event sequencing.

## Order-book reconstruction rules

Order-entry, order-modification and order-cancellation events are replayed strictly in timestamp/order-sequence order. Each contract is identified by symbol + instrument + expiry + strike + option type. Unknown cancel/modify references are counted as data-quality events rather than silently discarded.

Displayed bid/ask may be reconstructed only when the replayed outstanding-order book contains valid live orders. No midpoint is created when one side is missing. Crossed books, negative/zero prices, impossible quantities, duplicate event keys and time reversals are flagged.

## Executable fill rules

All option-leg fills must be generated from contemporaneous reconstructed quotes/order-book state or actual trade prints. A settlement price, OHLC price, or model price cannot substitute for a historical quote.

Multi-leg strategies require a documented synchronization window, leg-order sequence, partial-fill treatment and cancellation/rollback policy. Strategy-level fill is invalid when required legs cannot be filled within the preregistered synchronization rules.

## Point-in-time rule

Every normalized event carries `available_at`. A backtest decision may use only events with `available_at <= decision_time`. Licensed historical-file delivery metadata are stored separately from exchange event time.

## Data-quality acceptance gate

Phase 10 is DATA-READY only when:

- source licence/provenance is recorded;
- every file has a cryptographic hash;
- record lengths match the applicable historical boundary;
- jiffy conversion round-trips within the documented precision;
- event sequences are monotone within stream;
- contract fields are valid;
- duplicate events are measured;
- unknown cancels/modifications are measured;
- reconstructed books have no unaccounted negative quantity;
- crossed/locked/missing/stale quote rates are reported;
- contract-master joins and lot sizes pass PIT validation;
- a representative NIFTY OPTIDX day passes end-to-end replay.

## Current decision

The repository is software-ready for the execution-data gate, but no licensed historical order/trade file is present in the repository or accessible research artifact set. Therefore Phase 10 is not marked DATA-READY and no executable backtest is claimed.

### Scientific guardrail

Do not infer bid/ask history from EOD settlement, LTP, OHLC, volume or open interest. Do not manufacture depth. Do not tune the next strategy on the rejected four-trade 2026 forward sample.