# Phase 8 Results — Fresh-forward volatility validation

## Full multimodal forward test

The fixed Phase 5 multimodal specification was evaluated on a genuinely later NIFTY period, 2026-05-15 through 2026-09-17, using fresh option-surface observations and fresh underlying data. The old Phase 6 final holdout was used only as historical development data.

Development sample: 1,449 observations through 2026-05-14. Fresh forward evaluation: 87 observations.

The frozen logistic regression specification (C=0.5) produced fresh-forward five-session volatility-expansion AUC **0.5744**, versus the earlier Phase 5 holdout AUC around 0.688. No forward tuning was performed.

At 20 bps per side, none of the six preregistered strategy families passed the promotion gate.

Selected diagnostics:
- high-volatility trend: mean daily net -0.0313%, Sharpe -1.35
- high-volatility mean reversion: mean daily net -0.0503%, Sharpe -2.35
- high-volatility breakout: mean daily net +0.00142%, Sharpe +0.16
- low-volatility trend: mean daily net -0.1049%, Sharpe -3.08
- low-volatility mean reversion: mean daily net -0.0354%, Sharpe -1.04
- state switch: mean daily net -0.0575%, Sharpe -1.39

None passed the development CPCV plus fresh-forward 20-bps gates.

The strongest development CPCV median Sharpe among the six candidates was still negative at 20 bps; PBO proxy was approximately 0.037 for the development selection experiment, but this does not rescue any candidate because absolute performance and forward validation both failed.

## Phase 8C — volatility-surface skew CPCV

A separate CPCV test of the preregistered H-C1 surface-shape predictors was completed on the frozen Phase 4B historical IV dataset.

Across **28 CPCV paths**, using a conservative 30-calendar-day purge and 5-calendar-day embargo:

- 30D downside skew: median OOS R² **0.3166**, mean **0.3185**, positive in **100%** of paths, q10 **0.2892**
- 30D upside skew: median OOS R² **0.1068**, mean **0.0966**, positive in **89.3%** of paths
- 30–60D term slope: median OOS R² **0.1543**, mean **0.1556**, positive in **96.4%** of paths

These results strengthen the Phase 4D conclusion that the **volatility surface contains stable predictive information about subsequent surface evolution**, with downside skew the strongest and most consistent component in this test.

This still is **not evidence of a profitable option strategy**. The dependent variable is future change in implied-volatility surface shape, not executable P&L. Bid/ask, slippage, quote depth, order/trade timing, margin, and leg synchronization remain untested.

## Final Phase 8 decision

1. The historical Phase 5 multimodal volatility-expansion result does **not** generalize strongly enough on the fresh forward period to justify promotion of the tested NIFTY direction/state strategy families.
2. The price/volatility-only branch is likewise not supported.
3. The most reproducible remaining signal is **volatility-surface shape dynamics**, particularly 30D downside skew.
4. The next research gate should therefore be **execution-grade surface-relative-value validation using historical bid/ask/order-trade data**, rather than further tuning of the rejected NIFTY directional/state strategies.

### Guardrail

All reported returns are close-to-close NIFTY settlement proxies with fixed basis-point cost assumptions. No claim of live tradability or guaranteed profitability is made.
