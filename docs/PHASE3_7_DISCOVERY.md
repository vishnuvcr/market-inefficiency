# Phase 3.7 — Real-data discovery baseline

## Snapshot

- Dataset: `DS-KAGGLE-NIFTY`
- Source: Kaggle `debashis74017/nifty-50-minute-data`
- Acquisition run: GitHub Actions Acquire Kaggle NIFTY research snapshot #5
- NIFTY file SHA-256: `359a3ad605f9d47ae565270b4bbe89e140bba5244c2e17650c92f64663053429`
- India VIX file SHA-256: `bcf7345108926c09434776ff6b5aa1ff7e27d37cc1993e037bb5222bb9497030`
- NIFTY raw rows: 1,048,738
- India VIX raw rows: 1,048,338
- NIFTY raw coverage: 2015-01-09 through 2026-05-15 13:20 IST
- The final source session (2026-05-15) is incomplete and is excluded from the clean daily baseline.
- Clean daily baseline: 2,798 sessions, through 2026-05-14.

## Data-quality observations

- No duplicate raw NIFTY timestamps were detected.
- No missing NIFTY OHLC values were detected in the raw file.
- OHLC consistency checks passed for the raw NIFTY file.
- The supplied volume field is zero throughout and is therefore not used as a liquidity/execution measure.
- Historical session lengths include special/short sessions; these are retained rather than globally discarded.
- The incomplete final session is explicitly excluded from the clean daily research series.

## Phase 3 baseline observations

Using the clean daily baseline:

| Diagnostic | Observation |
|---|---:|
| Mean simple daily return | 0.0004285 |
| Daily return SD | 0.0101879 |
| Return skewness | -1.026 |
| Excess kurtosis | 15.864 |
| Absolute-return ACF(1) | 0.2767 |
| Absolute-return ACF(5) | 0.2142 |
| Maximum close-to-close drawdown | -38.22% |

The descriptive results show non-Gaussian tails and persistence in absolute returns. These are stylized facts, not evidence of a tradable inefficiency.

## Volatility baseline

The existing Phase 3.2 sessionized daily estimator comparison gives approximately:

- Close-to-close annualized volatility: 16.26%
- Parkinson: 12.86%
- Garman-Klass: 12.64%
- Yang-Zhang: 16.28%

The spread between estimators reinforces the need to keep the sampling/session convention fixed before comparing datasets or forming hypotheses.

## India VIX cross-check

Across 2,798 overlapping clean daily sessions:

- Pearson correlation between daily NIFTY return and same-session VIX close: -0.0847
- Pearson correlation between absolute NIFTY return and same-session VIX close: 0.5127
- Pearson correlation between VIX percentage change and next-session absolute NIFTY return: 0.0345

Conditional on contemporaneous VIX terciles, mean absolute NIFTY return was approximately:

- LOW VIX: 0.4605%
- MID VIX: 0.6261%
- HIGH VIX: 1.0153%

These are exploratory associations. In particular, contemporaneous VIX is not a point-in-time predictive signal in this analysis. No option-implied-volatility surface, bid/ask quotes, or execution costs are included.

## Research interpretation

### Candidate observations to carry forward

1. **Volatility clustering / persistence** — strong enough to justify formal modelling, but not itself an inefficiency claim.
2. **Tail behaviour / jump candidates** — worth formal jump testing under fixed sampling and robust inference.
3. **VIX–realized-volatility relationship** — useful for the later VRP track, where implied volatility must be compared with point-in-time realized volatility.
4. **Regime dependence** — suitable for later train-only HMM/GMM and conditional strategy tests.

### Explicitly not established

This Phase 3 baseline does **not** establish:

- volatility risk-premium mispricing;
- jump-risk mispricing;
- option-market inefficiency;
- predictive profitability;
- executable trading alpha.

Those require option data, point-in-time availability controls, realistic transaction costs, multiple-testing correction, CPCV, DSR/PBO, and untouched out-of-sample validation.

## Gate status

**Phase 3.7 = DISCOVERY / BASELINE only.**

Next research gate: formalize preregistered candidate hypotheses from the descriptive evidence, then move to option EOD/quote acquisition and point-in-time validation.


## Additional verified diagnostics

The downloaded Phase 3 artifact was independently inspected after acquisition:

- DFA Hurst estimate: **0.5523**
- Moving-block bootstrap 95% CI: **0.4698–0.6185**
- Shuffled-return surrogate Hurst: **0.5311**
- MFDFA width H(-2)−H(+2): **0.04895**
- Robust jump proxy flagged **81 / 2,798 = 2.895%** of return observations at the fixed z=3 threshold.
- Bipower-variation excess-variation proxy: **0.01072**.

These values remain descriptive. In particular, the Hurst interval overlaps 0.5 and the surrogate is also above 0.5, so no standalone efficiency conclusion is warranted.
