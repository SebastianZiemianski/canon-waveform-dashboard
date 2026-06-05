# Could Canon actually use this model?

## What they could use right now

The optimal settings table (cell 7 in both notebooks) is directly useful. For every color and coverage level, it shows which V, F_r and dt2 combination produces the most consistent print output. This is based on real experimental data, so Canon could already use these recommendations to tune their printheads without having to test every combination manually.

## Why the model itself is not ready for production yet

### Technical issues
- There is no input validation. If you enter a coverage value that was never in the training data (like 55), the model still gives you a number — but that number is not meaningful. It would need a check that warns the user when a value is outside the training range.
- The model only exists as a Jupyter notebook. Canon's systems can't call a notebook. For real use, the trained model would need to be saved to a file and wrapped in something like an API.

### Data issues
- The model was trained on one experiment with 30 specific chips. Canon probably has many different printhead batches. We don't know yet if the model works just as well for a completely different batch of hardware.
- For model 2, we tested it on a random 20% split of the same data. That's not the same as testing on a different print run — so the R²=0.998 might be a bit optimistic.

## What would need to happen before Canon could rely on it

1. Save the trained model to a file so it can be reloaded without retraining
2. Add input validation so it rejects values outside the training range
3. Test it on data from a completely different print run to verify it generalises
4. Check if it still works well on new printhead batches

## Summary

Right now this is a working proof of concept. It shows the approach is valid and the recommendations in cell 7 are already useful. But it would need the steps above before it could be part of a real production workflow at Canon.
