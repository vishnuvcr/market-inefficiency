# Phase 13 — Executable CPCV / PBO / DSR Validation

## Objective

Evaluate the complete preregistered surface-relative-value strategy library only after genuine timestamped execution data are available. The question is:

> Does any frozen surface strategy retain positive executable risk-adjusted performance after realistic fills, costs, synchronization, liquidity limits and multiple-testing controls?

## Frozen inputs

The following cannot be tuned on the final forward sample:
- Phase 8C surface predictors: 30D downside skew, 30D upside skew, 30D–60D ATM term slope.
- Candidate structure families from Phase 11.
- Entry/exit timing convention.
- Quote synchronization tolerance.
- Base transaction-cost assumptions and stress grid.
- Purge = 30 calendar days.
- Embargo = 5 trading days.
- Candidate-selection rule.
- Capital/risk normalization convention.

The rejected 2026-05-15 through 2026-09-18 settlement-proxy period is frozen and cannot be reused to choose a replacement sign, strike geometry, holding period or structure.

## Minimum executable input

Each reconstructed trade must contain at least:

candidate, decision_time, entry_time, exit_time, contract_id, side, quantity, entry_fill, exit_fill, gross_pnl, fees, taxes, net_pnl, capital_at_risk

For multi-leg structures the event must also preserve each leg's contract identity, quote timestamp, fill timestamp, fill side, fill price, filled quantity and synchronization span.

## Hard data checks

Reject the dataset or affected trade when:
- contract identity is missing or ambiguous;
- quote is missing, zero-size, non-finite, crossed or outside the allowed staleness window;
- requested size exceeds available displayed depth unless partial-fill reconstruction is explicitly supported;
- legs cannot be synchronized under the frozen time window;
- a fill price is not supported by contemporaneous executable quotes/trades;
- PIT lot size or contract multiplier is missing;
- entry/exit timestamps are outside the intended session;
- a position overlaps another position when the strategy forbids overlap.

No settlement price may be substituted for a missing executable quote.

## Statistical validation

For each candidate and each preregistered cost level:
1. Produce trade-level and day-level net returns.
2. Run combinatorial purged cross-validation with the frozen 30-day purge and 5-trading-day embargo.
3. Preserve the full distribution of path Sharpe, mean return, drawdown and tail loss.
4. Compute PBO from the preregistered in-sample candidate-selection procedure.
5. Compute DSR using the fixed number of candidate trials and the empirical return distribution.
6. Repeat under predefined execution stresses rather than optimizing stress assumptions.
7. Keep negative controls: sign-flip, delayed signal, shuffled signal and random-entry controls.

No candidate is promoted because it is the single highest performer in one path.

## Promotion gate

A strategy can advance only if all of the following are satisfied:
- positive executable net P&L at the base cost assumption;
- positive lower confidence bound for the chosen return statistic;
- materially positive CPCV path distribution rather than one favorable split;
- no material PBO/DSR warning under the frozen trial count;
- survives predefined cost and slippage stress;
- no liquidity or synchronization defect that materially changes results;
- no contradiction from negative controls;
- remains positive on one untouched later period.

A candidate that fails any hard gate is rejected for the current specification.

## Current status

PROTOCOL FROZEN / ECONOMIC RUN BLOCKED BY HISTORICAL EXECUTION DATA.

The software layers are being completed now so that licensed execution data can be loaded without changing the research design.