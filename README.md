# Market Inefficiency Research Lab

A reproducible research laboratory for testing structural inefficiency hypotheses in Indian derivatives markets.

## Research governance

This repository separates **hypothesis generation**, **empirical testing**, **statistical validation**, **execution realism**, and **paper trading**. No strategy is promoted from a backtest alone.

### Start here

- [Master Research Plan](RESEARCH_PLAN.md)
- [Live Status](STATUS.md)
- [Research Charter](docs/RESEARCH_CHARTER.md)
- [Hypothesis Registry](docs/HYPOTHESES.md)
- [Data Specification](docs/DATA_SPECIFICATION.md)
- [Validation Framework](docs/VALIDATION_FRAMEWORK.md)
- [Source Audit](docs/SOURCE_AUDIT.md)
- [Data Source Registry](docs/DATA_SOURCE_REGISTRY.md)
- [Kaggle Data Sources](docs/KAGGLE_DATA_SOURCES.md)
- [Experiment Registry](docs/EXPERIMENT_REGISTRY.md)
- [Protocol Configuration](config/research_config.json)

## Research tracks

A — Volatility Risk Premium

B — Jump-Risk Mispricing

C — Volatility-Surface Relative Value

D — Efficiency/Memory Regimes

E — Multimodal HMM/GMM Regime Model

F — Portfolio/Ensemble Allocation

G — Execution and Microstructure

H — Integrated Research Portfolio

## Current status

**Phase 3 — Stylized facts and inefficiency discovery — IN PROGRESS (~30%)**

Phase 0 governance and Phase 1 source validation are complete. Phase 2 schema/PIT controls, synthetic validation, adapter interfaces, NSE F&O EOD normalization, Kaggle NIFTY/India VIX normalization, quality/exclusion tooling and immutable snapshot tooling are implemented. Phase 3.1–3.3 now have deterministic stylized-fact, realized-volatility and volatility-persistence diagnostics. The Kaggle source is classified as a third-party research snapshot suitable for descriptive research; it is not yet DATA-READY because the exact external snapshot bytes still require local acquisition, hashing and validation. Historical option quote/depth and execution research remains gated on an appropriate source.

## Evidence policy

The supplied research protocol is treated as a hypothesis-generation document. Empirical claims must be independently source-audited and market-specific before they are used as established evidence.
