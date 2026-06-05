# Why predicting SD directly makes more sense

## The problem with predicting std

The current models (model 1 and model 2) predict a variability metric — how much nozzles or chips differ from each other. This is useful for optimisation, but it has a fundamental limitation: std is a derived metric calculated from SD values. You can't work backwards from a predicted std to understand what the print will actually look like.

If the model predicts `cross_chip_std = 0.003`, you know the chips will be consistent — but you don't know what SD level they will consistently produce. A setting that makes all chips consistently produce SD=0.05 and a setting that makes all chips consistently produce SD=0.40 could both have the same std.

## What Canon actually asked for

Canon's feedback was: *"you are trying to predict SD (per nozzle) based on input parameters V, F_r, dt2."*

They want to know the actual SD value the nozzles will produce — not just how variable they are. From predicted SD values you can then derive the std yourself, and also check whether the SD level matches the target density for the print job.

## How the SD models complement the std models

| Model | Predicts | Answers |
|---|---|---|
| Model 1 (std) | sd_std | Are nozzles uniform within one chip? |
| Model 2 (std) | cross_chip_std | Are all 30 chips consistent with each other? |
| Model 3 (SD) | sd_mean | What ink density will one chip produce? |
| Model 4 (SD) | cross_chip_mean | What ink density will all 30 chips produce on average? |

Using model 2 and model 4 together gives the complete answer for a given setting:
- **cross_chip_mean** → what SD level you will get
- **cross_chip_std** → how consistently all chips reach that level

## Why std prediction still has value

The std models are not wrong — they directly answer the optimisation question and are easier to interpret. But they should be seen as a step towards the full picture. The SD prediction models make the approach more complete and more aligned with what Canon described as the actual goal.
