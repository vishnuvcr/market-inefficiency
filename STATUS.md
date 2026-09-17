# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 1 — Literature and source validation**

Status: **IN PROGRESS**

Overall completion: **~45% of Phase 1**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Scaffold complete | 90% | Final CI verification before merge |
| 1. Literature/source validation | 🟡 In progress | 45% | Complete claim-level source extraction and mapping |
| 2. Data engineering | ⚪ Not started | 0% | Define and ingest versioned data |
| 3. Stylized facts | ⚪ Not started | 0% | Produce baseline market diagnostics |
| 4. Single-hypothesis research | ⚪ Not started | 0% | Run independent Track A–D experiments |
| 5. Multimodal regime model | ⚪ Not started | 0% | Build leakage-safe regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Implement net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO framework |
| 8. Paper trading | ⚪ Not started | 0% | Publish paper signals only after validation gates |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift and revalidation automation |

## Completed in this response

### Phase 1 — Literature/source validation

- Added `docs/LITERATURE_MATRIX.md`.
- Verified the existence and publication dates of the latest FY25–FY26 SEBI equity-derivatives studies dated 20 Aug 2026.
- Verified NSE's India VIX definition and methodology as an exchange-level source.
- Verified foundational methodology sources for AMH, Merton jump diffusion, SABR, Yang-Zhang volatility estimation, DSR and PBO.
- Added the 2025 Hurst-exponent methodological caution: H != 0.5 is not sufficient evidence of market inefficiency.
- Updated `docs/SOURCE_AUDIT.md` to distinguish verified theory/methodology from empirical hypotheses.
- Kept current SEBI numerical claims provisional until extracted directly from the primary reports.

### Phase 0

- Repository architecture, research plan, charter, hypothesis registry, data specification, validation framework, experiment registry, validator and GitHub Actions scaffold are in place.
- Draft PR #2 remains the integration point for the research scaffold.

## Immediate next tasks

1. Extract the exact FY25–FY26 SEBI statistics from the primary reports and map each statistic to a source entry.
2. Complete the claim-level literature/source matrix for all high-impact protocol assertions.
3. Add source citations/identifiers to the relevant hypothesis and experiment records.
4. Run/verify GitHub Actions on the latest branch commit.
5. Complete Phase 1 exit review; only then start Phase 2 data engineering.

## Decision log

### D0.1 — Research governance
**Decision:** Use a staged scientific workflow with explicit promotion gates and immutable experiment IDs.

### D0.2 — Evidence handling
**Decision:** Claims in the uploaded protocol are not automatically treated as verified facts. They enter the repository as source-backed claims pending source audit.

### D0.3 — Deployment boundary
**Decision:** No live-trading implementation is permitted before the full statistical and execution validation gates.

### D0.4 — Current-market source refresh
**Decision:** Current empirical claims about Indian derivatives participation/losses must use the latest primary SEBI reports rather than secondary summaries.

### D1.1 — Hurst methodology
**Decision:** Hurst exponent is a candidate feature, not a standalone inefficiency classifier. Any apparent deviation from 0.5 must be tested against estimator uncertainty and random-walk/surrogate controls.

### D1.2 — Source hierarchy
**Decision:** Primary regulatory/exchange and original academic sources are authoritative for high-impact claims. Secondary sources may guide discovery but cannot be the sole evidence.
