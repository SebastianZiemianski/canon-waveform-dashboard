# Model 1 — Within-Chip Uniformity

**Notebook:** `notebooks/04-modeling/waveform-uniformity-model.ipynb`

## What it predicts

For a given waveform setting (V, F_r, dt2) and print context (Color, Coverage), the model predicts `sd_std` — the standard deviation of SD values across all 1,120 nozzles on a single chip.

A low `sd_std` means all nozzles on that chip are firing consistently. The model is trained on data averaged across all 30 chips, so the prediction reflects a general chip-level uniformity score.

## Input features

| Feature | Type | Description |
|---|---|---|
| V | Tunable | Voltage applied to nozzle |
| F_r | Tunable | Flow rate ratio |
| dt2 | Tunable | Timing parameter |
| Coverage# | Context | Ink coverage level (fixed by print job) |
| Color$ | Context | Ink color (fixed by print job) |
| V × F_r, dt2 × Coverage#, V², F_r² | Engineered | Interaction and polynomial terms |

## Target

`sd_std` — standard deviation of nozzle SD values within one chip, averaged over ~6 replicate sheets and all 30 chips.

## Data

- Source: `data/processed/waveform_tuning_row_summary.parquet`
- 620,730 raw rows → 104,340 after aggregating replicates
- Train: chips 1–24 / Test: chips 25–30

## Results

| Model | R² | MAE |
|---|---|---|
| Linear Regression | 0.576 | 0.0022 |
| Random Forest | **0.845** | 0.0012 |
| XGBoost | 0.819 | 0.0013 |

## Advantages

- **Strong predictive performance** — R²=0.845 on unseen chips, well above the 0.80 target
- **Large training set** — 104k data points gives stable, reliable predictions
- **Generalises to new hardware** — tested on chips 25–30 that were never seen during training
- **Fast to run** — processed file is only 10 MB; no heavy preprocessing needed

## Disadvantages

- **Averages over all 30 chips** — the target `sd_std` is a mean across chips, so the model cannot distinguish between a setting where all chips are uniformly good vs one where some chips are great and others are poor
- **Does not answer Canon's core question** — Canon's goal is constant SD *across* all 30 chips, not just within each one
- **Within-chip metric only** — a chip could have low within-chip variability but still differ significantly from the other 29 chips
