# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 2 — Data engineering and market representation**

Status: **IN PROGRESS**

Overall completion: **~15% of Phase 2**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Passed CI on current protocol scaffold |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed; source registry and claim mapping complete |
| 2. Data engineering | 🟡 In progress | 15% | Source acquisition + schema acceptance |
| 3. Stylized facts | ⚪ Not started | 0% | Produce baseline market diagnostics |
| 4. Single-hypothesis research | ⚪ Not started | 0% | Run independent Track A–D experiments |
| 5. Multimodal regime model | ⚪ Not started | 0% | Build leakage-safe regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Implement net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO framework |
| 8. Paper trading | ⚪ Not started | 0% | Publish paper signals only after validation gates |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift and revalidation automation |

## Completed in this response

### Phase 1 — Literature/source validation

- Added the claim-level SEBI source registry and mapped source IDs into hypotheses and experiments.
- Completed the Phase 1 exit review after GitHub Actions validation succeeded on the latest protocol commit.
- Confirmed the research repository distinguishes unique-trader loss rates, trader-quarter loss rates, product shares, transaction costs and other denominators rather than collapsing them into one statistic.
- Confirmed no SEBI association is encoded as a causal effect.

### Phase 2 — Data engineering

- Created `docs/DATA_SOURCE_REGISTRY.md`.
- Audited current official NSE public data surfaces for underlying prices, derivatives reports, contract information and India VIX.
- Identified NSE paid EOD/historical order-and-trade data as the candidate high-resolution source for execution/microstructure research.
- Identified RBI Treasury-bill/yield publications as a candidate public risk-free-rate source.
- Added a critical data-availability gate: public/current option-chain access must not be assumed to provide a complete historical quote archive suitable for rigorous VRP/SABR/execution studies.
- Defined the minimum field contract and point-in-time `available_at` rule.

### CI verification

GitHub Actions run `35278800843` on head `6d5db8a8b5d66a12ee09270e5db92ce398427c88` completed successfully. The protocol validator and artifact publication steps passed.

## Immediate next tasks

1. Build the Phase 2 source adapters/interfaces for NSE EOD, NSE contract metadata and India VIX.
2. Build the RBI rate-data adapter/proxy specification.
3. Acquire or identify a representative historical option quote dataset and test it against the full option field contract.
4. Decide whether licensed NSE historical order/trade data or a vendor dataset is required for Tracks A–C and G.
5. Create the first immutable raw-data snapshot only after schema and point-in-time tests pass.

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

### D2.1 — Data availability is a research constraint
**Decision:** No strategy will be treated as executable merely because EOD prices exist. Historical bid/ask/depth availability must be verified separately for each experiment family.

### D2.2 — Point-in-time data
**Decision:** All research features require an `available_at` timestamp and as-of contract metadata; future information leakage through revised contract definitions or quote joins is prohibited.
