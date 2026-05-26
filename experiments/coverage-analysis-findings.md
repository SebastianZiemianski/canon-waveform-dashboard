# Waveform Tuning — Analysis Findings

Results from `waveform_tuning_analysis.ipynb` and `coverage_analysis.ipynb`.

---

## Metric clarification: SD = Scanner Density

The `Value_000#`, `Value_001#`, … columns in the raw data are **per-nozzle Scanner Density readings** — optical density measurements of the ink deposited by each nozzle. The summary columns derived from these are:

| Column   | Meaning |
|----------|---------|
| `sd_mean` | Mean Scanner Density across all nozzles per row — represents the **average ink density** deposited |
| `sd_std`  | Standard deviation of Scanner Density across nozzles — represents **nozzle-to-nozzle variability** (the actual uniformity metric) |
| `sd_max`  | Heaviest individual nozzle per row |
| `sd_p95`  | 95th percentile nozzle density per row |

**What this means for interpretation:**
- `sd_mean` is not a quality metric on its own — a high value means more ink was deposited overall, which is expected and correct for high-coverage jobs. Comparing `sd_mean` across Coverage# levels does not make sense as a quality measure.
- `sd_std` is the relevant uniformity metric: lower `sd_std` means nozzles are firing more consistently with each other.
- The analysis notebooks currently plot `sd_mean` as the primary metric throughout. The findings below are therefore about **average ink density**, not uniformity. A separate analysis using `sd_std` would be needed for a proper uniformity assessment.

---

## Effect of Coverage# on average density (sd_mean)

As expected, sd_mean increases monotonically with Coverage# for all colours — more coverage means more ink deposited:

| Color | sd_mean at Coverage# 2 | sd_mean at Coverage# 31 | Factor |
|-------|------------------------|--------------------------|--------|
| C     | 0.120                  | 0.683                    | ~5.7×  |
| K     | 0.130                  | 0.809                    | ~6.2×  |
| M     | 0.084                  | 0.510                    | ~6.1×  |
| Y     | 0.060                  | 0.428                    | ~7.1×  |

This is a direct scaling effect — the result confirms that Coverage# controls ink volume as intended and does not indicate which setting is "better." The correct question is whether the target density is reached at the chosen coverage level with low nozzle-to-nozzle variation (sd_std).

---

## Average density by ink colour

Across all tested parameters, Y deposits the least ink on average and K the most:

| Color | Mean sd_mean |
|-------|-------------|
| Y     | 0.251       |
| M     | 0.309       |
| C     | 0.419       |
| K     | 0.480       |

This reflects ink properties (pigment concentration, optical absorption) rather than print quality. Whether these density levels are correct depends on the target densities for the specific print job.

---

## Effect of Voltage (V) on average density

Higher voltage increases average deposited density for most colours (more ink ejected per drop):

- **C and Y**: sd_mean rises steadily from V=20 to V=30
- **M**: slight non-monotone behaviour around V=22–28
- **K**: non-monotone — sd_mean is lowest at V=20 but peaks at V=24, not V=30

The non-monotone behaviour of K around V=24 is notable and could indicate a change in drop formation regime (e.g. satellite formation, partial misfiring) at that voltage.

---

## Effect of Flank Ratio (F_r) on average density

Higher F_r values generally increase deposited density. The relationship is not linear:

| Color | F_r with lowest sd_mean | F_r with highest sd_mean |
|-------|------------------------|--------------------------|
| C     | 1.14                   | 1.29                     |
| K     | 1.105                  | 1.379                    |
| M     | 1.30                   | 1.29                     |
| Y     | 1.14                   | 1.379                    |

The M result (F_r=1.30 lowest, F_r=1.29 highest) is an anomaly worth investigating — a sharp density inversion over a 0.01 step suggests a physical transition (e.g. droplet instability) at that flank ratio for magenta ink.

---

## Effect of dt2 on average density

For Color C, more negative dt2 results in slightly lower average density (~5% across the full range). The effect is modest and monotone. Similar patterns are expected for other colours.

---

---

## Nozzle-to-nozzle variability (sd_std) — uniformity analysis

### sd_std vs Coverage#: not monotone

