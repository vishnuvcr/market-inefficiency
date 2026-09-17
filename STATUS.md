# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 2 — Data engineering and market representation**

Status: **IN PROGRESS**

Overall completion: **~40% of Phase 2**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Passed CI on current protocol scaffold |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed; source registry and claim mapping complete |
| 2. Data engineering | 🟡 In progress | 40% | Real-source ingestion + data-quality acceptance |
| 3. Stylized facts | ⚪ Not started | 0% | Produce baseline market diagnostics |
| 4. Single-hypothesis research | ⚪ Not started | 0% | Run independent Track A–D experiments |
| 5. Multimodal regime model | ⚪ Not started | 0% | Build leakage-safe regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Implement net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO framework |
| 8. Paper trading | ⚪ Not started | 0% | Publish paper signals only after validation gates |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift and revalidation automation |

## Latest Phase 2 work

- Added `docs/DATA_ADAPTERS.md` defining stable interfaces for NSE cash/EOD, derivatives EOD, contract master, India VIX, RBI rates and licensed quote/trade sources.
- Added a synthetic fixture at `tests/fixtures/phase2_minimal.json` without restricted market data.
- Added `scripts/validate_phase2_fixture.py` for deterministic chronology, point-in-time, OHLC hygiene and key-uniqueness checks.
- Added the synthetic fixture check to GitHub Actions.
- Synchronized `RESEARCH_PLAN.md` with the actual Phase 2 implementation state.

## Phase 2 remains data-gated

Interface completion is not equivalent to market-data readiness. Real NSE/RBI ingestion, corporate-action reconciliation, contract-history reconciliation, representative historical option-quote validation, and immutable production snapshot creation remain outstanding.

## Decision log additions

### D2.5 — Adapter boundary
**Decision:** Source-specific ingestion is isolated behind canonical adapter interfaces. Downstream research code must consume normalized data contracts rather than source-specific formats.

### D2.6 — Synthetic CI fixtures
**Decision:** CI uses synthetic fixtures for schema/PIT testing. Restricted exchange/vendor data is never committed to the public repository.

### D2.7 — No inferred quotes
**Decision:** Last traded price, volume or open interest may not be used to manufacture historical bid/ask/depth observations.

## Immediate next tasks

1. Implement the first public-source ingestion adapter and normalization path.
2. Implement dataset-quality diagnostics with exclusion reason codes.
3. Implement contract-master as-of joins and reconciliation tests.
4. Implement immutable snapshot manifest/hash generation.
5. Validate a representative historical option quote sample and make the licensed-data decision.
6. Only after the data gate passes, begin Phase 3 stylized-fact diagnostics.
