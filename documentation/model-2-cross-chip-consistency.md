# Model 2 — Cross-Chip Consistency

**Notebook:** `notebooks/04-modeling/cross-chip-consistency-model.ipynb`

## What it predicts

For a given waveform setting (V, F_r, dt2) and print context (Color, Coverage), the model predicts `cross_chip_std` — the standard deviation of the 30 per-chip mean SD values.

A low `cross_chip_std` means all 30 chips produce the same average SD output, i.e. the waveform setting drives consistent behaviour across the entire printhead assembly. This directly answers Canon's goal.

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

`cross_chip_std` — standard deviation of the 30 per-chip mean SD values for one condition. Computed directly from individual nozzle measurements across all chips.

## Data

- Source: `data/new/extended-rows.parquet 2`
- 3,600 rows (900 conditions × 4 colors), replicates already averaged
- Train/test: 80/20 random split stratified by color

## Results

See notebook output after execution.

## Advantages

- **Directly answers Canon's question** — measures consistency across all 30 chips, not just within one
- **Uses richer source data** — per-nozzle values for all chips in one row; no information lost through averaging
- **Same tunable inputs** — V, F_r, dt2 are the actual control parameters; Color and Coverage are treated as context
- **Actionable output** — for each (Color, Coverage) scenario, gives the best V/F_r/dt2 to achieve uniform output across the full printhead

## Disadvantages

- **Much smaller dataset** — 3,600 rows vs 104,340 in model 1; less data means potentially less stable predictions
- **Random train/test split** — cannot split by chip (no HeadIdx# in rows), so generalisation to unseen hardware is not directly tested
- **Color order assumed** — rows per condition are assigned colors M, C, Y, K by position; if the source file order ever changes, color assignment would be wrong
- **Does not capture within-chip variability** — a setting could have consistent chip means but high nozzle-to-nozzle spread within each chip; the two models are complementary
