# Literature & Evidence Matrix — Phase 1

Last reviewed: 2026-09-18

## Purpose

This document records the external evidence audit for the research protocol. It distinguishes established methodological/theoretical sources from empirical claims that still require testing in Indian derivatives data.

| Area | Source | Evidence role | Repository treatment | Status |
|---|---|---|---|---|
| Adaptive Markets Hypothesis | Lo (2004), Journal of Portfolio Management / SSRN | Theoretical framework for time-varying efficiency | Motivation; does not establish tradable alpha | VERIFIED THEORY |
| India VIX | NSE India methodology | Exchange definition and construction of India VIX | Use as an observed implied-volatility context variable | VERIFIED DEFINITION |
| Volatility risk premium | Carr & Wu (2010/2015 SSRN version; related published work) | Option-implied vs realized volatility-risk framework | Candidate empirical mechanism; test by horizon/moneyness | VERIFIED FRAMEWORK |
| Jump diffusion | Merton (1976) | Original discontinuous-return option-pricing framework | Model candidate; parameter estimation must be validated | VERIFIED THEORY |
| SABR / smile risk | Hagan et al. (2002) | Original SABR smile parameterization | Calibration candidate; stability and arbitrage checks required | VERIFIED THEORY |
| Hurst / efficiency | Pernagallo (2025) | Important methodological caution | Hurst != 0.5 cannot by itself be treated as evidence of inefficiency | VERIFIED CAUTION |
| Yang-Zhang volatility | Yang & Zhang (2000) | OHLC volatility-estimation methodology | Candidate estimator; compare with Parkinson/Garman-Klass | VERIFIED METHODOLOGY |
| PBO | Bailey et al. | Backtest-overfitting methodology | Required anti-overfitting component | VERIFIED METHODOLOGY |
| DSR | Bailey & López de Prado (2014) | Selection-adjusted Sharpe inference | Required multiple-testing control | VERIFIED METHODOLOGY |
| Indian retail derivatives outcomes | SEBI FY25-FY26 studies, 20 Aug 2026 | Current primary Indian-market evidence | Use claim-level registry `docs/SOURCES_SEBI_FY25_FY26.md` | VERIFIED PRIMARY EVIDENCE |

## Key findings from Phase 1

### 1. Adaptive Markets Hypothesis

Lo's AMH provides a framework in which market efficiency can vary with competition, adaptation and changing environments. It is a theoretical framework, not empirical proof that a specific trading strategy will work. The research therefore retains AMH as motivation for regime research rather than as a performance claim.

### 2. India VIX

NSE states that India VIX is derived from NIFTY option bid/ask information and represents expected volatility over the next 30 calendar days. The methodology uses out-of-the-money NIFTY options and a forward-index procedure. This makes India VIX a suitable contextual variable for Track A, but it must not be confused with realized volatility.

### 3. Hurst exponent — important protocol correction

Recent methodological work by Pernagallo (2025) shows that estimates of H != 0.5 can occur under random-walk processes and that Hurst estimates are sensitive to estimator choice. Therefore Track D will **not** classify H > 0.5 as automatically persistent/inefficient or H < 0.5 as automatically mean-reverting/inefficient. It will require surrogate/random-walk controls, estimator comparison, confidence intervals and complementary dependence statistics.

### 4. DSR and PBO

The DSR literature explicitly addresses performance inflation caused by selection bias/multiple testing and non-normal returns. PBO/CSCV addresses the probability that an in-sample-selected strategy is overfit. The repository will therefore maintain a trial ledger rather than reporting only the best configuration.

### 5. Yang-Zhang

Yang & Zhang's estimator is designed to use open, high, low and close prices while accounting for drift and opening jumps. The research will reproduce it alongside Parkinson and Garman-Klass instead of assuming the protocol's preferred estimator is universally optimal.

### 6. Current Indian derivatives evidence — claim-level extraction

The two official SEBI FY25–FY26 studies were published on 20 August 2026. The repository now records their key statistics and provenance in `docs/SOURCES_SEBI_FY25_FY26.md`.

The extracted evidence includes participation, profitability, transaction-cost, expiry-concentration, portfolio-size and trading-behaviour findings. Important denominator distinctions are preserved: for example, 87.7% is the FY26 loss-maker share for the relevant individual-trader population, while approximately 85% refers to loss-making trader-quarter observations in the trading-behaviour study. These are not interchangeable statistics.

SEBI's official press release states that the profitability study uses data from the top 15 brokers, representing approximately 90% of individual investors in the segment, while the trading-behaviour study is primarily based on a random sample of 5,000 individual traders plus the profitability sample. These population distinctions will be carried into future analysis.

### 7. Research implication of the SEBI evidence

The SEBI findings justify making the following data dimensions first-class research variables rather than assuming a homogeneous retail population:

- options versus futures;
- option-buying versus option-selling classification where data permit;
- trading intensity relative to capital/equity portfolio;
- distance to expiry, especially 0DTE/1DTE/7DTE;
- transaction-cost burden including statutory charges;
- equity-portfolio-size strata;
- participation persistence and trader-quarter outcomes.

These observations are **context and segmentation inputs**, not evidence that any repository strategy will generate positive net expectancy.

## Phase 1 source hierarchy

1. Primary regulatory/exchange documents.
2. Original academic papers and authoritative working papers.
3. Reputable secondary literature for context only.
4. Blogs, videos and educational pages only for discovery, never as sole evidence for a high-impact empirical claim.

## Primary references reviewed

- SEBI — Study: Trading Behaviour of Individual Traders in the Equity Derivatives Segment (FY25-FY26), 20 Aug 2026.
- SEBI — Study: Profitability of Individual Traders in the Equity Derivatives Segment (FY25-FY26), 20 Aug 2026.
- SEBI — PR No.50/2026, 20 Aug 2026.
- NSE — India VIX methodology and index description.
- Lo, A.W. — The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective.
- Merton, R.C. (1976) — Option Pricing When Underlying Stock Returns Are Discontinuous.
- Hagan, P.S., Kumar, D., Lesniewski, A.S., Woodward, D.E. (2002) — Managing Smile Risk.
- Yang, D. & Zhang, Q. (2000) — Drift-Independent Volatility Estimation Based on High, Low, Open, and Close Prices.
- Bailey, D.H. & López de Prado, M. (2014) — The Deflated Sharpe Ratio.
- Bailey, D.H., Borwein, J., López de Prado, M., Zhu, Q.J. — The Probability of Backtest Overfitting.
- Pernagallo, G. (2025) — Random walks, Hurst exponent, and market efficiency.
- Carr, P. & Wu, L. — work on volatility risk and risk premia in option contracts.

## Phase 1 conclusion

The literature supports the **research mechanisms and validation methodology**, while the current SEBI evidence supplies market-participation, outcome and cost context. Neither body of evidence establishes that any specific Indian-market implementation has positive net expectancy. The strongest methodological change resulting from this audit is the downgrade of the Hurst exponent from a direct inefficiency classifier to a candidate feature requiring robust controls.

## Phase 1 gate status

**SUBSTANTIALLY PASSED — EXIT REVIEW PENDING.**

Foundational methodology and current primary Indian regulatory sources have been identified and the principal FY25–FY26 SEBI statistics are now stored at claim level. Remaining work before formal Phase 1 closure is source-ID mapping into hypothesis/experiment records, final claim-matrix review, and GitHub Actions verification.
