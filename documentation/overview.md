# Model Overview — Presentation Reference

## The Problem We Are Solving

Canon wants to find the best waveform settings (V, F_r, dt2) for a given print job (Color, Coverage) so that all 30 chips in a printhead produce consistent and correct ink output. Running physical experiments for every possible combination is expensive and slow. The models replace some of that experimentation.

---

## The Four Models

### Model 1 — Within-Chip Uniformity
**Notebook:** `notebooks/04-modeling/waveform-uniformity-model.ipynb`

**What it does:** Predicts `sd_std` — how much the 1,120 nozzles on a single chip differ from each other. A low value means all nozzles on that chip fire consistently.

**Data:** `data/processed/waveform_tuning_row_summary.parquet` — 104,340 rows after aggregating replicates.

**Train/test split:** Chips 1–24 for training, chips 25–30 held out entirely for testing. This is a genuine generalisation test — the model never saw those chips.

**Results:**
| Model | R² |
|---|---|
| Linear Regression | 0.576 |
| XGBoost | 0.819 |
| Random Forest | **0.845** |

---

### Model 2 — Cross-Chip Consistency
**Notebook:** `notebooks/04-modeling/cross-chip-consistency-model.ipynb`

**What it does:** Predicts `cross_chip_std` — how much the 30 chips differ from each other. A low value means all chips are producing the same output. This is Canon's core question.

**Data:** `data/new/extended-rows.parquet 2` — 3,600 rows (900 conditions × 4 colors).

**Train/test split:** Random 80/20 split stratified by color. No chip-level holdout possible because the source data has one row per condition, not per chip.

**Results:** R²=0.998 (Random Forest) — suspiciously high, see limitations.

---

### Model 3 — Within-Chip SD Level
**Notebook:** `notebooks/04-modeling/within-chip-sd-model.ipynb`

**What it does:** Predicts `sd_mean` — the actual average ink density a single chip will produce, not just how variable it is. This answers "what level of SD will this setting achieve?"

**Data:** Same as Model 1.

**Results:** R²=0.995 (Random Forest).

---

### Model 4 — Cross-Chip SD Level
**Notebook:** `notebooks/04-modeling/cross-chip-sd-model.ipynb`

**What it does:** Predicts `cross_chip_mean` — the average ink density produced across all 30 chips for a given setting.

**Data:** Same as Model 2.

**Results:** R²=0.998 (Random Forest).

---

## How the Models Work Together

The full workflow for finding optimal settings:

1. Decide the target ink density (e.g. SD = 0.35) and the print context (Color, Coverage)
2. Use **Model 4** to find which settings produce `cross_chip_mean ≈ 0.35`
3. Among those candidates, use **Model 2** to pick the one with the lowest `cross_chip_std` (most consistent across chips)
4. **Model 3** and **Model 1** do the same at the individual chip level — useful for diagnosing whether a specific chip is the problem

Models 1+3 and Models 2+4 are pairs: one predicts the level (SD), one predicts the variability (std). You need both to give a complete answer.

---

## Differences Between the Models

| | Model 1 | Model 2 | Model 3 | Model 4 |
|---|---|---|---|---|
| Target | sd_std | cross_chip_std | sd_mean | cross_chip_mean |
| Answers | Nozzle uniformity within chip | Chip consistency across printhead | SD level per chip | SD level across printhead |
| Training rows | 104,340 | 3,600 | 104,340 | 3,600 |
| Test strategy | Chip holdout (chips 25–30) | Random 80/20 | Chip holdout | Random 80/20 |
| R² | 0.845 | 0.998 | 0.995 | 0.998 |
| Source file | waveform_tuning_row_summary | extended-rows | waveform_tuning_row_summary | extended-rows |

---

## Limitations

### Model 1
- Averages `sd_std` over all 30 chips, so a setting where chip 5 is terrible but the others are fine looks acceptable
- Does not tell Canon the actual SD level — only how variable nozzles are

### Model 2
- R²=0.998 comes from a random split of the same experiment — the test set shares the same hardware and print run as training. This inflates the R²
- Cannot split by chip because the source data has no `HeadIdx#` column
- Color is assigned by row position (M, C, Y, K), not by a column in the data — if the source file ever changes row order, color assignment would be wrong

### Models 3 and 4
- Predict the mean SD level, which is useful for checking whether the target density is met but not sufficient alone — you still need Models 1/2 to know how variable that level is

### All models
- Trained on one experimental run with one printhead batch. Whether the models generalise to different hardware batches is untested
- Random Forest cannot extrapolate beyond the range of values in the training data. For untested combinations of known values it interpolates; for values outside the training range it returns an unreliable estimate
- The row summary parquet was rebuilt from the extended-rows file without replicates, so Model 1's training data lost per-replicate variance. Results may differ slightly from the original

---

## What Could Be Better

- **Test on a different print run** — the most important missing step. Train on run A, test on run B. That would give honest R² numbers
- **Proper cross-validation** for Models 2 and 4 — k-fold CV would give more reliable performance estimates than a single 80/20 split
- **Hyperparameter tuning** — Random Forest was used with default settings. A grid search on `n_estimators`, `max_depth`, and `min_samples_leaf` could improve performance
- **Confidence intervals** — right now the model returns a point estimate. Knowing the uncertainty around a prediction would be more useful for Canon
- **Input validation in the dashboard** — currently if you enter a Coverage value that was never tested, the model still returns a number without warning
- **Wrapping the model as an API** — the saved `.pkl` file could be served via a simple Flask or FastAPI endpoint so Canon's systems could call it programmatically

---

## Questions Teachers Are Likely to Ask

**"Why is R²=0.998 so high — is this overfitting?"**
Model 2 uses a random 80/20 split from the same experiment, so the test set shares the same hardware and conditions as training. That makes the test too easy. The 0.998 likely overestimates real-world performance. Model 1's R²=0.845 is more trustworthy because it was tested on chips that were physically excluded from training.

**"How do you know the model works on new data?"**
For Model 1 we do — it was tested on chips 25–30 that were never in the training set. For Models 2, 3, and 4, we don't fully know yet. The next honest test would be training on one print run and testing on a completely separate one.

**"Why Random Forest and not a neural network?"**
For a dataset of this size (a few thousand to 100k rows) and with structured tabular data, tree-based models typically outperform neural networks. Neural networks need much more data to generalise. Random Forest is also interpretable through feature importance, which aligns with Canon's goal of understanding which parameters matter most.

**"What is the practical output — what does Canon actually do with this?"**
Cell 9 in each notebook takes a target SD level and returns the top 10 settings that get closest to that level while minimising variability. That is a direct actionable recommendation. The Streamlit dashboard makes this interactive without needing to open a notebook.

**"What does R² mean?"**
R²=0.845 means the model explains 84.5% of the variance in the test data. The remaining 15.5% is prediction error the model cannot account for. An R² of 1.0 would mean perfect predictions; 0.0 would mean the model is no better than always predicting the mean.

**"Why four models instead of one?"**
Because the question has two independent dimensions — level (what SD value) and variability (how consistent) — and each dimension exists at two scales — within a chip and across all chips. Each model answers one specific question. Combining them gives the full picture.

**"What would make this production-ready?"**
Three things: (1) validate on a completely different print run, (2) add input validation so out-of-range inputs are rejected rather than silently extrapolated, (3) serve the model via an API so Canon's systems can call it without opening Python.
