# CHAT & DECISION LOG — Market Inefficiency

**Purpose:** append-only substantive continuity log. This is the human-readable record of project requirements, decisions, corrections and conclusions from the conversation.

> This log stores actionable reasoning and decisions, not private hidden chain-of-thought.

## 2026-09-19 — User continuity instruction

User requirement:
- The repository must become the persistent source of truth across new chats.
- Before moving into any new step, inspect the GitHub repository files first.
- Every phase update, log, decision, important research conclusion and substantive chat requirement should be recorded back into the repository.
- Research methodology must remain stable; no drift into ad-hoc optimization.
- The project should explore all identified inefficiencies individually first and then in combinations before optimization.

Decision:
- `docs/PROJECT_CONTINUITY_MASTER.md` is the authoritative continuity summary.
- This file is the append-only substantive conversation/decision log.
- `STATUS.md`, `RESEARCH_PLAN.md`, relevant phase protocols/results, and current GitHub workflow state must be checked before any new research action.

## 2026-09-19 — Broad inefficiency research requirement

User requested:
- Explore all listed inefficiencies.
- Test each inefficiency alone before optimizing.
- Test combinations of inefficiencies before optimizing.
- Preserve the existing scientific research methodology.

Decision:
- Phase 14A was created and frozen.
- Standalone discovery precedes combination discovery.
- Optimization is a later phase and cannot be triggered by an attractive raw backtest.
- The rejected 2026-05-15 → 2026-09-18 period remains frozen and cannot be reused for replacement-strategy selection.

## 2026-09-19 — Phase 14A first results

Observed:
- Fixed NIFTY time-series momentum/reversal screens did not clear robustness gates.
- A short-straddle VRP screen looked strong in settlement-proxy terms.
- Additional diagnostic inspection found the 30D-IV > 20D-realized-vol condition effectively always active in that opportunity set.
- Therefore the result is interpreted as evidence for a broad short-volatility premium proxy, not proof of a successful VRP timing signal.

Decision:
- Do not optimize the VRP signal.
- Keep the broad premium hypothesis alive for a separate risk/execution study.
- The next question is incremental timing plus executable economics, not parameter tuning.

## 2026-09-19 — Phase 14A implementation corrections

Corrections made:
- cross-sectional membership acquisition retains former constituent price history to avoid survivorship bias at exit;
- historical symbol renames are handled with a PIT reverse mapping;
- cross-sectional test was hardened for duplicate NSE series and raw security identity;
- test fixtures were expanded to non-degenerate samples;
- futures basis proxy was corrected to use a market-neutral cash-and-carry style convergence calculation rather than futures-only price movement;
- futures expiry effect is explicitly labelled as a fixed discovery proxy;
- Phase 14A workflows were created and repeatedly corrected after CI validation failures.

Decision:
- A failing workflow must be repaired and re-run rather than bypassed.
- No economic result is accepted from an unverified pipeline.

## 2026-09-19 — Existing project frozen decisions carried forward

- Phase 9B skew vertical is rejected for promotion.
- Reverse-sign result from the same four-trade forward period is a negative control, not a new strategy.
- Public NIFTY Level-2 fixtures are software fixtures only.
- Historical execution data remains an external acquisition gate.
- Phase 13 remains the executable economic validation gate.
- Phase 14A does not replace Phase 13; it broadens discovery.

## 2026-09-19 — Future chat operating procedure

Before any future step:
1. Read `docs/PROJECT_CONTINUITY_MASTER.md`.
2. Read `STATUS.md` and `RESEARCH_PLAN.md`.
3. Read the relevant phase protocol/results.
4. Inspect latest GitHub workflow state and branch changes.
5. Perform the step only if it is consistent with frozen decisions.
6. Update continuity/log files before closing the step.

## 14.0 — Commit both continuity files



## 2026-09-19 — Persistent continuity system created

Repository files committed:
- `docs/PROJECT_CONTINUITY_MASTER.md`
- `docs/CHAT_DECISION_LOG.md`
- `STATUS.md` updated with the mandatory read-before-step rule.
- `RESEARCH_PLAN.md` updated with the same continuity rule.

Continuity policy now:
- The repository is the primary cross-chat project memory.
- Every substantive research step must begin by reading the continuity master, status, plan, relevant phase documents and current workflow state.
- Every substantive step must end by updating the continuity master and chat/decision log.
- No new optimization or strategy-selection work may proceed unless it is consistent with the frozen methodology recorded there.

This entry also records that the repository intentionally stores decision rationale and evidence, rather than hidden private chain-of-thought.
