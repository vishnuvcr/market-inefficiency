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

**Status:** 100% — exit gate passed on the current scaffold.

### Phase 1 — Literature and source validation
**Goal:** convert the uploaded protocol into a verified evidence base.

**Status:** 100% — exit gate passed.

Subphases:
- 1.1 Validate foundational theory sources — **complete**.
- 1.2 Validate Indian-market empirical sources — **complete with claim-level FY25–FY26 SEBI registry**.
- 1.3 Validate methodology references for Hurst/MFDFA, CPCV, DSR, PBO, SABR, MJD, and execution modelling — **complete for protocol scope**.
- 1.4 Record source quality, publication date, population, geography, and direct relevance — **complete for high-impact current claims**.
- 1.5 Mark unsupported claims as hypotheses rather than facts — **complete for current protocol registry**.
- 1.6 Map source IDs to hypotheses/experiments and perform exit review — **complete**.

**Phase 1 methodological decision:** Hurst exponent is a candidate feature, not a standalone inefficiency classifier. H != 0.5 must be evaluated against estimator uncertainty and surrogate/random-walk controls.

### Phase 2 — Data engineering and market representation
**Goal:** build leakage-safe, point-in-time datasets.

**Status: ~55% — schema/PIT controls, adapter interfaces, synthetic validation, NSE F&O EOD normalization, quality diagnostics, point-in-time contract reconciliation, snapshot-manifest tooling and Kaggle underlying/VIX ingestion are implemented; real-source acceptance remains.**

Subphases:
- 2.1 **Source inventory and acquisition plan — complete.** Official NSE/RBI sources plus the selected Kaggle research source have been identified; paid/licensed high-resolution data gaps are explicitly recorded.
- 2.2 **Adapter interfaces and normalization paths — substantially complete.** Canonical interfaces are defined, with deterministic NSE F&O EOD and Kaggle NIFTY normalization paths.
- 2.3 **Underlying OHLCV pipeline — Kaggle adapter implemented; real snapshot validation pending.**
- 2.4 **Full option-chain history — acquisition validation required.** Required fields: timestamp, underlying, expiry, strike, call/put, bid/ask, LTP, volume, OI, quote size/depth, multiplier/lot size and settlement.
- 2.5 **Contract-specification/version history — tooling implemented; real-source reconciliation pending.** Effective-date and information-availability joins are mandatory.
- 2.6 **Risk-free rate and India VIX inputs — Kaggle India VIX path implemented for descriptive research; independent source reconciliation remains pending.**
- 2.7 **Intraday/order-trade data — access decision required.** Needed for execution/microstructure work and potentially for rigorous quote-based option studies.
- 2.8 **Data-quality and point-in-time tests — synthetic CI implemented; exclusion-code diagnostics and contract as-of reconciliation are automated; real-data validation pending.**
- 2.9 **Immutable dataset snapshots and hashes — manifest generator implemented; first real Kaggle snapshot pending acquisition.**

**Kaggle boundary:** the selected Kaggle dataset is a third-party research snapshot. It can support descriptive/stylized-fact analysis of NIFTY and India VIX after hash/schema/quality validation, but it does not establish original historical exchange information availability and does not provide the required option bid/ask/depth layer.

**Phase 2 data-availability rule:** public EOD/Kaggle data can support the first layer of descriptive and stylized-fact research, but historical bid/ask/depth coverage must be independently verified before any executable option strategy is backtested.

**Exit gate:** a point-in-time data slice can be reconstructed exactly from a version identifier and all mandatory source/quality checks pass, or the source is explicitly classified as descriptive-only.

### Phase 3 — Stylized facts and inefficiency discovery
**Goal:** determine whether the market characteristics assumed by the protocol are actually present in the chosen universe.

**Status: ~60% — Phase 3.1–3.6 deterministic diagnostic scaffolds implemented; real-data evidence remains gated on validated immutable snapshots.**

