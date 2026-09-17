# Experiment Registry v1.0

No formal result is considered part of the research record unless it is registered here or in a linked machine-readable experiment manifest.

| Experiment | Hypotheses | Track | Baseline | Model candidates | Validation | Status |
|---|---|---|---|---|---|---|
| MI-A-001 | H-A1 | VRP | Close-to-close RV | Yang-Zhang, Parkinson, GK comparison | Walk-forward + CPCV | PROPOSED |
| MI-A-002 | H-A2 | VRP | Unconditional VRP | Regime-conditioned VRP | CPCV + DSR/PBO | PROPOSED |
| MI-B-001 | H-B1 | Jump | Historical jump statistics | MJD / jump-intensity estimators | OOS parameter stability | PROPOSED |
| MI-B-002 | H-B2 | Jump | Simple vertical tail spread | Relative-value tail structures | Net costs + stress | PROPOSED |
| MI-C-001 | H-C1 | SABR | Static surface parameters | Rolling SABR calibration | Parameter OOS diagnostics | PROPOSED |
| MI-C-002 | H-C2 | SABR | Naive surface residual | Calendar/butterfly residual signals | CPCV + DSR/PBO | PROPOSED |
| MI-D-001 | H-D1 | Efficiency | Rolling Hurst | Hurst + MFDFA + surrogate tests | Robustness | PROPOSED |
| MI-D-002 | H-D2 | Efficiency | Static strategy | Regime-conditional strategy routing | CPCV | PROPOSED |
| MI-E-001 | H-E1 | Regime | Single-modality HMM | Multimodal HMM/GMM | Ablation + holdout | PROPOSED |
| MI-E-002 | H-E2 | Regime | Fixed-weight portfolio | Regime-aware allocator | CPCV + PBO | PROPOSED |
| MI-F-001 | H-F1 | Portfolio | Equal-weight validated tracks | Risk-budgeted portfolio | CPCV + stress | PROPOSED |
| MI-G-001 | H-G1 | Execution | Mid-price backtest | Bid/ask + liquidity + impact | Cost sensitivity | PROPOSED |
| MI-G-002 | H-G2 | Execution | Immediate execution | Impact-aware trajectory | Implementation shortfall | PROPOSED |
| MI-H-001 | H-H1 | Integrated | Best frozen validated components | Full integrated model | Untouched holdout + paper | PROPOSED |

## Experiment manifest requirements

A future machine-readable manifest must include at least:

- `experiment_id`
- `hypothesis_ids`
- `universe`
- `frequency`
- `dataset_id`
- `feature_set_id`
- `model_family`
- `parameter_grid`
- `train_period`
- `validation_period`
- `test_period`
- `embargo`
- `purge_horizon`
- `transaction_cost_model`
- `random_seed`
- `trial_count`
- `code_commit`
- `status`
