# Phase 4D — Formal H-A2 / H-B1 / H-C1 Results

## Locked inputs

- Phase 4B IV artifact: run 35393747845, artifact 10567387234
- Phase 4B artifact digest: sha256:fb7a9a0dfb4917fe24188656eb5e1c1bc0ed02a68f22a2e95f1704cabeac9ff5
- Official NIFTY underlying artifact: run 35386941363, artifact 10564212363
- Underlying digest: sha256:3d1d07b9c6a295b33f110ed1b3c5ef3fb162e44b888f6eb0923fd8dbe47f45ee
- Coverage: 2020-04-13 through 2026-05-14
- IV observations used: 2,641,708 across 1,510 trade dates
- Chronological split: first 80% training/calibration, final 20% untouched holdout
- Volatility-state cut points: training-only terciles of 20-session prior realized volatility

## H-A2 — State dependence of VRP

The primary state feature is leakage-safe 20-session trailing annualized volatility. The holdout test compares 30D and 60D constant-maturity ATM implied variance minus subsequent realized variance across LOW/MID/HIGH states.

| Horizon | LOW mean | MID mean | HIGH mean | MID−LOW p | HIGH−LOW p |
|---|---:|---:|---:|---:|---:|
| 30D | 0.00742 | -0.01382 | -0.00348 | 0.00419 | 0.12249 |
| 60D | 0.00206 | -0.01025 | 0.00123 | 0.03527 | 0.91656 |

Bonferroni threshold for the four planned state contrasts is 0.0125. Therefore, only the 30D MID-vs-LOW contrast survives that correction. The HIGH-vs-LOW contrast is not significant at either horizon, and the 60D MID-vs-LOW contrast does not survive multiplicity correction.

**Interpretation:** the earlier descriptive finding of a larger VRP in the high-volatility regime does not survive as a robust monotonic high-volatility state effect in this chronological holdout. State dependence appears non-monotonic and horizon-sensitive.

## H-B1 — Jump-risk premium

Jump outcome: future 30-day squared log returns exceeding 3× the decision-day prior-20-session daily volatility.

Ex-ante tail proxy: 30D downside-wing implied variance above 30D ATM implied variance.

- Holdout n = 294
- Mean residual = -0.000696
- HAC SE = 0.001212
- 95% CI = [-0.003071, 0.001680]
- Normal-approximation p = 0.566
- OOS RMSE with tail proxy = 0.007189
- OOS RMSE using controls only = 0.007170

**Interpretation:** there is no holdout evidence that the downside-wing proxy adds incremental information about subsequent jump variance after controlling for ATM variance and trailing variance. The tail proxy slightly worsened OOS RMSE in this test.

## H-C1 — Surface-shape predictability

Target: subsequent change in 30D downside IV skew at the next observation at least 30 calendar days later.

Each surface feature is tested separately with controls for 30D ATM IV, trailing annualized volatility, and trailing 20-session return. Predictor standardization and coefficients are frozen from the training period.

| Feature | Holdout OOS R² vs training mean | Holdout coefficient p |
|---|---:|---:|
| 30D downside skew | 0.3645 | 9.71e-07 |
| 30D upside skew | 0.1095 | 0.00296 |
| 30D ATM 30→60D term slope | 0.0205 | 0.07768 |

Bonferroni threshold for the three feature coefficient checks is 0.0167. Downside skew and upside skew remain statistically distinguishable in the holdout under that correction; the term-slope coefficient does not.

**Interpretation:** surface-shape variables, especially current downside and upside skew, contain incremental out-of-sample information about subsequent skew changes in this holdout. This is predictive information about the option surface itself, not yet evidence of a profitable market-neutral trading return.

## Usable research conclusion

The formal Phase 4D holdout changes the research direction in a useful way:

1. **Aggregate VRP remains supported**, but the previously observed “high-volatility regime has the largest VRP” pattern is **not robust** under a frozen chronological holdout and multiplicity correction.
2. **The tested jump-risk proxy does not add incremental predictive power** for subsequent jump variance.
3. **Surface shape is the clearest surviving predictive signal**: downside and upside skew contain holdout information about future skew changes, while the simple 30D–60D term slope adds little.

The next research gate should therefore focus on **surface-relative-value and regime-conditioned surface dynamics**, then translate those signals into executable returns using quote/order-trade data, realistic costs, CPCV, DSR/PBO, and an untouched final holdout. No strategy profitability conclusion is justified by Phase 4D alone.

## Reproducibility

Successful validation workflow: Phase 4D run 35395984072 (run #6), job 105764794682.

Artifact:
- ID: 10567498551
- Name: phase4d-formal-diagnostics-f08ababe1ca399c8f67a7f2182cf3ab60923fe0b
- Digest: sha256:e574406bb2a47dd54d4f5c8c192c9a333c8ad14cb1020f615c5bade1eacd181c

The validation PR was temporary and is not part of the research branch history.