Subphases:
- 3.1 **Stylized-fact baseline — scaffold complete.** Coverage, returns, tails, absolute-return autocorrelation and drawdown diagnostics.
- 3.2 **Realized volatility — scaffold complete.** Close-to-close, Parkinson, Garman–Klass and Yang–Zhang estimators with explicit sampling/annualization controls.
- 3.3 **Volatility persistence — scaffold complete.** ACF/PACF, rolling volatility, clustering diagnostics and an explicit IID reference-interval uncertainty diagnostic.
- 3.4 **Jump diagnostics — scaffold complete.** Robust standardized-return flags, bipower-variation-style excess-variation proxy and Parkinson range extension; sensitivity analysis remains required.
- 3.5 **Memory/dependence — scaffold complete.** DFA Hurst, MFDFA, shuffled-return surrogate control and moving-block bootstrap uncertainty; real-data estimator/sampling validation remains required.
- 3.6 **Descriptive regime segmentation — scaffold complete.** Transparent volatility/direction labels, transitions and run-length diagnostics; real-data/session validation remains required.
- 3.7 **Discovery report — next.** Only pre-specified, robust findings may become Phase 4 hypotheses. Only pre-specified, robust findings may become Phase 4 hypotheses.

**Phase 3 guardrail:** these diagnostics are descriptive. They do not establish tradability or permit execution backtests.

### Phase 4 — Single-hypothesis model research
**Goal:** test each mechanism independently before combining them.

Status: **complete for the current preregistered option hypotheses** — PIT IV, VRP, state dependence, jump-risk proxy and surface-shape tests were completed. The surviving evidence is descriptive/predictive rather than yet tradable.

### Phase 5 — Multimodal market prediction
**Goal:** determine whether a multimodal predictor adds useful out-of-sample information about future market behaviour.

Status: **complete for the first specification**. Direct next-day direction prediction failed to improve on baseline-like performance, while 5-session volatility-expansion classification showed the strongest useful result (holdout AUC 0.688).

### Phase 6 — Strategy translation and execution realism
**Goal:** convert validated predictive states into fixed candidate strategies without contaminating the final holdout.

Status: **candidate screen complete**. A six-rule NIFTY settlement proxy was tested with 80/10/10 chronology. The validation-selected inverse-direction candidate was not robust under CPCV and is rejected for promotion.

### Phase 7 — Statistical validation and anti-overfitting controls
**Goal:** establish whether any observed edge survives scientific scrutiny.

Status: **current candidate stress-test complete**. 28-path CPCV, CSCV-style PBO and an approximate DSR diagnostic were run on the first 90%, with the Phase 6 final 10% held untouched.

### Phase 8 — Fresh-forward validation
**Goal:** test the strongest surviving predictions on genuinely later data before any paper-trading decision.

Status: **60% — fresh-forward multimodal and underlying-only branches completed; volatility-surface dynamics passed CPCV as a predictive diagnostic.**

The full fresh-forward multimodal model achieved AUC **0.5744** for five-session volatility expansion on 87 forward observations, down from the earlier historical holdout result. None of the six fixed volatility-conditioned strategy families passed the 20-bps promotion gate. The underlying-only Phase 8B branch was also rejected.

Phase 8C found that surface-shape predictors remain robust under 28-path CPCV with a 30-day purge and 5-day embargo; 30D downside skew had median OOS R² **0.3166** and was positive on 100% of paths. This is predictive surface evolution, not executable P&L.

### Phase 8 exit decision
The fresh-forward tests are complete. No strategy is promoted. The price/volatility-only branch and the frozen multimodal volatility-state strategy families failed their forward/promotion gates. Phase 8C retained the surface-dynamics signal as a predictive diagnostic only.

### Next gate — execution-grade surface-relative-value validation
Use historical bid/ask/order/trade information, leg synchronization, depth, margin and realistic transaction costs to determine whether the robust surface-dynamics signal can become an executable option strategy. No paper-trading promotion should occur before this gate passes.

### Phase 9A — Execution-grade surface-relative-value validation
**Goal:** convert the surviving surface-dynamics signal into executable, market-neutral option strategies using historical bid/ask/order-trade information and realistic costs.

Status: **protocol frozen; execution-data acquisition gate remains open.**

The full protocol is in docs/PHASE9A_EXECUTION_PROTOCOL.md. The candidate library remains broad by design. EOD settlement is not treated as historical bid/ask or executable fill data.

### Phase 9B — Frozen surface-signal settlement-proxy validation
**Goal:** test one mechanism-first, pre-specified translation of the strongest frozen surface predictor into a reproducible NIFTY option structure before spending effort on quote-level execution modelling.

Status: **completed; rejected for promotion.**

The tested rule used a same-expiry approximately 10Δ/50Δ put vertical, 45–75 days to expiry, 30-calendar-day holding period, one entry delta hedge and no overlapping positions. The model used a leakage-controlled expanding Ridge specification with the Phase 8C surface features and a 30-day future downside-skew target.

