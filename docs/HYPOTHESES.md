# Hypothesis Registry v1.0

The hypotheses below are derived from the uploaded research protocol and are deliberately phrased as testable statements rather than accepted facts. The evidence-source column identifies **context/motivation only**; it does not validate the hypothesis.

| ID | Track | Testable hypothesis | Primary outcome | Key falsification condition | Evidence/context sources |
|---|---|---|---|---|---|
| H-A1 | VRP | Option-implied risk exceeds subsequent realized risk often enough, after costs, to support a defined short-volatility structure during identifiable conditions. | Net risk-adjusted return and drawdown-adjusted return | Effect disappears after costs, regime conditioning, or holdout | S1-C05, S1-C08; NSE India VIX methodology |
| H-A2 | VRP | VRP magnitude varies systematically by volatility/regime state. | Conditional VRP spread | No stable conditional difference out of sample | S1-C05; NSE India VIX methodology |
| H-B1 | Jump risk | Tail-option implied jump intensity differs systematically from realized jump intensity. | Implied-vs-realized jump spread | Difference is unstable or fully explained by costs/liquidity | None required; Merton (1976) is the theoretical model source |
| H-B2 | Jump risk | Relative-value tail structures can monetize mispricing while maintaining bounded or controlled tail exposure. | Net expectancy and tail loss metrics | Edge depends on rare unhedged events or vanishes under realistic fills | S1-C08 as expiry-risk context; Merton (1976) |
| H-C1 | SABR | Calibrated surface parameters exhibit local persistence/mean reversion beyond estimation noise. | Parameter forecast error / persistence | No out-of-sample predictability | S1-C08 as expiry-concentration context; Hagan et al. (2002) |
| H-C2 | SABR | Relative-value spreads based on surface-shape deviations can mean-revert after controlling for spot and volatility level. | Market-neutral residual return | Returns are explained by directional/volatility beta | S1-C08; Hagan et al. (2002) |
| H-D1 | Efficiency | Measures of dependence such as Hurst/MFDFA vary through time and are distinguishable from estimator noise. | Stability and regime classification statistics | No stable regimes after robust estimation | S2-C03/S2-C04 as behavioural-regime context; Pernagallo (2025) |
| H-D2 | Efficiency | Strategy families have conditional performance differences across empirically identifiable regimes. | Out-of-sample conditional performance | Strategy selection fails after regime labels are frozen ex ante | S2-C03; S2-C05 |
| H-E1 | Regime | Multimodal market information contains incremental information about latent market state beyond single-modality features. | Predictive/stability gain vs ablations | Incremental value disappears in holdout | S1-C08; S2-C03 |
| H-E2 | Regime | Regime-aware allocation improves robustness versus fixed allocation. | Net risk-adjusted distribution | No consistent improvement across CPCV paths | S2-C03; S2-C05 |
| H-F1 | Portfolio | Combining independently validated sub-strategies can reduce concentration and improve risk-adjusted robustness. | Tail-adjusted portfolio metrics | Diversification benefit vanishes out of sample | S1-C05; S1-C06 |
| H-G1 | Execution | Explicit liquidity/impact modelling materially changes the ranking and viability of candidate strategies. | Gross-to-net degradation | No material effect or model cannot be calibrated | S1-C06/S1-C07/S1-C08; S2-C03 |
| H-G2 | Execution | Impact-aware execution reduces implementation shortfall relative to naive execution assumptions. | Implementation shortfall | Improvement not reproduced in realistic simulation/paper trading | S1-C06/S1-C07/S1-C08 |
| H-H1 | Integrated | A regime-aware portfolio built from independently validated tracks survives untouched holdout, multiple-testing correction, and paper trading. | Final net-of-cost evidence set | Any mandatory governance gate fails | S1-C05/S1-C06/S2-C03; only after component validation |

## Source-ID interpretation

- `S1` = SEBI FY25–FY26 Profitability Study; detailed claims in `docs/SOURCES_SEBI_FY25_FY26.md`.
- `S2` = SEBI FY25–FY26 Trading Behaviour Study; claim-level extraction currently recorded from SEBI's official press-release summary where direct report text extraction is not yet available.
- `S3` = SEBI PR No.50/2026; primary summary of the two studies and study designs.

## Experiment design rule

A hypothesis is not promoted because a single backtest is profitable. Promotion requires agreement among:

1. economic rationale,
2. statistical evidence,
3. robustness diagnostics,
4. realistic cost assumptions,
5. out-of-sample performance,
6. multiple-testing controls,
7. execution realism.
