# Project rules

- Preserve source provenance, actual measurements and explicit limitations. Never invent listing attributes, forecasts, sources or deployment success.
- Keep raw datasets and secrets out of Git. Retain DATA_ATTRIBUTION.md with derived data.
- Use explicit predictor allowlists. Never use Zestimate, rent estimates, price-derived fields or latest ZHVI as historical price-model predictors.
- Fit preprocessing and selection inside the appropriate training folds. Keep final test results out of selection. Out-of-sample pseudo-labels are not independent mispricing truth.
- Distinguish historical asking prices, model estimates, market-level adjustments and ZIP forecasts in user-facing text.
- Models train offline; the serving app loads saved artifacts only.
- Run relevant integrity checks and Streamlit AppTest after changes. Verify public hosting before recording a public URL.
- Keep dependency versions compatible with the saved model and deployment runtime.
