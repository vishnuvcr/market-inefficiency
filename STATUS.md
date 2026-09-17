# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 0 — Governance, reproducibility, and GitHub infrastructure**

Status: **IN PROGRESS**

Overall completion: **~70% of Phase 0**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟡 In progress | 70% | Run/verify GitHub Actions and open draft PR |
| 1. Literature/source validation | ⚪ Not started | 0% | Build source audit |
| 2. Data engineering | ⚪ Not started | 0% | Define and ingest versioned data |
| 3. Stylized facts | ⚪ Not started | 0% | Produce baseline market diagnostics |
| 4. Single-hypothesis research | ⚪ Not started | 0% | Run independent Track A–D experiments |
| 5. Multimodal regime model | ⚪ Not started | 0% | Build leakage-safe regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Implement net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO framework |
| 8. Paper trading | ⚪ Not started | 0% | Publish paper signals only after validation gates |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift and revalidation automation |

## Completed in this response

- Confirmed the GitHub repository is under `vishnuvcr/market-inefficiency` with `main` as the default branch.
- Created branch `research/v1.0-protocol`.
- Added the master research plan with 10 phases (0–9), subphases, gates, deliverables, and promotion states.
- Added a research charter defining evidence, leakage, reproducibility, and deployment rules.
- Added a hypothesis registry covering VRP, jump risk, SABR surface, efficiency regimes, multimodal regime allocation, portfolio, execution, and integrated validation.
- Added point-in-time data specifications and cost-model requirements.
- Added the validation framework covering purging, embargo, CPCV, DSR, PBO, multiple-testing accounting, parameter stability, stress tests, and an untouched holdout.
- Added a source-audit framework and flagged empirical claims for independent verification.
- Added the experiment registry and machine-readable research configuration.
- Added `scripts/validate_protocol.py` and the first GitHub Actions protocol-check workflow.
- Updated the repository README with navigation to the research controls.

## Immediate next tasks

1. Trigger and verify the GitHub Actions workflow through the draft PR.
2. Create the master GitHub issue linking the phase plan and research decisions.
3. Complete Phase 1 source verification with primary/academic references.
4. Begin Phase 2 data-source and data-schema implementation.

## Decision log

### D0.1 — Research governance
**Decision:** Use a staged scientific workflow with explicit promotion gates and immutable experiment IDs.

**Reason:** The protocol explicitly identifies backtest overfitting, leakage, and execution friction as major failure modes.

### D0.2 — Evidence handling
**Decision:** Claims in the uploaded protocol are not automatically treated as verified facts. They enter the repository as source-backed claims pending source audit.

### D0.3 — Deployment boundary
**Decision:** No live-trading implementation is permitted before the full statistical and execution validation gates.

### D0.4 — Current-market source refresh
**Decision:** Current empirical claims about Indian derivatives participation/losses must use the latest primary SEBI reports rather than secondary summaries.
