# Phase 4 — Preregistered Candidate Hypotheses and Data Gate

## Purpose

Phase 3 established descriptive stylized facts in NIFTY 50 and India VIX data. Phase 4 converts those observations into falsifiable option-market hypotheses.

No Phase 4 hypothesis is treated as evidence of an inefficiency before point-in-time option data, statistical controls, realistic costs, and untouched holdout validation are passed.

## Primary research universe

- Underlying: NIFTY 50 index
- Derivative: NSE index options (OPTIDX)
- Initial research period: only dates for which all required inputs can be verified as available at the decision timestamp.
- Preferred observation convention: end-of-session option price/settlement paired with the same-session underlying close and a documented risk-free input.
- Quote-based execution analysis is a separate gate because NSE public contract-wise EOD data does not itself establish historical bid/ask/depth.

NSE's historical contract-wise interface exposes symbol, year, expiry, option type and strike filters and downloadable CSV output. It reports option premium turnover, volume and open interest, while NSE separately offers historical order/trade datasets. These sources therefore support an EOD research layer and a later execution layer, but they are not interchangeable. citeturn0search3turn0search0turn0search35

## Hypothesis registry for formal testing

### H-A1 — Aggregate variance-risk premium

**Null:** conditional expected implied variance does not exceed subsequent realized variance after controlling for maturity, moneyness and regime.

**Alternative:** implied variance minus subsequent realized variance is systematically positive in a prespecified subset of contracts/regimes.

**Primary statistic:** mean point-in-time variance spread, reported with HAC/block-bootstrap confidence interval.

**Secondary:** median spread, quantiles, sign frequency, and decomposition by maturity/moneyness/regime.

**Falsification:** effect is not statistically distinguishable from zero after the preregistered dependence adjustment, or disappears under the untouched holdout.

### H-A2 — State dependence of VRP

**Null:** the variance spread is invariant across preregistered volatility/regime states.

**Alternative:** the spread differs across states defined without future information.

**Primary statistic:** out-of-sample difference in mean spread across frozen regime groups.

**Falsification:** state differences fail in the untouched holdout or disappear after multiple-testing correction.

### H-B1 — Jump-risk premium

**Null:** option-implied tail/jump component is consistent with subsequently observed jump variation.

**Alternative:** a persistent residual exists after controlling for overall volatility level, maturity and moneyness.

**Primary statistic:** implied-vs-realized jump residual with robust confidence interval.

**Falsification:** residual is unstable across periods, explained by controls, or disappears in holdout.

### H-C1 — Surface-shape predictability

**Null:** standardized SABR/surface-shape parameters have no out-of-sample predictive information beyond level and spot-return controls.

**Alternative:** at least one preregistered surface-shape feature predicts subsequent change in the same feature or market-neutral relative-value return.

**Falsification:** no incremental predictive information in holdout or after multiplicity adjustment.

### H-D1 — Regime-conditioned efficiency

**Null:** dependence/regime labels do not change the distribution of subsequent strategy returns after controls.

**Alternative:** frozen, train-only regime labels identify materially different subsequent return distributions.

**Falsification:** conditional differences disappear under CPCV and untouched holdout.

## Required option-data fields

### Contract identity

- symbol
- instrument type
- trade date
- expiry
- strike
- option type
- market lot

### EOD market data

- open
- high
- low
- close
- LTP
- settlement
- traded quantity
- premium turnover
- open interest
- change in open interest
- underlying value

NSE's historical contract-wise data documents these categories, including premium turnover for options. citeturn0search3

### External inputs

- point-in-time underlying/index series
- point-in-time risk-free curve
- contract specifications/lot-size history
- India VIX where used
- trading calendar/session metadata

### Execution layer

For any executable conclusion:

- bid
- ask
- quote timestamp
- trade timestamp
- depth/size where available
- transaction costs
- slippage/impact assumptions

NSE publishes separate historical order/trade specifications for the F&O segment, making this a distinct data layer rather than something inferred from EOD contract data. citeturn0search35turn0search37

## Point-in-time rules

For every feature at time t:

1. The input must have been available by t.
2. Contract master information must use the correct historical contract definition.
3. No future settlement, expiry or revised data may enter the feature.
4. Same-session variables may only be used when the strategy decision timestamp permits them.
5. Any derived IV must record the exact option price field used.
6. Zero/invalid option prices, crossed quotes, stale quotes and impossible option values are excluded under fixed rules rather than selectively removed after seeing results.

## Multiple-testing controls

The Phase 4 discovery stage may examine a broad surface, but the formal candidate set must be frozen before performance testing.

Required controls:

- hypothesis registry with immutable IDs
- fixed primary endpoint per hypothesis
- family-wise or false-discovery control as appropriate
- Deflated Sharpe Ratio
- Probability of Backtest Overfitting
- CPCV
- untouched chronological holdout

## Promotion gates

A candidate can move from DISCOVERY to CANDIDATE only if:

- data-quality gates pass;
- PIT audit passes;
- primary statistic is prespecified;
- uncertainty interval is reported;
- effect survives relevant dependence correction;
- economic magnitude is documented.

A candidate can move to VALIDATED only after:

- realistic costs;
- CPCV;
- DSR/PBO;
- regime stress;
- parameter perturbation;
- untouched holdout;
- execution-data validation where required.

## Current data-status decision

The public NSE contract-wise EOD source is **DATA-CANDIDATE**, not yet the final execution dataset. NSE's public historical page supports contract-wise EOD retrieval, while NSE's paid historical EOD/order-trade offerings provide broader historical datasets. citeturn0search3turn0search0

Therefore:

**Phase 4A:** acquire and validate NIFTY OPTIDX EOD data.

**Phase 4B:** reconstruct implied-volatility surfaces with explicit price-field and risk-free conventions.

**Phase 4C:** test H-A1/H-A2/H-B1.

**Phase 4D:** acquire/validate quote or order-trade data before any executable strategy claim.

## Decision rule

A positive descriptive result is never sufficient for promotion. The project advances only when the complete lifecycle is satisfied:

**hypothesis → preregistration → data snapshot → PIT feature construction → baseline → formal test → leakage audit → cost model → CPCV → DSR/PBO → stress tests → untouched holdout → decision**
