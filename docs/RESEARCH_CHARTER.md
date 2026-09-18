# Research Charter

## 1. Scope

Primary market scope: Indian listed equity derivatives, with initial emphasis on liquid index options and expansion only after data quality is demonstrated.

Primary research objective: test structural-inefficiency hypotheses under realistic market and execution constraints.

## 2. Scientific principles

1. **Predefine before optimize.** Signal families, evaluation metrics, and rejection rules are recorded before large parameter searches.
2. **Chronology is sacred.** No random shuffling of time-series observations when it can leak information.
3. **Point-in-time features only.** A feature may use information that would have been available at the timestamp of the decision and nothing later.
4. **Net results matter.** Gross P&L is descriptive; net-of-cost results are the economic test.
5. **Multiple testing is real.** Search breadth is logged and incorporated into statistical evaluation.
6. **Ablation is mandatory.** Complex models must show what information actually contributes.
7. **Replication over novelty.** A result must survive alternative periods, parameter perturbations, and reasonable model variants.
8. **Negative results are first-class outputs.** Rejected hypotheses remain recorded with reasons.

## 3. Research units

Every experiment has an immutable ID such as `MI-A-001`, where the letter identifies the track and the number identifies the experiment.

Each experiment record must specify:

- Hypothesis ID.
- Economic mechanism.
- Universe.
- Frequency.
- Data snapshot/version.
- Feature timestamp rules.
- Entry/exit definition.
- Position sizing.
- Transaction-cost model.
- Validation design.
- Number of configurations tested.
- Primary metric.
- Secondary diagnostics.
- Acceptance/rejection rule.
- Code commit.

## 4. Evidence hierarchy

**Tier 1:** primary regulatory, exchange, academic, or original-model sources.

**Tier 2:** reputable secondary research that directly cites primary sources.

**Tier 3:** educational commentary and market blogs.

Tier 3 sources may guide ideas but must not be the sole support for high-impact empirical claims.

## 5. Research safety boundary

The repository may generate research signals for evaluation, but research outputs must be clearly labelled as simulated or paper-trading outputs until the deployment gate is explicitly passed.

No claim of persistent profitability is permitted solely from historical optimization.
