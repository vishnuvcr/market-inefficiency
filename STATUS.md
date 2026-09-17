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
| 2. Data engineering | 🟡 In progress | 55% | Kaggle snapshot acquisition + real-source quality acceptance |
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
- Added `scripts/validate_dataset_quality.py` with conservative diagnostics and explicit exclusion reason codes; it never silently repairs bad observations.
- Added `scripts/reconcile_contract_master.py` for point-in-time contract metadata enrichment using effective dates and metadata availability timestamps.
- Added `scripts/create_snapshot_manifest.py` for deterministic SHA-256/provenance snapshot manifests.
- Added Kaggle source policy in `docs/KAGGLE_DATA_SOURCES.md` and registered `DS-KAGGLE-NIFTY` for NIFTY index and India VIX descriptive/stylized-fact research.
- Added `scripts/ingest_kaggle_nifty.py` with explicit Kaggle version, acquisition timestamp, snapshot hash and conservative research classification.
- Added a synthetic Kaggle-format fixture and CI adapter test.
- Extended GitHub Actions to validate the Kaggle adapter in addition to the existing Phase 2 tests.

## Kaggle data decision

The project will use Kaggle as the first external research-data source for the underlying NIFTY index and India VIX layers. The adopted source is `debashis74017/nifty-50-minute-data` (`NSE - Nifty 50 Index Minute data (2015 to 2026)`).

Kaggle data are classified as a **third-party research snapshot**, not as a direct NSE archival feed. They can support descriptive/stylized-fact analysis after local hash, schema, chronology and quality validation. They do not establish historical exchange publication timing, historical option bid/ask/depth, or a valid execution model.

The raw Kaggle files will not be committed to this public repository. The exact dataset version, acquisition timestamp, SHA-256 hashes and processing commit must be recorded in the snapshot manifest.

## Phase 2 remains data-gated

No real Kaggle/NSE dataset is yet declared `DATA-READY` because the actual source bytes have not been validated in the research runtime. Synthetic CI tests demonstrate the mechanics only; they are not evidence about market behavior.

The full derivatives research gate also remains open because historical option bid/ask/depth data are still not established.

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

### D2.12 — Kaggle research-source boundary
**Decision:** Kaggle is accepted as a practical external source for underlying/index and India-VIX descriptive research after validation. It is not treated as proof of original historical information availability and cannot satisfy the option quote/depth execution-data requirement by itself.

## Immediate next tasks

1. Acquire the exact Kaggle dataset version locally.
2. Hash the source files and run `scripts/ingest_kaggle_nifty.py`.
3. Run the quality/exclusion diagnostics and inspect every exclusion class.
4. Create the first immutable Kaggle snapshot manifest.
5. Use the validated NIFTY/VIX snapshot to start Phase 3 descriptive/stylized-fact diagnostics for the underlying/context layer.
6. In parallel, validate a representative historical option EOD/quote sample and make the licensed-data decision for Tracks A–C/G.
