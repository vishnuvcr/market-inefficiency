# Phase 8 Protocol — Fresh-forward volatility-state strategy validation

## Objective

Test whether the strongest surviving Phase 5 signal—five-session volatility expansion—can improve strategy selection on data that did not exist in the Phase 6/7 research period.

## Fresh-forward design

The frozen historical dataset ends 2026-05-14. Phase 8 therefore creates a genuinely new forward window beginning 2026-05-15 and uses newly acquired official NSE NIFTY 50 and NSE NIFTY OPTIDX EOD data through 2026-09-18.

The old Phase 6 final holdout is not used for selection. It becomes ordinary historical development data because the model is now being evaluated on a later, previously unavailable time window.

## Frozen prediction specification

The Phase 5 multimodal feature family and logistic regression specification remain unchanged:
- price, realized-volatility, memory and option-surface features;
- median-imputation + standardization;
- logistic regression, C=0.5;
- volatility-expansion target = next-five-session realized variance greater than current prior-20-session realized variance;
- strategy probability threshold = 0.55 for high-volatility and 0.45 for low-volatility.

No threshold or model tuning is permitted using the fresh forward window.

## Fixed candidate family

1. High-volatility trend: sign of 20-session return when predicted probability >= 0.55.
2. High-volatility mean reversion: negative sign of 20-session z-score when probability >= 0.55.
3. High-volatility breakout: sign of 1-session return when probability >= 0.55 and absolute 1-session return exceeds prior-20-session daily volatility.
4. Low-volatility trend: sign of 20-session return when probability <= 0.45.
5. Low-volatility mean reversion: negative sign of 20-session z-score when probability <= 0.45.
6. State-switch: high-vol trend in predicted high-vol state, low-vol mean reversion in predicted low-vol state, cash otherwise.

No candidate is selected by inspecting the fresh forward holdout.

## Robustness gate

Development-period CPCV uses eight chronological blocks, all 2-of-8 test combinations, five-observation purge and two-observation embargo. A candidate must satisfy, at 20 bps/side:
- median CPCV Sharpe > 0;
- positive-path fraction >= 60%;
- fresh-forward Sharpe > 0;
- fresh-forward mean daily net return > 0.

This is a predeclared promotion screen, not a ranking rule.

## Execution guardrails

Returns are settlement-to-settlement NIFTY proxies. Costs are fixed sensitivity assumptions, not observed bid/ask/slippage. This phase does not establish live trading profitability. Any options execution claim still requires quote/order/trade data.
