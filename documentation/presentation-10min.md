# 10-Minute Presentation — Waveform Tuning Models

---

## Slide 1 — The Problem *(1 min)*

**Title:** Finding the Best Waveform Settings for Canon Printheads

**Say:**
> Canon has printheads with 30 chips, each with 1,120 nozzles. The goal is to find the voltage (V), flow rate (F_r), and timing (dt2) settings that make all nozzles and all chips produce consistent ink output — for any color and coverage level.
>
> Testing every combination physically takes weeks. We built machine learning models that predict print quality for untested settings, so Canon can narrow down candidates before running experiments.

---

## Slide 2 — The Data *(1 min)*

**Title:** What the Data Looks Like

**Key facts to mention:**
- One row per condition (V, F_r, dt2, Color, Coverage)
- Extended-rows file: 3,600 rows, each with 30 × 1,120 nozzle measurements = 33,600 value columns
- Summary file: 108,000 rows — one row per chip per condition with pre-computed `sd_mean` and `sd_std`

**Artifact:** Show the schema table from `documentation/dataset/schema.md` or just write on the slide:

| Column | Meaning |
|---|---|
| V, F_r, dt2 | Tunable waveform parameters |
| Coverage# | Ink coverage — fixed by the print job |
| Color$ | Ink color — fixed by the print job |
| sd_mean | Average nozzle SD on one chip |
| sd_std | Nozzle variability within one chip |

---

## Slide 3 — Why Four Models *(1 min)*

**Title:** Two Questions × Two Scales

**Say:**
> To fully describe print quality we need to answer two questions: what SD level will the setting produce, and how consistently does it produce it? Each question exists at two scales — within a single chip, and across all 30 chips.

**Artifact — draw or show this table:**

| | What level? (SD) | How consistent? (std) |
|---|---|---|
| Within one chip | Model 3 — `sd_mean` | Model 1 — `sd_std` |
| Across all chips | Model 4 — `cross_chip_mean` | Model 2 — `cross_chip_std` |

> Model 2 and Model 4 together give the most complete answer for Canon's use case.

---

## Slide 4 — Model Results *(2 min)*

**Title:** Performance Comparison

**Artifact — show this table:**

| Model | Target | Algorithm | R² | Test strategy |
|---|---|---|---|---|
| 1 — Within-chip uniformity | sd_std | Random Forest | **0.845** | Chips 25–30 held out |
| 2 — Cross-chip consistency | cross_chip_std | Random Forest | 0.998* | Random 80/20 |
| 3 — Within-chip SD level | sd_mean | Random Forest | 0.995 | Chips 25–30 held out |
| 4 — Cross-chip SD level | cross_chip_mean | Random Forest | 0.998* | Random 80/20 |

*\* Random 80/20 from same experiment — likely overestimates real-world performance*

**Say:**
> Random Forest outperformed both XGBoost and Linear Regression in all four models. Model 1's R²=0.845 is the most trustworthy result because we tested it on chips the model had never seen during training.

---

## Slide 5 — Feature Importance *(1 min)*

**Title:** What Drives Print Variability?

**Artifact:** Feature importance plot from Model 1 notebook (cell after model comparison)

**Say:**
> Color and Coverage are the strongest drivers of nozzle variability. This confirms what the earlier coverage analysis found. The waveform parameters — V, F_r, dt2 — rank lower but are the only ones Canon can actually tune. Color and Coverage are determined by the print job and cannot be changed.

> This is why the models treat Color and Coverage as context filters, not as optimisation targets.

---

## Slide 6 — Finding the Best Settings *(2 min)*

**Title:** Using the Model — Target SD Search

**Artifact:** Show output of Cell 9 (target SD search) from any notebook. Example output for Color=C, Coverage=22, target SD=0.35:

```
    V     F_r     dt2   cross_chip_mean  cross_chip_std
 20.0    1.14  -900.0          0.349          0.0021
 21.0    1.10  -900.0          0.352          0.0023
 20.0    1.10  -700.0          0.351          0.0028
```

**Say:**
> Given a target ink density — for example SD = 0.35 for Cyan at Coverage 22 — the model filters all candidate settings to those that actually hit that level (within a tolerance), then ranks them by how consistent they are across all 30 chips. The top result is the recommended setting.

> This directly answers Canon's question without running a new experiment.

---

## Slide 7 — Dashboard Demo *(1 min)*

**Title:** Interactive Tool

**Artifact:** Live demo or screenshot of the Streamlit dashboard (`app.py`)

**Say:**
> We wrapped the model in a small dashboard. You select Color and Coverage, optionally set a target SD, and get back either measured data from the experiment or model predictions for untested combinations. The Measured tab is a direct data lookup — no model involved, fully reliable. The Predicted tab uses the Random Forest for combinations not yet physically tested.

> Start it with: `streamlit run app.py`

---

## Slide 8 — Limitations and Next Steps *(1 min)*

**Title:** Honest Assessment

**Limitations:**
- Models 2 and 4 were not tested on new hardware — R²=0.998 may be optimistic
- Random Forest interpolates but cannot extrapolate beyond the training value range
- Trained on one experiment with 30 chips from one batch

**Next steps:**
1. Validate on a second independent print run
2. Add input validation in the dashboard (reject out-of-range values)
3. Serve the model as an API for Canon's systems to call directly

---

## Timing Summary

| Slide | Topic | Time |
|---|---|---|
| 1 | Problem | 1 min |
| 2 | Data | 1 min |
| 3 | Why four models | 1 min |
| 4 | Results table | 2 min |
| 5 | Feature importance | 1 min |
| 6 | Target SD search | 2 min |
| 7 | Dashboard | 1 min |
| 8 | Limits + next steps | 1 min |
| **Total** | | **10 min** |
