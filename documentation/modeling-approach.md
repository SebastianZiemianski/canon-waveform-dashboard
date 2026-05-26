# Modeling Approach

This document covers the transition from data understanding to data preparation and modeling — CRISP-DM phases 3 and 4. It builds directly on the analysis in `experiments/coverage-analysis-findings.md` and the experimental design documented in `team/Process_description.md`.

---

## 1. Problem definition

The goal is to predict nozzle-to-nozzle uniformity from waveform parameters, so that optimal waveform configurations can be identified without exhaustive physical testing.

The target metric is `sd_std` — the standard deviation of Scanner Density values across all 1,120 active nozzles per print condition. A lower `sd_std` means the nozzles fire more consistently with each other, which directly translates to better print quality.

`sd_mean` is explicitly **not** the quality metric. It scales predictably with `Coverage#` and reflects average ink density deposited, not consistency. Comparing `sd_mean` across conditions only makes sense within the same coverage level and colour, and even then does not tell us whether the output is uniform.

---

## 2. Prediction unit — aggregating replicates

The raw dataset has 620,730 rows. Each waveform condition (`Color$`, `HeadIdx#`, `V`, `F_r`, `dt2`, `Coverage#`) is typically tested across ~6 replicate sheets. Individual rows therefore contain sheet-to-sheet printing variance on top of the underlying condition effect — variance the model cannot and should not learn to predict.

Before modeling, we aggregate to condition level:

```
group by: Color$, HeadIdx#, V, F_r, dt2, Coverage#
target:   mean(sd_std) across replicate sheets
```

This reduces the dataset to approximately 103,000 rows and gives each row a stable estimate of the true uniformity for that waveform setting. Rows with fewer than 3 replicate sheets are dropped to avoid noisy estimates.

---

## 3. Features

### 3.1 Raw features

| Feature | Type | Values | Notes |
|---------|------|--------|-------|
| `V` | float | 20, 22, 24, 26, 28, 30 | Drive voltage in volts |
| `F_r` | float | 5 per V level, range 1.02–1.379 | Flank ratio — waveform edge slope |
| `dt2` | float | −1100, −900, −700, −500, −300 | Timing offset in microseconds |
| `Coverage#` | float | 6 sampled levels per condition | Ink density index (2–31) |
| `Color$` | categorical | C, K, M, Y | One-hot encoded; colours behave differently |

`HeadIdx#` is used as a grouping variable for train/test splitting (see section 5) but not as a model input — the model should generalise across chips, not memorise chip-specific behaviour.

### 3.2 Engineered features

The coverage analysis showed that the parameter effects are non-linear and that certain pairs interact. The following interaction and polynomial terms are added:

| Feature | Motivation |
|---------|-----------|
| `V × F_r` | F_r range shifts with V in the experimental design — the two are physically coupled |
| `dt2 × Coverage#` | Timing offset and ink volume level interact in their effect on uniformity |
| `V²` | Voltage shows non-linear effects on sd_std, especially for Black (K) ink |
| `F_r²` | Flank ratio also has a non-linear, non-monotone relationship with uniformity |

---

## 4. Target variable

`sd_std` (mean across replicates per condition). Lower is better — no formal threshold has been defined yet. Beyond point-prediction accuracy, the model must correctly rank conditions: correctly identifying the parameter region with lowest sd_std is more important than minimising average prediction error.

---

## 5. Train / test split strategy

A random row-level split would leak information: replicate sheets of the same condition would end up in both train and test, making evaluation scores optimistic and not representative of real-world performance.

**Primary split — by `HeadIdx#`:**
Train on chips 1–24, test on chips 25–30. This tests whether the model generalises to unseen physical printheads, which is the realistic deployment scenario: a model trained on a subset of chips should predict uniformity for a new chip.

**Secondary split — by (V, F_r) combination:**
Hold out 5 of the 30 waveform configurations as test. This tests whether the model can extrapolate to unseen parameter combinations — a stricter evaluation relevant for recommending configurations that have not been physically tested.

---

## 6. Candidate models

| Model | Rationale |
|-------|-----------|
| Linear regression | Baseline — establishes a floor and checks whether linear approximation is sufficient |
| Polynomial regression (degree 2) | Captures the non-linear V and F_r effects identified in the analysis |
| Random Forest | Handles interactions and non-linearity automatically; feature importance gives interpretable insight into which parameters drive uniformity |
| Gradient Boosting (XGBoost / LightGBM) | Expected best performance on structured tabular data; also provides feature importance |

The approach is sequential: start with linear regression, then add complexity only if it is justified by the evaluation metrics. Neural networks are not considered — the feature set is small and structured, and interpretability matters for the Canon stakeholder.

---

## 7. Evaluation metrics

| Metric | What it tells us |
|--------|-----------------|
| R² | How much variance in sd_std the model explains — primary metric |
| MAE | Mean absolute error in the same units as sd_std — interpretable |
| Top-k ranking accuracy | Does the model correctly identify the lowest-sd_std conditions? Relevant for parameter recommendation |

A model with **R² > 0.80** on the held-out chip set would be a strong result. **R² > 0.60** is the minimum for the model to be useful for ranking parameter configurations and making recommendations.

---

## 8. Next step

Implement the aggregation and feature engineering pipeline, then train and evaluate the baseline model:

- `notebooks/04-modeling/01-data-preparation-for-modeling.ipynb` — aggregation, encoding, feature engineering
- `notebooks/04-modeling/02-baseline-and-model-comparison.ipynb` — train, evaluate, compare models
