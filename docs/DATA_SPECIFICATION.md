# Data Specification v1.1

## Purpose

This document defines the minimum research-grade data contract for the market-inefficiency program. It separates public EOD/stylized-fact inputs from higher-resolution quote/trade inputs required by experiments that depend on implied volatility, intraday realization, liquidity or execution.

The machine-readable contract is `config/data_schema.json` and is validated by `scripts/validate_data_schema.py`.

## Time and point-in-time rules

- Store normalized timestamps in UTC.
- Interpret exchange session dates and source timestamps in `Asia/Kolkata` unless the source explicitly specifies another timezone.
- Every research observation and metadata record must carry `available_at`.
- A feature or contract attribute may be used only when `available_at <= decision_timestamp`.
- Contract specifications, lot sizes and listing intervals are effective-dated and must be joined as-of the decision timestamp; future revisions must not overwrite historical definitions.

## Data layers

### 1. Underlying EOD

Required: `timestamp`, `available_at`, `instrument_id`, `open`, `high`, `low`, `close`, `volume`, `session_id`.

Optional: adjusted close and corporate-action identifiers. The raw source remains preserved so adjusted and unadjusted representations can be reconciled.

Uniqueness key: `instrument_id + timestamp`.

### 2. Option EOD

Required: `timestamp`, `available_at`, `underlying_id`, `expiry`, `strike`, `option_type`, `open`, `high`, `low`, `close`, `last_price`, `volume`, `open_interest`, `settlement`, `lot_size`.

Quote fields where available: `bid`, `ask`, `mid`, `bid_size`, `ask_size`.

Uniqueness key: `underlying_id + expiry + strike + option_type + timestamp`.

`option_type` is restricted to `CE` and `PE`.

### 3. Contract master

Required: `contract_id`, `underlying_id`, `expiry`, `strike`, `option_type`, `lot_size`, `effective_from`, `effective_to`, `available_at`.

Uniqueness key: `contract_id + effective_from`.

Effective intervals must not overlap. Lot size must be positive. Historical experiments must use the contract definition effective at that point in time.

### 4. India VIX

Required: `timestamp`, `available_at`, `close`.

Uniqueness key: `timestamp`.

India VIX is treated as market volatility context, not as a substitute for realized volatility.

### 5. Risk-free series

Required: `timestamp`, `available_at`, `tenor`, `rate`.

Uniqueness key: `timestamp + tenor`.

Rates are stored as decimal annualized values after source-specific normalization.

### 6. Intraday quotes/trades

Required: `timestamp`, `available_at`, `instrument_id`, `event_sequence`.

Quotes may contain `bid`, `ask`, `bid_size`, `ask_size`; trades may contain `trade_price`, `trade_size`, `trade_id`.

Uniqueness key: `instrument_id + timestamp + event_sequence`.

This layer is mandatory only for experiments whose target or execution model depends on intraday information.

## Quote and record hygiene

Reject or flag at ingestion/validation:

- negative prices;
- crossed markets (`bid > ask`);
- invalid/zero bid-ask when midpoint pricing is assumed;
- stale quotes beyond an experiment-defined tolerance;
- duplicate keys;
- impossible expiry/strike relationships;
- missing contract metadata;
- observations outside the valid listing interval;
- non-positive lot sizes;
- overlapping effective-dated contract records.

Every exclusion must be counted and recorded in the dataset quality report. Silent row deletion is prohibited.

## Dataset snapshots

Every immutable snapshot must have a manifest containing:

`dataset_id`, `snapshot_created_at`, `source`, `source_version`, `preprocessing_version`, `code_commit`, `sha256`, `row_count`.

`dataset_id` is immutable. Raw source data is retained separately from transformed research tables. Licensed exchange/vendor data must not be committed to this public repository.

## Source availability boundary

Public NSE EOD/contract/VIX data can support data engineering and baseline stylized-fact work. Historical bid/ask/depth and detailed order/trade data are separate products and must be explicitly acquired or licensed before any experiment is described as quote-level or execution-realistic. The current NSE option-chain interface must not be treated as a complete historical quote archive without evidence.

## Cost-model inputs

The simulator must support configurable bid-ask crossing/slippage, brokerage, statutory taxes/fees where applicable, exchange/clearing charges, market impact, partial fills, latency, financing/carry and margin/capital usage.

## Realized-volatility estimators

The uploaded protocol proposes Yang-Zhang as the primary OHLC estimator with Parkinson and Garman-Klass comparators. The implementation will reproduce all three and test sensitivity rather than assume one estimator is universally superior.

## Acceptance gate

No formal model experiment may proceed until the relevant dataset quality report passes critical checks, excluded observations are counted, the source/licence is documented, point-in-time reconstruction passes, and the immutable snapshot identifier is recorded in the experiment manifest.
