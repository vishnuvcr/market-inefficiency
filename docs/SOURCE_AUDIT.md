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
| SEBI retail-trader loss evidence | Protocol pp.8–9 | Use current primary SEBI reports and source registry | VERIFIED CURRENT PRIMARY EVIDENCE |

## Phase 1 verified external sources

### Primary regulatory/exchange sources

1. **SEBI — Trading Behaviour of Individual Traders in the Equity Derivatives Segment (FY25–FY26)**, published 20 Aug 2026. Claim-level registry: `docs/SOURCES_SEBI_FY25_FY26.md` (S2).
2. **SEBI — Profitability of Individual Traders in the Equity Derivatives Segment (FY25–FY26)**, published 20 Aug 2026. Claim-level registry: `docs/SOURCES_SEBI_FY25_FY26.md` (S1).
3. **SEBI PR No.50/2026**, published 20 Aug 2026, summarising the two studies and their study designs. Registry: `docs/SOURCES_SEBI_FY25_FY26.md` (S3).
4. **NSE — India VIX index description and computation methodology.** NSE states that India VIX is derived from NIFTY option prices and represents expected volatility over the next 30 calendar days.

### Academic/methodological sources

- Lo (2004), *The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective*.
- Merton (1976), *Option Pricing When Underlying Stock Returns Are Discontinuous*.
- Hagan et al. (2002), *Managing Smile Risk*.
- Yang & Zhang (2000), *Drift-Independent Volatility Estimation Based on High, Low, Open, and Close Prices*.
- Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*.
- Bailey, Borwein, López de Prado & Zhu, *The Probability of Backtest Overfitting*.
- Pernagallo (2025), *Random walks, Hurst exponent, and market efficiency*.
- Carr & Wu, work on volatility risk and risk premia in option contracts.

## Phase 1 exact SEBI extraction completed

The current primary SEBI evidence has now been extracted into `docs/SOURCES_SEBI_FY25_FY26.md` with source IDs, dates, populations, definitions/caveats and research uses.

Key FY26 observations recorded from the primary SEBI sources include:

- 87.7% of individual traders were loss-making in FY26; the corresponding FY25 figure in the revised comparison is 90.9%.
- FY26 aggregate net loss was ₹91,685 crore, versus a revised ₹1.12 lakh crore in FY25.
- Individual transaction costs were about ₹25,000 crore in FY26, and STT paid by individuals rose from ₹4,920 crore in FY25 to ₹6,645 crore in FY26.
- About 59% of index-options turnover occurred on 0DTE, 75% within 1DTE and 97% within 7DTE in FY26.
- Nearly 97% of traders predominantly followed option-buying strategies, while around 2% were classified as majorly options sellers in the trading-behaviour study.
- Higher trading intensity was associated with higher loss rates; this is retained as an association, not a causal claim.

The profitability report also records that gross trading P&L figures are not equivalent to net investable returns, and some population definitions differ by analysis. The repository therefore keeps the exact denominator and definition attached to each claim rather than collapsing them into a single “retail loss rate”.

## Important methodological correction from Phase 1

The protocol describes Hurst values below/above 0.5 as mean-reverting/persistent regimes. The 2025 Pernagallo study demonstrates that estimated H != 0.5 can arise under random-walk processes and is sensitive to estimator choice. Therefore the repository will **not** treat Hurst >0.5 or Hurst <0.5 as direct evidence of inefficiency. Track D must use estimator comparison, surrogate/random-walk controls, confidence intervals and complementary dependence measures.

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

**SUBSTANTIALLY VERIFIED; EXIT REVIEW PENDING.** Foundational theory, methodology and current primary Indian evidence have been source-audited and the major SEBI claims are now recorded at claim level. Remaining Phase 1 work is to map source IDs into hypothesis/experiment records, complete the broader claim matrix, and verify the GitHub Actions gate on the latest branch commit.