Fresh forward coverage from 2026-05-15 through 2026-09-18 contained 4 non-overlapping trades and produced -₹14,828 total settlement-proxy P&L, 25% win rate and an approximate event annualized Sharpe of -0.87. The forecast itself remained predictive of future surface change (forward R² 0.3029; correlation 0.5695), so the rejection is a monetization result rather than evidence that the surface predictor disappeared.

The reverse-sign result is retained as a negative control and cannot be promoted from the same four observations without post-hoc selection. The one-day-delay and random-entry controls also showed instability. Detailed results are in docs/PHASE9B_RESULTS.md.

**Phase 9B decision:** REJECTED for capital trading and for paper-trading promotion. The rule is retained only as a reproducible paper-monitoring specification. The next valid research step is execution-grade historical quote/order-trade validation or a separately preregistered new monetization hypothesis; the fresh 2026 forward period must not be reused to tune a replacement strategy.

### Phase 10 — Historical execution-data reconstruction
**Goal:** normalize genuine historical NIFTY option order/trade/quote information and make point-in-time executable reconstruction possible.

Status: **40% — software/schema layer implemented; external licensed data gate remains open.**

The parser supports the NSE F&O historical trim and historically relevant full record sizes, preserves raw-file hashes, performs exact jiffy conversion, and rejects unsupported layouts. No bid/ask is inferred from EOD data.

### Phase 11 — Executable surface strategy library
**Goal:** represent all preregistered market-neutral surface structures with explicit legs and deterministic exposure calculations before connecting them to historical execution fills.

Status: **85% — structure/exposure library complete; no economic selection performed.**

The library now explicitly covers skew verticals, put/call risk reversals, put and call butterflies, iron condors, ATM calendars, skew butterflies, four-leg maturity-spread surface boxes and straddle/strangles. It also exposes a deterministic first-order underlying delta-hedge quantity for structures that require hedging. Theoretical Greeks/payoffs are diagnostics only and are never treated as historical fills.

### Phase 12 — Execution simulator and cost model
**Goal:** convert normalized historical order/trade/quote state into leg-level fills, synchronization, slippage, fees, margin and impact.

Status: **80% — execution mechanics and multi-schema quote audit implemented; economic backtest remains data-blocked.**

Two public NIFTY Level-2/top-of-book fixtures (TickBytes and OptionVault) are preserved only for software validation. The simulator now enforces the declared synchronization window, rejects non-finite/zero-size/crossed quotes, executes buys at ask and sells at bid, enforces displayed-size capacity, and computes quoted cash flow. The quote audit accepts both public schemas and records rejection/duplicate/spread diagnostics.

The official NSE historical order/trade archive, or an equivalent licensed timestamped quote/order/trade dataset, remains the required economic-data gate.

### Phase 13 — Executable CPCV/PBO/DSR validation
**Goal:** test the full strategy library without post-hoc selection, using only executable fills, and retain complete path distributions.

Status: **protocol next; implementation can be completed before the economic dataset arrives.**

The preregistration will freeze the candidate set, cost grid, purge/embargo rules, selection rule, risk normalization, and promotion gates before any executable P&L is observed. The phase will not use the rejected 2026-05-15 through 2026-09-18 forward window to tune a replacement candidate.

### Phase 14 — Untouched executable forward validation
**Goal:** evaluate the frozen strategy specification once on an untouched later period.

Status: **not started; depends on Phase 13.**

### Phase 15 — Paper trading
**Goal:** prospective implementation validation before capital.

Status: **not started; only eligible after Phase 14.**

### Phase 16 — Live governance
**Goal:** monitor drift, liquidity, execution quality and retirement/revalidation triggers.

Status: **not started.**

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

## Current research decision

The broad hypothesis remains open. Phase 8 rejected the volatility-state directional families on fresh forward data. Phase 9B then showed that the strongest surviving surface-dynamics predictor still forecasts future surface shape, but the tested direct skew-vertical monetization failed its fresh-forward settlement-proxy gate. No NIFTY strategy is currently promoted to paper trading. The option-surface signal remains the main predictive research branch, with execution-grade data acquisition as the next mandatory gate.

## Current baseline decision

The uploaded research protocol is treated as the **hypothesis-generation document**, not as proof that any listed inefficiency exists in the market. Empirical statements in the protocol will be independently source-audited before being used as accepted facts.
