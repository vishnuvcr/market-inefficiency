# Source Audit — Protocol Claims

## Purpose

The uploaded research protocol contains a mixture of established theory, empirical claims, implementation proposals, and market narratives. This table separates those categories so the research code does not silently convert a proposal into a fact.

| Claim area | Source in uploaded protocol | Repository treatment | Verification status |
|---|---|---|---|
| BSM assumptions and volatility smile/skew | Protocol pp.1–2 | Background theory; cite primary/academic sources in final reports | VERIFIED AS BACKGROUND |
| Adaptive Markets Hypothesis | Protocol pp.2–3 | Theoretical motivation; not treated as direct proof of tradability | VERIFIED THEORY |
| Hurst exponent and persistence | Protocol pp.2–3 | Candidate regime feature; requires estimator robustness tests | REQUIRES ROBUSTNESS |
| VRP in options | Protocol p.3 | Testable hypothesis; requires instrument- and period-specific measurement | REQUIRES EMPIRICAL TEST |
| Jump-risk premium | Protocol p.4 | Testable hypothesis; requires estimated realized jump process | REQUIRES EMPIRICAL TEST |
| SABR parameter mean reversion | Protocol p.4 | Testable hypothesis; requires calibration stability checks | REQUIRES EMPIRICAL TEST |
| HMM/GMM multimodal regimes | Protocol pp.4–5 | Proposed methodology; must beat ablations and simpler baselines | REQUIRES EMPIRICAL TEST |
| Yang-Zhang as foundational RV estimator | Protocol pp.5–6 | Candidate primary estimator; compare against alternatives | METHODOLOGY VERIFIED; COMPARISON REQUIRED |
| CPCV / purging / embargo | Protocol pp.6–7 | Required validation framework | METHODOLOGY VERIFIED; IMPLEMENTATION REQUIRED |
| DSR threshold >95% | Protocol p.7 | Initial protocol gate; sensitivity analysis required | PROTOCOL RULE, NOT UNIVERSAL LAW |
| PBO <10% | Protocol p.7 | Initial protocol gate; sensitivity analysis required | PROTOCOL RULE, NOT UNIVERSAL LAW |
| Almgren-Chriss execution | Protocol p.8 | Candidate execution model; calibrate to available market data | REQUIRES IMPLEMENTATION/CALIBRATION |
| SEBI retail-trader loss evidence | Protocol pp.8–9 | Use current primary SEBI reports in place of secondary summaries | PRIMARY SOURCES LOCATED; EXACT EXTRACTION PENDING |

## Phase 1 verified external sources

### Primary regulatory/exchange sources

1. **SEBI — Trading Behaviour of Individual Traders in the Equity Derivatives Segment (FY25–FY26)**, published 20 Aug 2026.
2. **SEBI — Profitability of Individual Traders in the Equity Derivatives Segment (FY25–FY26)**, published 20 Aug 2026.
3. **NSE — India VIX index description and computation methodology.** NSE states that India VIX is derived from NIFTY option prices and represents expected volatility over the next 30 calendar days.

### Academic/methodological sources

- Lo (2004), *The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective*.
- Merton (1976), *Option Pricing When Underlying Stock Returns Are Discontinuous*.
- Hagan et al. (2002), *Managing Smile Risk*.
- Yang & Zhang (2000), *Drift-Independent Volatility Estimation Based on High, Low, Open, and Close Prices*.
- Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*.
- Bailey, Borwein, López de Prado & Zhu, *The Probability of Backtest Overfitting*.
- Pernagallo (2025), *Random walks, Hurst exponent, and market efficiency*.
- Carr & Wu, work on volatility risk and risk premia in option contracts.

## Important methodological correction from Phase 1

The protocol describes Hurst values below/above 0.5 as mean-reverting/persistent regimes. The 2025 Pernagallo study demonstrates that estimated H != 0.5 can arise under random-walk processes and is sensitive to estimator choice. Therefore the repository will **not** treat Hurst >0.5 or Hurst <0.5 as direct evidence of inefficiency. Track D must use estimator comparison, surrogate/random-walk controls, confidence intervals and complementary dependence measures.

## Current Indian-market empirical claims

The latest primary SEBI FY25–FY26 reports have been located. Secondary reports currently reproduce figures such as approximately 87.7% loss-makers in FY26 and aggregate individual net losses around ₹91,685 crore, but these figures will be treated as provisional until extracted directly from the SEBI report and recorded with the exact population, denominator, period and definition.

The earlier official FY25 figure of approximately ₹1,05,603 crore net loss and approximately 91% loss-making individuals remains historical FY25 evidence and must not be silently relabelled as FY25–FY26.

## Source-quality rule

For any high-impact empirical claim, the repository will store:

- source URL;
- publication date;
- relevant population and period;
- exact statistic/definition;
- extraction date;
- whether the source is primary;
- material caveats;
- the research experiment(s) that rely on the claim.

## Phase 1 status

**PARTIALLY VERIFIED.** Foundational theory, methodology and primary source locations are verified. Exact extraction and claim-level mapping of the current SEBI FY25–FY26 reports remains an open Phase 1 task.
