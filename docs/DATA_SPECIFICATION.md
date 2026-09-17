# Data Specification v1.0

## Required data domains

### Underlying

- Timestamp, open, high, low, close, volume.
- Corporate-action adjustments where relevant.
- Trading-session calendar.
- Instrument identifier history.

### Options

At minimum:

- Quote/trade timestamp.
- Underlying identifier.
- Expiry.
- Strike.
- Call/put.
- Bid and ask.
- Last traded price.
- Volume.
- Open interest.
- Quote size/depth when available.
- Contract multiplier/lot size by effective date.
- Settlement conventions.

### Market context

- Risk-free rate or documented proxy.
- India VIX or equivalent volatility-index series.
- Exchange calendar/holidays.
- Event calendar where available and admissible.

### Intraday/microstructure

Required only for experiments that depend on realized intraday variance, order flow, liquidity, or execution.

## Point-in-time rule

Every derived feature must declare `available_at`. The feature timestamp used for a decision must not occur after the simulated decision timestamp.

## Quote hygiene

Reject or flag:

- negative prices;
- bid > ask;
- zero/invalid bid-ask when mid-price is assumed;
- stale quotes outside the experiment-defined tolerance;
- duplicate timestamps/contracts;
- impossible expiry/strike relationships;
- missing contract specification;
- trading outside the instrument's valid listing interval.

## Data versioning

Every experiment records:

`dataset_id + data_snapshot_timestamp + source + preprocessing_version + code_commit`

The same dataset ID must be immutable.

## Cost model inputs

The simulator must support configurable:

- bid-ask crossing/slippage;
- brokerage;
- statutory taxes/fees where applicable;
- exchange/clearing charges;
- impact assumptions;
- partial fills;
- latency;
- financing/carry;
- margin/capital usage.

## Primary realized-volatility estimators

The uploaded protocol proposes Yang-Zhang as the primary OHLC estimator while using Parkinson and Garman-Klass as comparators. The repository will reproduce all three and test sensitivity rather than assuming one estimator is universally superior.

## Data acceptance gate

No model run may proceed to a formal experiment unless the data-quality report passes all critical checks and records the number of excluded observations.
