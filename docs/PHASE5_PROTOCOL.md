# Phase 5 — Broad Multimodal Market-Inefficiency Prediction Protocol

## Objective

Return to the project's original broad question: **can point-in-time market information predict future market behaviour well enough to expose a potentially exploitable inefficiency?**

This phase is deliberately not an options-only strategy test. It combines:

- NIFTY price/return and momentum features;
- volatility clustering and persistence proxies;
- memory/dependence proxies;
- frozen NIFTY option-surface information from Phase 4B.

The primary target is **next-trading-day NIFTY direction**. Secondary targets are next-5-session volatility expansion and next-5-session return.

## Leakage controls

The first 80% of the chronological sample is used for model fitting. The final 20% is an untouched holdout.

All rolling state features use observations strictly prior to the decision date. Option-surface variables are constructed from same-day EOD information and treated as available at the decision boundary. Future labels are created only after the feature matrix is frozen.

Model settings are fixed before holdout evaluation:

- logistic regression C = 0.5;
- ridge regression alpha = 10;
- directional trade thresholds = 0.55 / 0.45;
- feature families: price-only, price+volatility, and multimodal.

The multimodal family is the preregistered primary family. The other two are ablations.

## Economic interpretation

A successful predictive result is **not automatically a profitable strategy**. The first question is whether out-of-sample prediction beats simple baselines. The second is whether that prediction can produce positive returns after conservative costs. Quote/depth data are still required for execution-grade option studies.

The settlement-based trading proxy included in Phase 5 is therefore a screening diagnostic only.

## Exit criteria

Phase 5 can advance when:

1. the full multimodal model has a valid untouched holdout;
2. predictive metrics are reported against the simpler baselines;
3. cost sensitivity is reported;
4. no leakage is detected;
5. candidate signals are either promoted to strategy research or rejected for the current specification.

Negative results remain first-class outputs.
