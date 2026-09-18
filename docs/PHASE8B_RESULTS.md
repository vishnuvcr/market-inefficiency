# Phase 8B Results — Fresh-forward underlying-only volatility test

## Purpose

Phase 8B independently tested whether the Phase 5 five-session volatility-expansion signal survives on genuinely later NIFTY data **without using fresh option data**.

This was a reduced-feature validation branch using the frozen Phase 5 **price+volatility** family and the frozen logistic-regression specification (C=0.5). The forward window was entirely after the previously consumed Phase 4/6/7 sample endpoint.

## Data

- Development: 2020-04-13 through 2026-05-14.
- Fresh forward data: 2026-05-15 through 2026-09-18.
- Fresh underlying source: NSE Indices historical index data.
- Fresh forward rows: 88.
- Clean forward evaluation rows: 87 after exclusion of the final observation without a next-day return.
- Artifact: `10571765535`
- Artifact digest: `sha256:c684cd4a820948c9cc1bd912f9cf0352d220ae6ad3838c7effc5d0c8840a9ead`

## Fresh-forward prediction

The underlying-only price+volatility model produced:

- AUC: **0.5580**
- Accuracy at 0.50: **47.1%**
- Brier score: **0.2683**
- Forward volatility-expansion rate: **29.9%**

This is only modestly above random ordering and does not reproduce the much stronger multimodal Phase 5 result (AUC ~0.688).

## Strategy translation

Fixed candidates:

- high-volatility trend
- high-volatility mean reversion
- state-switch

At **20 bps/side** in the fresh forward window:

- high-volatility trend: mean daily net **-0.0180%**, Sharpe **-0.70**
- high-volatility mean reversion: mean daily net **-0.0755%**, Sharpe **-2.92**
- state-switch: mean daily net **-0.0113%**, Sharpe **-0.31**

No candidate passed the promotion gate.

## Development robustness

Twenty-basis-point development CPCV across 28 paths gave:

- high-volatility trend: median Sharpe **-2.00**, positive-path fraction **0%**
- high-volatility mean reversion: median Sharpe **-1.13**, positive-path fraction **7.1%**
- state-switch: median Sharpe **-2.53**, positive-path fraction **0%**

## Decision

**The reduced underlying-only volatility-state branch is rejected for promotion.**

The earlier Phase 5 multimodal volatility signal therefore cannot be treated as a general NIFTY price/volatility effect. Its stronger historical performance may depend materially on the option-surface information included in the multimodal model.

The next scientific test remains the full fresh-forward multimodal branch using newly acquired option surfaces. That branch must use strict point-in-time data and must not promote a strategy based on the fresh forward window.

The reported returns remain settlement-to-settlement NIFTY proxies with fixed cost sensitivities; they are not execution-grade live trading results.