Unlike sd_mean, nozzle variability does **not** increase continuously with coverage. It peaks around Coverage# 23 and then slightly decreases at the highest coverage levels:

| Color | sd_std at Cov# 2 | sd_std at Cov# 31 | Peak at | Factor (2→31) |
|-------|-----------------|-------------------|---------|---------------|
| C     | 0.0037          | 0.0104            | Cov# 23 | ~2.8×         |
| K     | 0.0041          | 0.0125            | Cov# 23 | ~3.0×         |
| M     | 0.0027          | 0.0062            | Cov# 23 | ~2.3×         |
| Y     | 0.0024          | 0.0040            | Cov# 18 | ~1.7×         |

The decrease at very high coverage (24–31) likely reflects saturation: when all nozzles are heavily loaded, density differences between nozzles are compressed. Y is most robust to coverage changes (1.7× increase); K is worst (3.0×).

Importantly, the coverage factor for sd_std (1.7–3.0×) is much smaller than for sd_mean (5.7–7.1×), meaning **coverage affects how much ink is deposited much more than how consistently nozzles fire**.

### Correlation between sd_mean and sd_std

The Pearson correlation between average density and nozzle variability is moderate:

| Color | r(sd_mean, sd_std) |
|-------|--------------------|
| C     | 0.50               |
| K     | 0.53               |
| M     | 0.46               |
| Y     | 0.35               |

A correlation of ~0.5 means density and uniformity are related but not tightly coupled — it is possible to find settings with relatively high density and low variability. The density/uniformity trade-off is not a hard constraint.

### Effect of Voltage on sd_std

Voltage has a strong, monotone effect on nozzle variability for Color C — stronger than on sd_mean:

| V  | Mean sd_std |
|----|-------------|
| 20 | 0.0062      |
| 22 | 0.0063      |
| 24 | 0.0071      |
| 26 | 0.0089      |
| 28 | 0.0110      |
| 30 | 0.0138      |

V=20 and V=22 are nearly equal and clearly best. V=30 is 2.2× worse than V=20. **Voltage is the strongest single controllable driver of nozzle uniformity.**

### Effect of F_r on sd_std

The F_r relationship for sd_std is highly non-linear and different from what sd_mean suggested. For Color C:

- **Worst F_r values**: 1.105 (sd_std=0.015), 1.02 (0.011), 1.379 (0.011), 1.20 (0.011)
- **Best F_r values**: 1.32 (0.006), 1.23 (0.006), 1.09 (0.006), 1.14 (0.006)

Note that F_r=1.02 — which appeared robust in the sd_mean analysis — is actually among the worst for uniformity. Conversely, F_r=1.32 and F_r=1.23, which seemed intermediate in sd_mean, are the most consistent settings. **The optimal F_r for uniformity is different from the optimal F_r for density level.**

### Most/least uniform (V, F_r) combinations for sd_std (Color C)

| Type            | V    | F_r   | sd_std sensitivity |
|-----------------|------|-------|--------------------|
| Most robust     | 24   | 1.32  | 0.0051             |
| Most robust     | 22   | 1.09  | 0.0057             |
| Most robust     | 22   | 1.23  | 0.0058             |
| Most sensitive  | 28   | 1.105 | 0.0163             |
| Most sensitive  | 30   | 1.20  | 0.0174             |
| Most sensitive  | 30   | 1.02  | 0.0200             |

High voltage combined with certain F_r values (1.105, 1.20, 1.02) produces the worst nozzle-to-nozzle variability. Low-to-mid voltage with F_r in the 1.09–1.32 range is the most stable region.

### Revised recommended settings (based on sd_std)

These settings minimise nozzle-to-nozzle variability at the given coverage level:

| Color | V     | F_r        | Note |
|-------|-------|------------|------|
| C     | 20–22 | 1.09–1.32  | Avoid F_r=1.02, 1.105, 1.379 |
| K     | 20–22 | similar pattern expected | requires dedicated sd_std analysis |
| M     | 20–22 | similar pattern expected | requires dedicated sd_std analysis |
| Y     | 20–22 | similar pattern expected | requires dedicated sd_std analysis |

These differ from the sd_mean-based recommendations — particularly for F_r. A full sd_std analysis per colour is needed before finalising parameter recommendations.
