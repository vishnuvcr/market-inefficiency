# Phase 14 — Broad Inefficiency Discovery and Combination Screening

## Objective

Systematically test the broader market-inefficiency families already identified in the research program **before any parameter optimization**. The purpose is to answer a narrower question than profitability optimization:

> Does each mechanism, by itself, produce a statistically and economically meaningful trading signal under a frozen, simple implementation? If not, does a preregistered combination of distinct mechanisms retain a meaningful edge?

This phase does **not** search for the best lookback, strike, threshold, leverage, model, or portfolio weight. Those belong only to a later optimization phase after a mechanism has first passed the discovery gate.

## Scope

1. Time-series equity effects: momentum, short-horizon reversal, volatility clustering/regime effects, volume/liquidity shocks.
2. Cross-sectional equity effects: cross-sectional momentum, reversal, size/liquidity, abnormal-volume effects.
3. Futures effects: cash-futures basis, calendar basis/roll, expiry effects, open-interest/volume effects.
4. Options effects: aggregate variance risk premium, jump-risk pricing, skew dynamics, term-structure dynamics, volatility-of-volatility, put/call relative value.
5. Index/constituent effects: index-versus-constituents valuation, dispersion/correlation, constituent breadth.
6. Event effects: earnings/announcement drift, index rebalancing, derivatives expiry and roll effects, corporate-action effects.
7. Microstructure effects: spread, depth imbalance, order-flow imbalance, short-horizon lead/lag and price-impact effects.
8. Cross-market effects: global equity lead/lag, USD/INR, rates, volatility indices and other admissible contemporaneous information.
9. Dependence/regime effects: memory, regime transitions, overnight/intraday asymmetry and volatility-state dependence.

A family is **not considered testable** merely because a data source exists. The point-in-time, timestamp, contract-identity and execution requirements below must be satisfied.

## Frozen methodology

Every Phase 14 experiment follows:

`hypothesis -> preregistration -> data snapshot -> feature construction -> fixed baseline -> single-mechanism screen -> fixed-cost trading proxy -> leakage audit -> CPCV -> multiple-testing control -> stress tests -> untouched prospective holdout -> decision`

The project-wide rules remain unchanged:

- No result-driven sign selection.
- No post-result lookback/threshold/holding-period selection.
- No optimization of candidate weights during the discovery screen.
- No re-use of the rejected 2026-05-15 through 2026-09-18 forward period as a tuning sample.
- EOD settlement may be used only for explicitly labelled settlement-proxy diagnostics, never as an executable fill.
- Microstructure claims require genuine timestamped quotes/order/trade data.
- Option claims that depend on bid/ask/depth require execution-grade data.
- All data snapshots are hashed and point-in-time availability is recorded.
- Every retained mechanism must survive the same leakage, cost, CPCV, PBO/DSR and forward-validation gates used elsewhere in the project.

## Phase 14 subphases

### 14.0 Governance and data-readiness freeze

Produce the machine-readable hypothesis registry and data sufficiency matrix.

For each hypothesis record:
- mechanism identifier;
- economic rationale;
- required fields;
- admissible source;
- point-in-time requirement;
- sampling frequency;
- minimum history;
- executable-price requirement;
- fixed baseline trading translation;
- negative controls;
- statistical test;
- status.

Exit: no family enters the screen without a complete preregistration and a declared data-quality gate.

### 14.1 Single-mechanism discovery screen

For each data-ready mechanism, run a deliberately simple, fixed trading translation.

The default discovery implementation is:
- one signal;
- one fixed sign convention defined before seeing results;
- one fixed holding horizon;
- equal-risk sizing;
- no leverage optimization;
- no signal threshold optimization;
- predefined cost grid;
- no overlapping positions unless the hypothesis itself requires overlap.

The screen records:
- gross and net mean return;
- event Sharpe and day-level Sharpe where appropriate;
- win rate;
- drawdown and tail loss;
- turnover;
- exposure/capital proxy;
- cost sensitivity;
- CPCV path distribution;
- negative-control results.

The purpose is **existence detection**, not maximizing performance.

### 14.2 Combination screen

Only after the single-mechanism registry is frozen, test combinations.

Combinations are restricted to preregistered mechanism bundles and **equal-weight / equal-risk aggregation**. No fitted portfolio weight optimization is allowed.

Initial bundles:

