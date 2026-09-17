# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 1 — Literature and source validation**

Status: **IN PROGRESS — EXIT REVIEW**

Overall completion: **~80% of Phase 1**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Scaffold complete | 90% | Final CI verification before merge |
| 1. Literature/source validation | 🟢 Exit review | 80% | Source-ID mapping + CI verification |
| 2. Data engineering | ⚪ Not started | 0% | Freeze data specification after Phase 1 sign-off |
| 3. Stylized facts | ⚪ Not started | 0% | Produce baseline market diagnostics |
| 4. Single-hypothesis research | ⚪ Not started | 0% | Run independent Track A–D experiments |
| 5. Multimodal regime model | ⚪ Not started | 0% | Build leakage-safe regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Implement net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO framework |
| 8. Paper trading | ⚪ Not started | 0% | Publish paper signals only after validation gates |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift and revalidation automation |

## Completed in this response

### Phase 1 — Literature/source validation

- Created `docs/SOURCES_SEBI_FY25_FY26.md` as a claim-level primary-source registry.
- Extracted the principal FY25–FY26 SEBI profitability statistics directly from the primary SEBI report.
- Recorded the official SEBI press-release findings for the trading-behaviour study, including the study design and population caveats.
- Added explicit source IDs S1/S2/S3 and claim IDs to preserve provenance.
- Recorded important denominator distinctions, including unique-trader loss rates versus trader-quarter loss rates.
- Added transaction-cost and expiry-concentration evidence to the research context.
- Updated `docs/SOURCE_AUDIT.md` and `docs/LITERATURE_MATRIX.md` to reflect the completed extraction.
- Kept all SEBI findings as descriptive/associational context rather than evidence of strategy profitability.

### Phase 0

- Repository architecture, research plan, charter, hypothesis registry, data specification, validation framework, experiment registry, validator and GitHub Actions scaffold are in place.
- Draft PR #2 remains the integration point for the research scaffold.

## Immediate next tasks

1. Add S1/S2/S3 source IDs to the relevant hypothesis and experiment records where they are used as empirical context.
2. Run/verify GitHub Actions on the latest branch commit; CI has not yet been confirmed for the newest commit.
3. Perform the formal Phase 1 exit review against the source-coverage gate.
4. If the exit review passes, freeze the Phase 2 data specification and begin data-source engineering.
5. Do not begin strategy backtesting merely from the SEBI findings; they are context/segmentation evidence, not proof of an exploitable edge.

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

### D1.3 — SEBI provenance
**Decision:** FY25–FY26 SEBI evidence is stored at claim level with source ID, population, period and caveat metadata. Profitability-study figures are extracted from the primary report; trading-behaviour figures are attributed to SEBI's official press-release summary where direct PDF text extraction is not yet available.

### D1.4 — No causal overreach
**Decision:** Associations reported by SEBI, such as trading intensity versus loss incidence, will not be encoded as causal effects without an appropriate causal design.
