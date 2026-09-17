# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 0 — Governance, reproducibility, and GitHub infrastructure**

Status: **IN PROGRESS**

Overall completion: **~25% of Phase 0**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟡 In progress | 25% | Complete protocol scaffold + automated validation |
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

- Confirmed the GitHub repository exists and is currently empty apart from the bootstrap commit.
- Created branch `research/v1.0-protocol`.
- Added the master research plan with 10 phases (0–9), subphases, gates, and promotion states.
- Defined the research tracks: VRP, jump-risk, SABR surface, Hurst/MFDFA, multimodal HMM/GMM, ensemble allocation, execution, and integrated portfolio.
- Established the principle that the uploaded protocol is a hypothesis-generation source, not empirical proof.
- Added the initial GitHub research architecture; automated checks are the next infrastructure task.

## Immediate next tasks

1. Add research charter and hypothesis registry.
2. Add source-audit registry, including verification of current SEBI material.
3. Add data specification and configuration.
4. Add protocol validator and GitHub Actions CI.
5. Open a draft pull request containing the Phase 0 research scaffold.

## Decision log

### D0.1 — Research governance
**Decision:** Use a staged scientific workflow with explicit promotion gates and immutable experiment IDs.

**Reason:** The protocol explicitly identifies backtest overfitting, leakage, and execution friction as major failure modes.

### D0.2 — Evidence handling
**Decision:** Claims in the uploaded protocol are not automatically treated as verified facts. They enter the repository as source-backed claims pending source audit.

### D0.3 — Deployment boundary
**Decision:** No live-trading implementation is permitted before the full statistical and execution validation gates.
