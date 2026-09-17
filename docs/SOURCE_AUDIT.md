# Source Audit — Protocol Claims

## Purpose

The uploaded research protocol contains a mixture of established theory, empirical claims, implementation proposals, and market narratives. This table separates those categories so the research code does not silently convert a proposal into a fact.

| Claim area | Source in uploaded protocol | Repository treatment | Verification status |
|---|---|---|---|
| BSM assumptions and volatility smile/skew | Protocol pp.1–2 | Background theory; cite primary/academic sources in final reports | Pending detailed source audit |
| Adaptive Markets Hypothesis | Protocol pp.2–3 | Theoretical motivation; not treated as direct proof of tradability | Pending source audit |
| Hurst exponent and persistence | Protocol pp.2–3 | Candidate regime feature; requires estimator robustness tests | Pending empirical replication |
| VRP in options | Protocol p.3 | Testable hypothesis; requires instrument- and period-specific measurement | Pending empirical study |
| Jump-risk premium | Protocol p.4 | Testable hypothesis; requires estimated realized jump process | Pending empirical study |
| SABR parameter mean reversion | Protocol p.4 | Testable hypothesis; requires calibration stability checks | Pending empirical study |
| HMM/GMM multimodal regimes | Protocol pp.4–5 | Proposed methodology; must beat ablations and simpler baselines | Pending empirical study |
| Yang-Zhang as foundational RV estimator | Protocol pp.5–6 | Candidate primary estimator; compare against alternatives | Pending implementation |
| CPCV / purging / embargo | Protocol pp.6–7 | Required validation framework | Methodology implementation pending |
| DSR threshold >95% | Protocol p.7 | Initial protocol gate; sensitivity analysis required | Protocol rule, not universal law |
| PBO <10% | Protocol p.7 | Initial protocol gate; sensitivity analysis required | Protocol rule, not universal law |
| Almgren-Chriss execution | Protocol p.8 | Candidate execution model; calibrate to available market data | Pending implementation |
| SEBI retail-trader loss evidence | Protocol pp.8–9 | Must use current primary SEBI reports in place of secondary summaries | Source refresh required |

## Current external source verification

SEBI's official research index lists two FY25–FY26 equity-derivatives studies dated 20 August 2026: `Study - Trading Behaviour of Individual Traders in the Equity Derivatives Segment (FY25–FY26)` and `Study - Profitability of Individual Traders in the Equity Derivatives Segment (FY25–FY26)`. These are the preferred primary sources for the protocol's retail-participation claims.

The prior official SEBI FY25 comparative study states that individual-trader net losses in the equity derivatives segment widened to ₹1,05,603 crore in FY25 and that approximately 91% of individual traders made losses. These figures should not be copied into a FY25–FY26 claim without checking the newer FY25–FY26 publications.

## Source-quality rule

For any high-impact empirical claim, the repository will store:

- source URL;
- publication date;
- relevant population and period;
- exact statistic/definition;
- extraction date;
- whether the source is primary;
- any material caveat.
