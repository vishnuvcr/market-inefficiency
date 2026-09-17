# Hypothesis Registry v1.0

The hypotheses below are derived from the uploaded research protocol and are deliberately phrased as testable statements rather than accepted facts.

| ID | Track | Testable hypothesis | Primary outcome | Key falsification condition |
|---|---|---|---|---|
| H-A1 | VRP | Option-implied risk exceeds subsequent realized risk often enough, after costs, to support a defined short-volatility structure during identifiable conditions. | Net risk-adjusted return and drawdown-adjusted return | Effect disappears after costs, regime conditioning, or holdout |
| H-A2 | VRP | VRP magnitude varies systematically by volatility/regime state. | Conditional VRP spread | No stable conditional difference out of sample |
| H-B1 | Jump risk | Tail-option implied jump intensity differs systematically from realized jump intensity. | Implied-vs-realized jump spread | Difference is unstable or fully explained by costs/liquidity |
| H-B2 | Jump risk | Relative-value tail structures can monetize mispricing while maintaining bounded or controlled tail exposure. | Net expectancy and tail loss metrics | Edge depends on rare unhedged events or vanishes under realistic fills |
| H-C1 | SABR | Calibrated surface parameters exhibit local persistence/mean reversion beyond estimation noise. | Parameter forecast error / persistence | No out-of-sample predictability |
| H-C2 | SABR | Relative-value spreads based on surface-shape deviations can mean-revert after controlling for spot and volatility level. | Market-neutral residual return | Returns are explained by directional/volatility beta |
| H-D1 | Efficiency | Measures of dependence such as Hurst/MFDFA vary through time and are distinguishable from estimator noise. | Stability and regime classification statistics | No stable regimes after robust estimation |
| H-D2 | Efficiency | Strategy families have conditional performance differences across empirically identifiable regimes. | Out-of-sample conditional performance | Strategy selection fails after regime labels are frozen ex ante |
| H-E1 | Regime | Multimodal market information contains incremental information about latent market state beyond single-modality features. | Predictive/stability gain vs ablations | Incremental value disappears in holdout |
| H-E2 | Regime | Regime-aware allocation improves robustness versus fixed allocation. | Net risk-adjusted distribution | No consistent improvement across CPCV paths |
| H-F1 | Portfolio | Combining independently validated sub-strategies can reduce concentration and improve risk-adjusted robustness. | Tail-adjusted portfolio metrics | Diversification benefit vanishes out of sample |
| H-G1 | Execution | Explicit liquidity/impact modelling materially changes the ranking and viability of candidate strategies. | Gross-to-net degradation | No material effect or model cannot be calibrated |
| H-G2 | Execution | Impact-aware execution reduces implementation shortfall relative to naive execution assumptions. | Implementation shortfall | Improvement not reproduced in realistic simulation/paper trading |
| H-H1 | Integrated | A regime-aware portfolio built from independently validated tracks survives untouched holdout, multiple-testing correction, and paper trading. | Final net-of-cost evidence set | Any mandatory governance gate fails |

## Experiment design rule

A hypothesis is not promoted because a single backtest is profitable. Promotion requires agreement among:

1. economic rationale,
2. statistical evidence,
3. robustness diagnostics,
4. realistic cost assumptions,
5. out-of-sample performance,
6. multiple-testing controls,
7. execution realism.
