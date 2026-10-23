# Methodology

## Data and geographic scope

Two distinct units of analysis: historical property asking-price records and monthly ZIP-level ZHVI. Texas plus exact Houston/Houstonia/South Houston labels defines scope. Houstonia has no Texas match. City labels are not a municipal boundary or the entire metro. Property types are limited to single-family, condo and townhouse; lots, manufactured and multifamily are excluded from this residential experiment. Missing/nonpositive price, malformed ZIP and nonpositive living area are excluded. Two residential prices below \$20,000 are excluded as ambiguous entries under a declared rule, not inferred to be rentals. No upper-price trimming is used.

## Historical reference and feature allowlist

The publisher's snapshot date is June 5, 2024. No individual start dates or year built are inferred from unrelated fields. April 30, 2024 is a conservative completed-month reference. The model uses that ZHVI value and 6/12-month changes, along with beds, baths, living area, known-unit lot area, coordinates, ZIP and property type. Zestimate, rent Zestimate, tax assessment, duplicate price fields, price reductions, days/time on Zillow, listing IDs and addresses are excluded as model predictors. Latest ZHVI is display-only and never enters historical training.

The supplied 2026 vintage can revise past values. An observation-date cutoff does not restore vintage/release-time availability. Evaluations therefore remain retrospective. The ZIP integration validates many-to-one cardinality and retains all cleaned rows; the common A/B cohort excludes unmatched market-feature rows, with counts recorded.

## Model evaluation

Partitions persist as property IDs and connected address/rounded-coordinate groups. Approximately 60/20/20 training/validation/test; actual counts differ with group sizes. Every imputation, scaling and encoding fit occurs within training folds. Fixed modest model configurations compare 3 grouped CV folds. Training CV dollar MAE selects the model family and feature set before test evaluation. All candidate test results are then reported without reselection. Validation residuals calibrate one global empirical 90% dollar band. A training-only ZIP holdout probes geographic extrapolation; it is not the same distribution as the main test.

Outer-fold training labels use inner-fold regression model/feature-set selection and fit only on the outer training portion. These out-of-sample estimates define pricing gaps and pseudo-labels. Five auxiliary classifiers exclude the exact gap, asking price and regression estimate, preventing trivial label-formula reproduction. Macro F1 selects the auxiliary classifier on validation; final test metrics describe pseudo-label reproduction. The application uses the direct configurable gap rule instead.

## Forecasting

Two earlier nonoverlapping forecast origins select a method on mean MAE at months 6 and 12 across ZIPs. A third origin calibrates horizon-specific 90th-percentile relative-error bands. A fourth origin is held out. All 12 monthly path predictions are retained; endpoint metrics and complete monthly errors are available. Missing runs are never silently forward-filled. Each training prefix uses contiguous positive data and at least 60 months. Forecasts refit the earlier-selected method using available history through September 2026. Neither better test scores from an alternative nor a favorable ZIP triggers reselection.

Methods: last observation, damped additive trend, log ARIMA(1,1,0) with drift, Prophet with seasonality disabled for seasonally adjusted values, and recursive XGBoost over lagged monthly log returns. No exhaustive model tuning. Intervals pool relative errors across correlated ZIPs and do not guarantee future coverage. No ZHVI forecast is an individual-property sale-price forecast.

## Explainability and assistant

SHAP TreeExplainer reads the actual selected trained model, and verifies baseline plus contributions equals the predicted log1p price. Contributions are on the log-price scale, not dollars or causal effects. Held-out examples ensure the displayed prediction and explanation come from the same trained model.

The assistant performs deterministic intent matching against the selected property and ZIP forecast. It states missing information, checks explicit mismatched identifiers and avoids unsupported school/crime/flood/owner claims. Sixty fixed questions across six held-out properties test expected facts, identity mismatch and refusals. This is a narrow factual check, not general natural-language competence. No generative LLM comparison has been completed.
