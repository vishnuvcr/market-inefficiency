# Phase 9A — Execution-Grade Surface Relative-Value Protocol

## Objective

Convert the surviving Phase 8C volatility-surface signal into an executable, market-neutral research test without changing the signal after observing strategy P&L.

The current surviving signal is future surface-shape evolution, especially 30D downside skew. Phase 9A does not assume that this signal is profitable. It tests whether a tradable option structure can load on the predicted surface change and still retain positive net P&L after realistic execution costs.

## Research question

> Given information available at decision time t, does the frozen surface-dynamics predictor identify an option relative-value trade whose realized, executable P&L is positive after spread, slippage, leg synchronization, fees/taxes, margin and financing assumptions?

This is a strategy-conversion question, not another predictive-feature search.

## Data gate

The existing EOD settlement/IV dataset is sufficient for signal construction and theoretical P&L diagnostics, but not for executable promotion.

Execution validation requires historical market data containing, at minimum:

- timestamped NIFTY OPTIDX quotes or order/trade observations;
- bid and ask prices and sizes where available;
- contract identifiers, expiry, strike and option type;
- trade/order timestamps with documented clock convention;
- enough information to reconstruct contemporaneous executable prices;
- historical contract/lot-size information;
- margin/risk-parameter inputs where available.

NSE documents historical F&O order and trade datasets separately from EOD data, with order/trade ticks and transaction timestamps. These are therefore an explicit acquisition gate rather than something inferred from EOD settlement data.

## Frozen predictor

Phase 8C is frozen before strategy construction:

- 30D downside skew;
- 30D upside skew;
- 30D–60D ATM term slope;
- predictor coefficients and feature standardization from the already completed validation specification;
- no re-fitting on strategy P&L;
- no forward-period feature selection.

Primary target: future change in 30D downside skew.

The model output is converted into an expected surface move, not directly into a directional NIFTY forecast.

## Strategy library

The initial strategy library is deliberately broad. No single structure is designated as the winner.

### Surface-relative-value candidates

1. Delta-matched downside-skew verticals.
2. Delta-matched upside-skew verticals.
3. Put/call risk reversals with explicit delta hedging.
4. ATM butterflies/flies designed to isolate curvature.
5. Skew butterflies designed to isolate downside or upside skew.
6. Calendar structures comparing matched-delta short and longer-dated wings.
7. Four-leg surface boxes combining downside/upside skew exposures.
8. Iron condors as a hybrid VRP + surface-shape candidate.
9. Straddles/strangles only where their surface exposure is explicitly mapped and the signal predicts the relevant surface component.

Each family must be tested in both economic directions where meaningful. The system must choose trade direction from the pre-registered predicted surface change, not from realized P&L.

## Exposure normalization

Every candidate is represented by:

- delta;
- vega;
- gamma;
- theta;
- exposure to downside skew;
- exposure to upside skew;
- exposure to ATM level;
- exposure to term slope;
- maximum loss;
- margin requirement.

The research engine will not compare raw rupee P&L across structures. Candidate trades are normalized by a documented risk budget and/or maximum loss.

Where practical, delta is neutralized at entry. Any delta hedge must use information available at the hedge timestamp and must itself incur modeled execution cost.

## Execution model

For each leg:

1. Construct the executable side from contemporaneous bid/ask.
2. Reject quotes that are stale, crossed, locked, missing, zero-sized or outside documented quality limits.
3. Apply a synchronization window to prevent impossible multi-leg fills.
4. Model leg sequencing rather than assuming simultaneous fills.
5. Apply spread cost and slippage separately.
6. Record partial-fill and unfilled-leg outcomes.
7. Apply brokerage, exchange charges, taxes and other documented costs when the required inputs are available.
8. Apply margin/risk constraints and capital utilization.
9. Mark all entries/exits to executable prices, never to settlement midpoint.

Execution sensitivity must be evaluated over a pre-registered grid rather than selecting a favourable cost after seeing results.

## Signal-to-trade mapping

For a candidate structure j:

Expected surface move -> structure exposure -> signed trade -> delta hedge -> executable entry -> exit

The sign of the trade is determined before realized P&L is observed.

A structure is only eligible when its dominant exposure matches the predicted surface component and its unintended exposures remain within the pre-registered tolerance.

## Exit rules

Initial evaluation should use fixed, pre-registered holding horizons aligned with the predictor target, plus clearly specified event/expiry exits.

No optimization of exit timing against the final holdout is permitted.

## Validation hierarchy

Phase 9A must run in this order:

1. Data availability audit
2. Quote/order/trade schema validation
3. Timestamp and PIT audit
4. Contract/lot-size reconciliation
5. Executable-price reconstruction
6. Theoretical structure exposure validation
7. Cost and margin model
8. Historical development backtest
9. CPCV with purge/embargo appropriate to the holding horizon
10. DSR/PBO/multiple-testing controls
11. Stress tests
12. Untouched final forward period
13. Decision

No strategy is promoted because it is profitable on settlement-based proxy P&L.

## Required diagnostics

For every candidate:

- gross P&L;
- net P&L;
- Sharpe/Sortino;
- win rate;
- average win/loss;
- maximum drawdown;
- tail loss / expected shortfall;
- turnover;
- average holding period;
- capital/margin usage;
- spread paid;
- slippage;
- fill rate;
- leg mismatch rate;
- delta exposure;
- vega/skew exposure;
- P&L attribution by volatility level and regime;
- P&L attribution by expiry/maturity bucket;
- sensitivity to transaction costs;
- CPCV path distribution;
- PBO/DSR diagnostics.

## Promotion gate

A candidate remains RESEARCH-CANDIDATE unless all required economic and statistical gates pass.

Promotion requires, at minimum:

- positive net performance under the base cost model;
- survival across the preregistered cost-sensitivity grid;
- positive/acceptable CPCV robustness;
- no material degradation under execution stress;
- DSR/PBO results consistent with a non-overfit explanation;
- positive result on the untouched final forward period;
- no unresolved PIT or execution-data defects.

The exact numerical thresholds remain those already defined in the repository validation framework unless a threshold is explicitly preregistered before the relevant experiment.

## Important negative-control tests

The workflow must include:

- shuffled signal control;
- sign-flipped signal control;
- delayed-signal control;
- random-entry control;
- surface-feature permutation control where appropriate.

A strategy that only works with the exact realized ordering but not under leakage-safe controls may still be real, but must be interpreted cautiously and cannot be promoted solely on that basis.

## Data-acquisition decision

NSE currently advertises historical F&O EOD data separately from historical order/trade data. The official historical order/trade specification describes all-order ticks and trade ticks with transaction timestamps. Therefore the next engineering gate is to acquire a documented historical order/trade/quote dataset or explicitly classify Phase 9A as blocked for executable validation.

No bid/ask history will be fabricated from OHLC or settlement data.

## Expected outcomes

There are three scientifically valid outcomes:

1. Executable edge survives — proceed to independent paper-trading validation.
2. Surface prediction survives but monetization fails — retain the predictive surface result and reject the tested strategy families.
3. Surface prediction itself fails when translated to executable observations — retire the corresponding strategy hypothesis and continue to the next independent inefficiency track.

The research objective is not to force outcome 1.
