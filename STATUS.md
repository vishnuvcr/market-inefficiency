# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 2 — Data engineering and market representation**

Status: **IN PROGRESS**

Overall completion: **~55% of Phase 2**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Passed CI on current protocol scaffold |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed; source registry and claim mapping complete |
| 2. Data engineering | 🟡 In progress | 55% | Real-source sample + data-quality acceptance |
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
- Added `scripts/validate_dataset_quality.py` with conservative diagnostics and explicit exclusion reason codes; it never silently repairs bad observations.
- Added `scripts/reconcile_contract_master.py` for point-in-time contract metadata enrichment using effective dates and metadata availability timestamps.
- Added synthetic contract-master fixtures and CI coverage for quality diagnostics plus contract reconciliation.
- Added `scripts/create_snapshot_manifest.py` and deterministic CI coverage for SHA-256/provenance snapshot manifests.
- Extended GitHub Actions to run the new Phase 2 quality, reconciliation and snapshot tests.
- Added a synthetic Phase 2 fixture and deterministic chronology, PIT, OHLC and key-uniqueness checks.
- Corrected the contract-master validator rule so effective-dated metadata uses `effective_from/effective_to` plus `available_at`, rather than an observation timestamp.

## Phase 2 remains data-gated

The research tooling is materially further along, but no real NSE dataset is yet declared `DATA-READY`. Real-source ingestion, corporate-action reconciliation, contract-history reconciliation against representative real data, historical option-quote validation, and an immutable production snapshot remain outstanding.

Synthetic CI tests demonstrate the mechanics only; they are not evidence about market behavior.

## Decision log additions

### D2.5 — Adapter boundary
**Decision:** Source-specific ingestion is isolated behind canonical adapter interfaces. Downstream research code must consume normalized data contracts rather than source-specific formats.

### D2.6 — Synthetic CI fixtures
**Decision:** CI uses synthetic fixtures for schema/PIT testing. Restricted exchange/vendor data is never committed to the public repository.

### D2.7 — No inferred quotes
**Decision:** Last traded price, volume or open interest may not be used to manufacture historical bid/ask/depth observations.

### D2.8 — Explicit availability timestamps
**Decision:** Historical source availability is never inferred from trade date. The adapter requires an explicit `available_at` value so point-in-time reconstruction cannot silently assume publication timing.

### D2.9 — Explicit exclusion reason codes
**Decision:** Quality failures are recorded with machine-readable reason codes instead of silent row deletion or automatic repair. This preserves auditability and allows exclusion sensitivity analysis later.

### D2.10 — Point-in-time contract enrichment
**Decision:** Contract metadata must match both the observation's effective-date interval and the information available by the decision timestamp. Ambiguous or missing matches are excluded rather than guessed.

### D2.11 — Immutable snapshot manifest
**Decision:** Every acquired research snapshot must have a manifest containing source/version, preprocessing version, code commit, SHA-256 and row count when determinable. Restricted datasets can remain outside the public repository while retaining reproducibility metadata.

## Immediate next tasks

1. Validate the NSE F&O adapter against a representative real historical sample.
2. Run the quality/exclusion report on that real sample and inspect every exclusion class.
3. Reconcile real observations against the contract master as-of the research decision timestamp.
4. Create the first immutable real-data snapshot manifest.
5. Validate a representative historical option quote sample and make the licensed-data decision.
6. Only after the data gate passes, begin Phase 3 stylized-fact diagnostics.
