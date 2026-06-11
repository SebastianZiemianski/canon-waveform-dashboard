# Model 6 — Per-Nozzle SD Prediction

## Simple explanation

Imagine you have a printer with 30 chips. Each chip has 1,120 nozzles. Every nozzle shoots ink and produces a measured SD value — the actual ink density at that nozzle.

The question this model answers is:

> "If I set the printer to V=20, F_r=1.14, dt2=-900 — what SD value will each individual nozzle produce?"

To teach the model this, we take every single nozzle reading from every condition in the experiment and turn it into one row in a table:

| V | F_r | dt2 | Coverage | Color | Chip | Nozzle | SD value |
|---|---|---|---|---|---|---|---|
| 20 | 1.14 | -900 | 22 | C | 3 | 47 | 0.342 |
| 20 | 1.14 | -900 | 22 | C | 3 | 48 | 0.351 |
| ... | | | | | | | |

That gives us 6 million rows. The model learns the relationship between the left side (settings + chip + nozzle) and the right side (the actual SD value).

When you give it new settings it has never seen, it predicts what each nozzle will produce — using what it learned about how voltage, flow rate, and timing affect ink output.

---

## The surprising finding

Before building this model, the expectation was that knowing *which specific nozzle* you are asking about would matter a lot — because every nozzle is slightly different due to manufacturing.

The result was the opposite:

| What drives the prediction | Share |
|---|---|
| Waveform settings (V, F_r, dt2…) | **91.6%** |
| Chip identity (which chip) | 6.9% |
| Nozzle position (which nozzle) | 1.6% |

The waveform controls 91.6% of the SD value. The nozzle-to-nozzle manufacturing differences are real but small compared to what the waveform does. This means the model generalises well — it is learning physics, not just memorising specific nozzles.

---

## What it predicts

- **Input:** V, F_r, dt2, Color, Coverage, chip number, nozzle position
- **Output:** predicted SD value for that specific nozzle
- **R² = 0.953** on 1.2 million test readings

---

## What you can do with it

1. **Predict per-nozzle output for any tested setting** — see which nozzles will be high or low
2. **Identify outlier nozzles** — nozzles that consistently deviate from their chip mean across all settings are candidates for hardware defects
3. **Compare predicted vs actual** — run the prediction for a known setting, compare to the real measurement, see where the model is wrong

---

## Differences from the other models

| | Models 1–5 | Model 6 |
|---|---|---|
| One row = | one chip per condition | one nozzle per condition |
| Target | sd_std or sd_mean (aggregated) | individual nozzle SD value |
| Training rows | 108,000 | 6,000,000 (5% sample) |
| Chip/nozzle identity used | chip only (Model 5) | both chip and nozzle |
| Answers | best setting for a chip | what every nozzle will produce |

---

## Limitations

- Only works for these exact 30 chips and their nozzles — nozzle identity is hardware-specific
- Trained on 5% of conditions to keep memory usage manageable; full training would take significantly more time and RAM
- The 1.6% nozzle importance means the model cannot precisely distinguish nozzle 47 from nozzle 48 — it predicts the waveform-driven level well, but fine nozzle-to-nozzle differences are mostly noise
