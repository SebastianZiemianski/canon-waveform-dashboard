
## What goes into every model

Every model takes the same five inputs:

| Input | What it is |
|---|---|
| **V** (voltage) | How strong the electrical signal is that tells the nozzle to fire |
| **F_r** (flow rate) | Controls how much ink flows through the nozzle |
| **dt2** (timing) | The timing of the electrical pulse — when exactly the nozzle fires |
| **Coverage** | How much of the paper is covered with ink — low = light print, high = dark print |
| **Color** | Which ink is used — Cyan, Magenta, Yellow or Black |

V, F_r and dt2 are the settings Canon can actually tune. Coverage and Color are fixed by whatever is being printed.

---

## Model 1 — Are the nozzles on one chip firing consistently?

**What it predicts:** how much the 1,120 nozzles on a single chip differ from each other.

**Simple explanation:**  
Imagine one chip as a row of 1,120 tiny ink guns. Ideally they all fire exactly the same amount. In practice some fire a little more, some a little less. This model predicts how big that difference is for a given set of waveform settings.

**Why it is valuable:**  
If nozzles on one chip fire inconsistently, you get uneven colour density in the print — visible as streaks or banding. This model tells you which settings keep all nozzles on one chip behaving the same way.

**Result: R² = 0.845** — the model explains 85% of the variation.

---

## Model 2 — Are all 30 chips producing the same output?

**What it predicts:** how much the 30 chips differ from each other in average output.

**Simple explanation:**  
A full printhead has 30 chips. Even if every chip internally has consistent nozzles, the chips themselves might produce different amounts of ink. This model predicts how consistent all 30 chips are with each other.

**Why it is valuable:**  
This is Canon's actual goal — a printhead where all 30 chips behave the same regardless of which settings you use. If chip 5 prints darker than chip 18, the output will have visible differences across the page width.

**Result: R² = 0.998** — nearly perfect prediction.

---

## Model 3 — How much ink will one chip actually deposit?

**What it predicts:** the average Scanner Density (SD) a single chip will produce — i.e. how dark or light the ink will be.

**Simple explanation:**  
This model does not measure consistency — it measures the actual ink level. Give it a set of waveform settings and it tells you: "this chip will produce an average SD of 0.19", meaning roughly how dark the print will be.

**Why it is valuable:**  
Model 1 tells you nozzles are consistent, but consistent at what level? Model 3 fills that gap. You need both — a chip where all nozzles fire the same amount is only useful if they are also firing the right amount.

**Result: R² = 0.995** — very high because ink density is strongly driven by Coverage.

---

## Model 4 — What SD level will all 30 chips produce together?

**What it predicts:** the average Scanner Density across all 30 chips — the overall expected ink density for the full printhead.

**Simple explanation:**  
Same idea as model 3 but across all 30 chips at once. It tells you what the average ink density will be across the entire printhead for a given setting.

**Why it is valuable:**  
Using model 4 together with model 2 gives the complete answer:  
- Model 4 says "all chips will produce SD = 0.28"  
- Model 2 says "all chips will be within 0.003 of each other"  
Together: consistent output at the right density level.

**Result: R² = 0.998** — nearly perfect.

---

## The most practical feature — finding settings for a target ink density

Model 1 has a special cell (cell 9) that combines the SD and std question into one search.

**How it works:**  
You give it three things — a target ink density (e.g. sd_mean = 0.35), a tolerance (e.g. ±0.02), and a color. It then finds all settings that produce ink density close to your target, and from those returns the ones with the lowest std — the most uniform ones at that density level.

**Example:**  
"I need Cyan at roughly sd_mean = 0.35. Which V, F_r, dt2 gives me that with the most consistent nozzles?"  
→ Answer: V=20, F_r=1.26, dt2=-300, Coverage=16 — sd_mean=0.363, sd_std=0.0038

**Why this matters:**  
Without this, the model might recommend settings that are very uniform but too light or too dark for the job. This cell ensures you get both — the right darkness and the most consistent output at that level.

---

## How to use all four models together

| Question | Use |
|---|---|
| Which settings give me the most uniform nozzles on one chip? | Model 1 |
| Which settings make all 30 chips produce the same output? | Model 2 |
| What ink density will I get with these settings? | Model 3 or 4 |
| Do I get the right density AND consistent chips? | Model 2 + Model 4 together |
| I need a specific ink darkness — which settings are most uniform at that level? | Model 1 cell 9 |
