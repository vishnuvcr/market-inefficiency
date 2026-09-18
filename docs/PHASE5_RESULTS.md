# Phase 5 — Results

Workflow validation passed on run 35398112350; artifact 10569690872 (sha256:0962d539db616c9b16ddd374fc452bb0d79684a7d3ab3520f0acbd6769392d3d).

## Broad prediction result

The multimodal feature set combined NIFTY price/return, volatility, memory/dependence proxies and frozen Phase 4B option-surface information.

Untouched chronological holdout:

- 301 observations, 2025-02-13 through 2026-05-07.
- Next-day direction AUC: 0.4584.
- Direction accuracy: 48.2%.
- 5-session return OOS R²: -0.1038.
- The settlement-based directional proxy had negative Sharpe even before assumed costs.

The result is therefore not evidence of a reliable direct next-day directional edge under this specification.

## Important positive result

The same multimodal information was substantially more informative for 5-session volatility expansion:

- holdout AUC: 0.6879;
- accuracy: 61.1%;
- Brier score: 0.2297.

This is a useful change in research direction: the data are showing more signal about future volatility state than about the sign of the next return.

This does not establish a profitable strategy. It identifies a prediction problem worth translating into strategy selection, especially volatility-sensitive strategies.

## Guardrail

The option inputs are settlement-derived and the directional trade proxy uses NIFTY close-to-close outcomes. No claim about executable options profitability is made.
