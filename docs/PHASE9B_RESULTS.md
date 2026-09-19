# Phase 9B — Surface-Skew Strategy Results

## Scope

Phase 9B tested one mechanism-first translation of the frozen volatility-surface research signal into a NIFTY option structure. The purpose was to determine whether predictive surface information survives translation into a simple market-neutral relative-value trade.

This is a settlement-price research proxy, not an execution backtest. Historical bid/ask, depth, order/trade timing and realistic leg fills were not available, so no executable P&L is claimed.

## Data

- Historical Phase 4B IV observations: 2,641,708
- Historical surface period: 2020-04-13 to 2026-05-14
- Fresh forward IV observations: 135,243
- Fresh forward period: 2026-05-15 to 2026-09-18
- Fresh option sessions validated: 88
- Fresh underlying and option acquisition completed successfully.
- The fresh option snapshot contained 3 days with no archive available and 0 days with acquisition/validation errors; those exclusions were preserved in the manifest.
- The option snapshot is explicitly classified as not execution-backtest allowed because it is EOD rather than historical bid/ask/order-trade data.

## Frozen model specification

The strategy uses a leakage-controlled expanding Ridge model with these inputs:

- down_skew_30
- up_skew_30
- term_slope_30_60
- atm_iv_30
- 20-session trailing annualized volatility
- 20-session trailing return

Target: change in 30D downside IV skew at the first surface observation at least 30 calendar days later.

Ridge penalty: alpha = 10.

Development predictions are generated only from observations whose full 30-day target window would already have been observed at the decision date. The forward coefficients are frozen at 2026-05-14 and are never refit on the forward period.

## Strategy definition

A single pre-specified structure was tested:

- Entry maturity: 45–75 calendar days, targeting approximately 60 days.
- Long-skew mapping: long approximately 10-delta put and short approximately 50-delta put, same expiry.
- Short-skew mapping: exact reverse of the same spread.
- One entry delta hedge using contemporaneous NIFTY close.
- 30-calendar-day holding period.
- No overlapping positions.
- EOD settlement used for option legs.
- No bid/ask midpoint or synthetic spread was used.

The positive-prediction direction was fixed before evaluating the fresh forward P&L. The reverse direction was retained as a negative control, not as a post-hoc alternative candidate.

## Forecast diagnostic

The signal continued to predict subsequent surface evolution in the fresh period:

| Metric | Development | Fresh forward |
|---|---:|---:|
| Forecast R² | 0.3254 | 0.3029 |
| Forecast correlation | 0.5949 | 0.5695 |

This is important: the forward failure is not evidence that the surface predictor itself disappeared. The remaining problem is monetization/execution.

## Strategy result

### Development

- Non-overlapping trades: 50
- Total settlement-proxy P&L: +₹25,638
- Mean trade P&L: +₹513
- Win rate: 54%
- Approximate event annualized Sharpe: 0.22
- 95% bootstrap CI for mean trade P&L: −₹1,299 to +₹2,392

The development result is therefore not statistically compelling on its own.

### Fresh forward: 2026-05-15 to 2026-09-18

- Non-overlapping trades: 4
- Total settlement-proxy P&L: −₹14,828
- Mean trade P&L: −₹3,707
- Win rate: 25%
- Approximate event annualized Sharpe: −0.87
- Mean P&L / entry-risk proxy: −7.9%

The four forward trades were:

| Entry | Exit | Signal | P&L proxy |
|---|---|---:|---:|
| 2026-05-15 | 2026-06-15 | Long-skew | +₹14,461 |
| 2026-06-16 | 2026-07-16 | Short-skew | −₹12,126 |
| 2026-07-17 | 2026-08-17 | Long-skew | −₹7,101 |
| 2026-08-18 | 2026-09-17 | Long-skew | −₹10,062 |

With only four trades, the forward sample is too small for a meaningful bootstrap confidence interval. The observed loss is nevertheless sufficient to fail the pre-specified promotion gate.

## Negative-control interpretation

The control results materially constrain interpretation:

- Sign-flipping the model exactly reverses the settlement-proxy P&L; on the fresh period this produces +₹14,828, but it is based on the same four observations.
- A one-day delayed signal was positive in both development and the tiny forward sample.
- Random-entry was positive in development and also happened to be positive in the tiny forward sample.

These results mean that the recent four-trade outcome cannot be used to select the opposite sign as a new strategy without creating post-hoc selection bias. The reverse mapping therefore remains a control finding, not a promoted strategy.

## Phase 9B decision

REJECT for paper trading as a validated strategy.

The evidence supports a narrower and more useful conclusion:

1. The 30D downside-skew predictor retains meaningful out-of-sample information about future surface evolution.
2. The tested same-expiry 10-delta/50-delta downside-skew vertical did not convert that information into positive fresh-forward settlement-proxy P&L.
3. The four-trade forward sample is too small to justify selecting the opposite sign, a delay, or another variant after the fact.
4. No live or executable trading claim is justified.
5. The strategy should not be capital-traded from this Phase 9B result.

## Usable current strategy specification

For research/paper-monitoring only, the frozen rule is:

Calculate the frozen 30D downside-skew prediction after each validated EOD surface update. If the prediction is positive, paper-enter the 45–75D same-expiry 10Δ-put/50Δ-put long-skew vertical and delta-hedge at entry; if negative, reverse the spread. Exit after 30 calendar days. Do not overlap positions.

This rule is useful as a reproducible paper-monitoring specification, but it is not a validated live strategy.

## Next gate

The next statistically defensible step is execution-grade validation, not tuning the four forward observations. That requires timestamped historical option quotes/order-trade data, documented quote hygiene, leg synchronization, fill assumptions, fees/taxes, margin and impact. The reverse-sign observation can be retained as a future hypothesis but must be tested in a newly frozen experiment rather than selected from this forward sample.

Artifact:
- GitHub Actions run: 35442399330
- Artifact: 10583604205
- Artifact SHA-256: sha256:99a6175cd4d5f688cc05e21d4354754f1d22267d22edacb9ebf6f8fea193a11d