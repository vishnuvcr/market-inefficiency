# Market Inefficiency Research — Master Research Plan v1.0

## Research objective

Build a reproducible research system that tests whether structural inefficiencies exist in Indian derivatives markets and whether they can survive realistic transaction costs, regime changes, multiple-testing penalties, and strict out-of-sample validation.

This repository is a **research laboratory**, not a signal-selling or performance-promise system. A hypothesis can be rejected, retained as conditional, or promoted only when its evidence meets the predefined gates in `docs/VALIDATION_FRAMEWORK.md`.

## Core research questions

1. Do option-implied risk premia systematically differ from subsequent realized risk after realistic costs?
2. Are jump-risk probabilities embedded in option prices persistently different from realized jump behavior?
3. Do volatility-surface shape parameters exhibit statistically significant, tradable mean reversion?
4. Does market dependence/regime structure vary through time, and can regime identification improve strategy selection without leakage?
5. Does a multimodal regime allocator improve robustness relative to static allocation?
6. Do observed theoretical edges survive bid/ask, slippage, latency, lot-size, margin, fees, taxes, and execution constraints?
7. Do the findings remain credible after CPCV, DSR, PBO, stress tests, and untouched holdout periods?

## Research tracks

- **Track A — Volatility Risk Premium:** implied variance/volatility versus realized variance.
- **Track B — Jump-Risk Mispricing:** Merton/Bates-style jump intensity and tail pricing.
- **Track C — Volatility Surface Arbitrage:** SABR parameter dynamics and relative-value structures.
- **Track D — Efficiency/Memory Regimes:** Hurst/MFDFA and complementary dependence statistics.
- **Track E — Multimodal Regime Model:** HMM/GMM using price, volatility, options-flow, and other admissible information.
- **Track F — Strategy Selection/Ensemble:** regime-conditional allocation across validated sub-strategies.
- **Track G — Execution and Microstructure:** spread, depth, impact, latency, and Almgren–Chriss-inspired execution simulation.
- **Track H — Integrated Portfolio:** risk-budgeted combination of only independently validated tracks.

## Phase map

### Phase 0 — Governance, reproducibility, and GitHub infrastructure
**Goal:** establish a research environment that cannot silently change the rules after observing results.

Subphases:
- 0.1 Repository architecture.
- 0.2 Hypothesis registry and immutable IDs.
- 0.3 Dataset/version registry.
- 0.4 Configuration and experiment naming conventions.
- 0.5 GitHub Actions CI and research-health checks.
- 0.6 Research decision log.

**Status:** 90% — scaffold complete; final CI verification remains.

**Exit gate:** protocol, configuration, validator, and status system pass automated checks.

### Phase 1 — Literature and source validation
**Goal:** convert the uploaded protocol into a verified evidence base.

**Status:** 45% — foundational theory/methodology and primary-source locations verified; exact current SEBI statistic extraction and claim-level mapping remain.

Subphases:
- 1.1 Validate foundational theory sources — **substantially complete**.
- 1.2 Validate Indian-market empirical sources — **primary FY25–FY26 SEBI reports located; exact extraction pending**.
- 1.3 Validate methodology references for Hurst/MFDFA, CPCV, DSR, PBO, SABR, MJD, and execution modelling — **substantially complete**.
- 1.4 Record source quality, publication date, population, geography, and direct relevance — **in progress via `docs/LITERATURE_MATRIX.md`**.
- 1.5 Mark unsupported claims as hypotheses rather than facts — **complete for current protocol registry**.

**Phase 1 methodological decision:** Hurst exponent is a candidate feature, not a standalone inefficiency classifier. H != 0.5 must be evaluated against estimator uncertainty and surrogate/random-walk controls.

**Phase 1 exit gate:** every externally asserted empirical claim used by the code or report has a traceable source entry.

### Phase 2 — Data engineering and market representation
**Goal:** build leakage-safe, point-in-time datasets.

Status: 0% — blocked until Phase 1 source/data requirements are frozen.

Subphases:
- 2.1 Underlying OHLCV and corporate-action handling.
- 2.2 Full option-chain history with strike, expiry, type, quote time, bid, ask, volume, OI, and underlying reference.
- 2.3 Contract-specification/version history.
- 2.4 Risk-free rate and volatility-index inputs.
- 2.5 Intraday data where required for realized volatility and execution studies.
- 2.6 Data quality tests: missingness, stale quotes, crossed markets, zero/negative prices, timestamp ordering, duplicate contracts.
- 2.7 Immutable dataset snapshots and hashes.

**Exit gate:** a point-in-time data slice can be reconstructed exactly from a version identifier.

### Phase 3 — Stylized facts and inefficiency discovery
**Goal:** determine whether the market characteristics assumed by the protocol are actually present in the chosen universe.

Status: 0%.

### Phase 4 — Single-hypothesis model research
**Goal:** test each mechanism independently before combining them.

Status: 0%.

### Phase 5 — Multimodal regime switching
**Goal:** determine whether a regime model adds information beyond single features.

Status: 0%.

### Phase 6 — Portfolio construction and execution realism
**Goal:** convert individual effects into implementable portfolios.

Status: 0%.

### Phase 7 — Statistical validation and anti-overfitting controls
**Goal:** establish whether any observed edge survives scientific scrutiny.

Status: 0%.

### Phase 8 — Paper-trading validation
**Goal:** compare research assumptions with live market behavior without capital risk.

Status: 0%.

### Phase 9 — Ongoing research and model governance
**Goal:** prevent research decay after initial validation.

Status: 0%.

## Mandatory experiment lifecycle

Every experiment must follow:

`hypothesis -> preregistration -> data snapshot -> feature construction -> baseline -> model -> backtest -> leakage audit -> cost model -> CPCV -> DSR/PBO -> stress tests -> untouched holdout -> decision`

No stage may be skipped because an earlier result looks attractive.

## Promotion states

- **PROPOSED:** idea recorded but untested.
- **DATA-READY:** required data and quality checks pass.
- **BASELINE:** descriptive/statistical baseline completed.
- **CANDIDATE:** preliminary evidence supports further study.
- **VALIDATED:** mandatory statistical and economic gates passed.
- **PAPER:** approved for paper trading.
- **REJECTED:** evidence does not support the hypothesis under the current specification.
- **RETIRED:** previously validated effect no longer survives monitoring.

## Deliverables

Each phase produces machine-readable outputs plus a human-readable report. Required artifacts include configuration, data version, code commit, experiment IDs, performance tables, confidence intervals, diagnostic plots, and validation summaries.

## Current baseline decision

The uploaded research protocol is treated as the **hypothesis-generation document**, not as proof that any listed inefficiency exists in the market. Empirical statements in the protocol will be independently source-audited before being used as accepted facts.
