# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 2 — Data engineering and market representation**

Status: **IN PROGRESS**

Overall completion: **~45% of Phase 2**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Passed CI on current protocol scaffold |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed; source registry and claim mapping complete |
| 2. Data engineering | 🟡 In progress | 45% | Real-source sample + data-quality acceptance |
| 3. Stylized facts | ⚪ Not started | 0% | Produce baseline market diagnostics |
| 4. Single-hypothesis research | ⚪ Not started | 0% | Run independent Track A–D experiments |
| 5. Multimodal regime model | ⚪ Not started | 0% | Build leakage-safe regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Implement net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO framework |
| 8. Paper trading | ⚪ Not started | 0% | Publish paper signals only after validation gates |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift and revalidation automation |

## Latest Phase 2 work

- Added `docs/DATA_ADAPTERS.md` defining stable interfaces for NSE cash/EOD, derivatives EOD, contract master, India VIX, RBI rates and licensed quote/trade sources.
- Implemented `scripts/ingest_nse_fo_eod.py` for bounded NSE F&O EOD CSV normalization with explicit point-in-time availability and provenance hashing.
- Added `tests/fixtures/nse_fo_eod_sample.csv` and deterministic adapter tests.
- Added the NSE adapter test to GitHub Actions.
- Added a synthetic Phase 2 fixture and deterministic chronology, PIT, OHLC and key-uniqueness checks.
- Corrected the contract-master validator rule so effective-dated metadata uses `effective_from/effective_to` plus `available_at`, rather than an observation timestamp.

## Phase 2 remains data-gated

The normalization path is implemented, but no real NSE dataset is yet declared `DATA-READY`. Real-source ingestion, corporate-action reconciliation, contract-history reconciliation, representative historical option-quote validation, and immutable production snapshot creation remain outstanding.

## Decision log additions

### D2.5 — Adapter boundary
**Decision:** Source-specific ingestion is isolated behind canonical adapter interfaces. Downstream research code must consume normalized data contracts rather than source-specific formats.

### D2.6 — Synthetic CI fixtures
**Decision:** CI uses synthetic fixtures for schema/PIT testing. Restricted exchange/vendor data is never committed to the public repository.

### D2.7 — No inferred quotes
**Decision:** Last traded price, volume or open interest may not be used to manufacture historical bid/ask/depth observations.

### D2.8 — Explicit availability timestamps
**Decision:** Historical source availability is never inferred from trade date. The adapter requires an explicit `available_at` value so point-in-time reconstruction cannot silently assume publication timing.

## Immediate next tasks

1. Validate the NSE F&O adapter against a representative real historical sample.
2. Implement dataset-quality diagnostics with exclusion reason codes.
3. Implement contract-master as-of joins and reconciliation tests.
4. Implement immutable snapshot manifest/hash generation.
5. Validate a representative historical option quote sample and make the licensed-data decision.
6. Only after the data gate passes, begin Phase 3 stylized-fact diagnostics.