- `TS_EQUITY`: momentum + short-horizon reversal + volatility-state signal.
- `XS_EQUITY`: cross-sectional momentum + cross-sectional reversal + liquidity/volume shock.
- `DERIVATIVE_RV`: futures basis + option variance premium + surface-shape signal.
- `SURFACE`: downside skew + upside skew + term slope + volatility-of-volatility proxy.
- `CROSS_MARKET`: global-risk lead/lag + USD/INR + rates/volatility input.
- `INDEX_RELATIVE`: index-versus-constituent valuation + dispersion/correlation + breadth.
- `ALL_READY_EQUAL_RISK`: only mechanisms that independently clear the data-quality gate.

A combination is not allowed to rescue a mechanism by changing its sign after observing results. Component signs remain those preregistered in the component hypothesis.

### 14.3 Statistical validation

For every single mechanism and every preregistered combination:

1. Use chronological development/test construction with the project's existing purge and embargo rules.
2. Run CPCV and retain the full path distribution.
3. Compute PBO from the frozen candidate-selection procedure.
4. Compute DSR using a declared trial count.
5. Apply false-discovery control across the simultaneous mechanism tests.
6. Run sign-flip, delayed-signal, shuffled-feature and random-entry controls where applicable.
7. Repeat at the predefined transaction-cost grid and execution-stress grid.
8. Require economically meaningful effect size, not merely a small p-value.

A family that is statistically significant but economically eliminated by modest predefined costs is classified as **statistically present / not economically usable**, not as a tradable inefficiency.

### 14.4 Prospective holdout

The next genuinely later observations after the Phase 14 specification freeze will be reserved as an untouched prospective holdout.

The already-used **2026-05-15 through 2026-09-18** period is permanently frozen and cannot become the Phase 14 tuning or selection sample.

Until a later untouched period exists, a discovery result can be classified as:
- `DISCOVERY_POSITIVE` — historical evidence only;
- `ECONOMIC_CANDIDATE` — historical net evidence survives all discovery gates;
- `VALIDATED` — only after the untouched later holdout also passes.

### 14.5 Decision taxonomy

Each mechanism receives one of:

- `DATA_BLOCKED`
- `REJECTED_NO_SIGNAL`
- `REJECTED_AFTER_COST`
- `REJECTED_CPCV`
- `REJECTED_MULTIPLE_TESTING`
- `DISCOVERY_POSITIVE`
- `ECONOMIC_CANDIDATE`
- `VALIDATED`

No ranking, winner selection or optimization occurs in Phase 14.

## Data sufficiency rules

### Ready with existing project inputs

- NIFTY daily return/reversal/volatility-regime effects.
- NIFTY option-implied variance versus realized variance.
- NIFTY option-surface skew and term-slope dynamics.
- Some EOD NIFTY futures/option volume, open-interest and expiry effects, subject to contract/PIT validation.

### Requires new point-in-time data

- Cross-sectional equity strategies require historical NIFTY-50 membership/weights plus security-level daily price/volume data.
- Dispersion/correlation requires constituent returns and, for option-based dispersion, constituent-option IV/contract data.
- Event drift requires auditable announcement/earnings/event timestamps.
- Cross-market tests require synchronized historical series and a frozen information-availability convention.
- Intraday reversal/overnight effects require timestamped intraday data.
- Microstructure tests require genuine quote/order/trade history and cannot use settlement proxies.

## Promotion gate for Phase 14

A mechanism or combination may advance to optimization only when all are true:

1. The effect is positive under the frozen trading translation at base costs.
2. The lower confidence bound for the selected return statistic is positive.
3. The CPCV path distribution is materially positive rather than dependent on one split.
4. The result survives the frozen multiple-testing procedure and trial-count accounting.
5. Predefined cost/slippage stress does not eliminate the effect.
6. Negative controls do not reproduce the effect.
7. There is no PIT, overlap, synchronization or contract-specification defect.
8. A genuinely later untouched holdout remains available for the next validation phase.

## Relationship to existing phases

Phase 14 does **not** replace Phase 13. Phase 13 remains the execution-grade statistical validation gate for the option-surface strategy library once genuine historical executable data are available.

Phase 14 is the broader discovery branch. Any Phase 14 candidate that depends on executable quotes/order/trades must ultimately pass the same Phase 10–13 execution-data and statistical gates before paper trading.

## Immediate next action

Execute **14.0**, then run all `DATA_READY` single-mechanism screens before any optimization. No candidate gets tuned merely because an early screen is attractive.
