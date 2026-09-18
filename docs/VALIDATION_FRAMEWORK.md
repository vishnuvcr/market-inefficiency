# Quantitative Validation Framework v1.0

## Principle

Historical performance is treated as an estimate subject to selection bias, dependence, non-normality, and implementation error. Validation therefore has multiple independent gates.

## Gate V1 — Chronological split

Use explicitly labelled train/validation/test periods. The final holdout remains untouched until the research specification is frozen.

## Gate V2 — Purging

For labels with forward-looking horizons, remove training observations whose label windows overlap test observations.

## Gate V3 — Embargo

Apply a configurable post-test embargo to reduce leakage through temporal dependence.

## Gate V4 — CPCV

Generate multiple out-of-sample paths using combinatorial purged cross-validation. Store the complete path-level metric distribution rather than only a single aggregate Sharpe ratio.

Required outputs:

- number of paths;
- path dates;
- path return series;
- annualized return/volatility;
- Sharpe/Sortino;
- maximum drawdown;
- tail loss metrics;
- turnover;
- transaction costs;
- margin usage;
- number of trades.

## Gate V5 — Deflated Sharpe Ratio

Compute the DSR using the effective number of trials and the empirical return distribution. The repository records both the estimated Sharpe ratio and the multiple-testing-adjusted evidence.

The uploaded protocol proposes DSR > 0.95 as a promotion threshold. This is retained as a **protocol candidate threshold** and will be sensitivity-tested rather than treated as a universal statistical law.

## Gate V6 — Probability of Backtest Overfitting

Estimate PBO from the distribution of in-sample versus out-of-sample rankings. The uploaded protocol proposes PBO < 10% as a promotion threshold. This is retained as the initial protocol rule and will be stress-tested for implementation assumptions.

## Gate V7 — Multiple-testing ledger

Every search dimension is logged:

- parameter combinations;
- feature families;
- universes;
- holding periods;
- entry/exit rules;
- cost assumptions;
- model families;
- regime definitions.

The research cannot silently discard failed variants from the trial count.

## Gate V8 — Parameter stability

Perturb key parameters around the chosen configuration and test whether results degrade smoothly rather than collapsing at a narrow optimum.

## Gate V9 — Alternative specification

Repeat critical conclusions using reasonable alternatives such as:

- alternate realized-volatility estimators;
- alternative hedge frequencies;
- alternate cost assumptions;
- alternate volatility-surface interpolation;
- alternate model seeds/initializations;
- alternate regime-feature subsets.

## Gate V10 — Stress tests

Test periods and conditions with:

- high volatility;
- low liquidity;
- large overnight gaps;
- extreme skew;
- sharp directional moves;
- expiry proximity;
- data interruptions.

## Gate V11 — Untouched holdout

The final holdout is evaluated exactly once after the research configuration is frozen.

## Gate V12 — Paper trading

A statistically acceptable strategy still requires prospective paper trading to test implementation assumptions.

## Final promotion rule

No candidate may be marked `PAPER` or `VALIDATED` unless all mandatory gates are recorded in the experiment report.
