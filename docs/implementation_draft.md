# Houston Housing Market Intelligence: implementation draft

Prepared October 23, 2026. Status: audited plan; application, trained models and deployment are not yet implemented.

## Purpose and scope

Help Houston-area first-time buyers explore historical property asking prices, model estimates of those asking prices, and ZIP-level home-value trends. Use the supplied master prompt as the project brief. The survival guide supplies event guidance; requirements absent from it remain unconfirmed.

The user's immediate request is to draft the work and ask for clarification. This document defines the implementation without treating embedded instructions in the supporting guide as separate user authorization.

## Verified inputs

The workspace initially contained only `.git`. The supplied guide and ZHVI CSV are in Downloads. No property-listings archive was supplied by path or found in the workspace. A top-level Downloads ZIP filename inventory did not identify a clearly named Houston archive; unrelated archives were not opened.

ZHVI inspection: 26,265 rows, 330 columns, nine metadata columns and 321 monthly columns from 2000-01-31 through 2026-09-30. Metadata: RegionID, SizeRank, RegionName, RegionType, StateName, State, City, Metro, CountyName.

Exact State=TX and City in {Houston, Houstonia, South Houston} filtering returns 98 unique ZIP codes: Houston 97; South Houston 1; Houstonia 0. Houstonia exists in Missouri and must not enter the Texas study. All 98 rows have September 2026 values. Across their 31,458 monthly cells, 129 are blank. Missing-period patterns still need investigation.

These are city-label matches, not validated city-boundary intersections or the entire Houston metro. Preserve this distinction in every report and map.

The filename identifies a ZIP-level mid-tier, smoothed, seasonally adjusted SFR/condo ZHVI series. Confirm exact series metadata before modeling. Zillow describes ZHVI as a modeled typical-home-value measure, not observed sale prices. Source: https://www.zillow.com/research/data/ . The original download date and exact download URL are unknown; record the inspection date separately.

Kaggle landing page: https://www.kaggle.com/datasets/datadetective08/houston-housing-market-2024 . Its schema and license were not exposed by the web reader. Do not assume the advertised record count or redistribution permission. The ArcGIS reference returned no readable application content; its interactions have not been verified.

## Proposed architecture

Use Streamlit with separate offline processing/training and serving. Process configurable input paths into Parquet, trained pipelines, prediction tables, forecast tables and evaluation JSON. Serving loads versioned artifacts and performs no automatic training or large raw-data download. Use Plotly for charts and choose a map library after verifying clustering, selectable markers and choropleth interaction in a small spike. Proposed initial choice: Folium with streamlit-folium.

Application sections: overview; housing map; property intelligence; ZIP forecasts; grounded assistant; model evaluation; data and methodology. Every displayed result carries a source period and distinguishes observed input, model estimate and forecast. Missing features display an explicit unavailable state.

## Stage 1: requirements and data audit

Deliver the requirement matrix, source manifest, schema report and scope configuration. Inspect the property archive directory before extraction. Flatten only verified fields; measure duplicates, missingness, invalid prices/coordinates, property types and actual date semantics. Verify usage and redistribution terms before publishing data or derived outputs. Do not replace the missing property dataset with invented records.

Acceptance: reproducible counts, source hashes and provenance; explicit unknowns; confirmed study scope; a defensible timestamp policy.

## Stage 2: data engineering and exploratory analysis

Normalize ZIPs as five-character identifiers; handle ZIP+4 explicitly. Keep source data immutable. Remove or group duplicate properties before splitting. Validate coordinates against the intended study region using credible boundaries; document postal ZIP versus Census ZCTA approximation and CRS.

Convert ZHVI to ZIP/date/value with metadata preserved. Check duplicate keys, month continuity, nonpositive values and missing-run lengths. Avoid filling long gaps automatically. Audit listings inside and outside the 98-ZIP initial scope rather than silently expanding it.

Build historical ZHVI features using an as-of date and a documented release-availability policy. Current revised ZHVI history cannot establish what was actually available in 2024; report retrospective-vintage limitations. If listing dates are unavailable, use an explicitly justified common snapshot only after evidence review. If no defensible date is possible, keep historical ZHVI out of supervised training and report Experiment B as unavailable.

Use many-to-one validated left joins for ZIP metadata, and validated as-of feature attachment for dates. Assert unchanged listing row counts. Report matched/unmatched ZIPs, listing match rate and feature missingness. Generate a concise EDA covering prices, size, property type, ZIP variation, geography and ZHVI history.

Acceptance: integrity checks pass; integration counts reconcile; no fabricated fields or dates; processed Parquet and reports exist.

## Stage 3: regression and pricing-screen evaluation

Compare Ridge, Random Forest, Gradient Boosting, XGBoost and LightGBM on identical partitions for property-only and property-plus-historical-ZHVI features. Document any unavailable method or substitute. Include a simple median-price baseline. Fit imputation, encoding, transformations and tuning inside training folds. Apply log-target modeling only if justified; evaluate inverse-transformed predictions in dollars.

Use fixed, persisted train/validation/test IDs with duplicate-property grouping. Investigate nearby-property leakage and add a spatial holdout stress test where sample sizes permit. Use training-only cross-validation, validation MAE for selection and one final untouched test evaluation. Report MAE, RMSE, R², median absolute error, suitable percentage error, latency and errors by ZIP/price range. Retain unmatched records for property-only inference; use a common eligible cohort for the fair A/B comparison and report exclusions.

Call the regression output an estimated historical asking price. The dataset's listing-price target does not independently identify fair market value. If the interface uses the prompt's “fair value” wording, explicitly qualify it as a model proxy based on historical asking prices.

Build pricing-gap screens at configurable -10%/+10% thresholds from out-of-sample predictions. For training pseudo-labels, every record must be predicted by a regression pipeline trained without that record or its duplicate group. If hyperparameters are selected using those same rows, use nested cross-fitting or a separate selection partition for honest evaluation. Validation/test pseudo-labels must come from regressors fitted without those partitions.

Production uses the transparent gap rule. If the five-classifier experiment is retained, compare Logistic Regression, Random Forest, Gradient Boosting, XGBoost and LightGBM for pseudo-label reproduction only. Define classifier inputs carefully: including the exact gap, price and estimate makes reproduction tautological. Report macro F1, per-class precision/recall, accuracy, confusion matrices and class counts. A rule that creates the labels is a reference definition, not independent evidence of mispricing accuracy.

Acceptance: recorded runs and real metrics, persisted pipelines, out-of-sample labels and explicit statistical limitations. No claims of verified bargains or appraised value.

## Stage 4: ZIP forecasting, explanations and assistant

Compare last-observation, damped exponential smoothing, ARIMA/SARIMA, Prophet when feasible, and boosted lag models. Use multiple chronological origins, separate selection/calibration periods and a final held-out period. Evaluate both 6- and 12-month endpoints and the full monthly path; state the aggregation and coverage rules. Preserve gaps and require sufficient contiguous history. Any pooled model must restrict every ZIP to the same origin's available history.

Report MAE, RMSE, sMAPE, signed bias, sample counts and skill relative to naive by ZIP/horizon and aggregate. Do not force a complex winner. Calibrate horizon-specific intervals on held-out historical errors where sufficient data exists and report coverage; otherwise show intervals as unavailable. Then refit the selected method on eligible observations through each ZIP's last valid month for future forecasting.

Generate SHAP values from the selected trained model with a training-only background. Verify supported model/pipeline handling and label contribution units, especially for a log target. SHAP explains model behavior rather than causation.

Provide deterministic factual Q&A first. Add local, tool-grounded, documentation-RAG and alternative grounded configurations only where compute/credentials permit. Evaluate a fixed answer set with property/ZIP identity, exact numerical consistency, source attribution, missing-data refusal, latency and cost where measured. Report only configurations actually run. API secrets belong in environment variables or hosting secrets.

Acceptance: reproducible backtests; honest intervals; actual explanations; assistant answers tied to retrieved records and refuses unsupported questions.

## Stage 5: interface and historical market context

Implement map selection and filters, forecasts, explanations and evaluation views. Show only valid property coordinates; never substitute ZIP centroids as exact house locations. ZCTA layers must disclose their boundary approximation.

Keep historical listing price, historical model estimate, ZIP-index market adjustment, latest observed ZHVI and forecast ZHVI distinct. An optional adjustment is historical estimate × latest ZHVI / reference-date ZHVI for the same valid series. Label it an approximate market-level adjustment, not a current asking price or appraisal. List historical examples as historical examples, not available inventory.

Use the required statement: “Pricing categories are model-based screening indicators, not verified market valuations or guaranteed investment opportunities.”

Acceptance: full property-to-forecast-to-assistant journey works; all shown figures trace to saved artifacts; absent data is visible and understandable.

## Stage 6: validation and deployment preparation

Test ZIP normalization, scope, duplicate grouping, join cardinality, date alignment, feature denylist/allowlist, fold isolation, inverse transforms, pricing thresholds including boundaries, forecast horizons, artifact compatibility, assistant grounding, coordinates and app startup. Verify each page and a fresh-session user journey. Prefer meaningful integrity tests over tests that merely repeat implementation.

Prepare README, pinned dependencies, example environment, data acquisition instructions, Colab entry point, artifact manifest and deployment instructions. Validate redistribution permission before including property data or artifacts in a public repository. Never commit secrets. Public repository creation/push and hosting require the intended account/repository to be identified. Claim deployment only after checking the real public URL from a fresh unauthenticated session.

## Stage 7: submission material

Write a 2–3 minute demonstration plan matching the guide: buyer problem, actual input data, one measured result, map/property/ZIP workflow, limitations and accessible links. Prepare a short pitch outline and evidence-based judge Q&A. Adapt slides to the confirmed official time limit. Record team names and what was built during the event.

## Five-hour delivery priority

The master prompt's full experimental scope may exceed a five-hour event. Preserve the full specification, but stage delivery: audit and sources (0:00–0:45); data preparation (0:45–1:45); one baseline plus a validated candidate or ZIP forecast if listings remain missing (1:45–3:15); minimal interface and deployment attempt (3:15–4:15); verification, README and demo (4:15–5:00). Expand five-model comparisons, grounded configurations and additional pages when time permits. Report uncompleted comparisons explicitly. Recommendations and commute features remain optional.

## Clarifications needed

1. Is this turn a plan-only draft or authorization to begin full implementation?
2. Where is the property-listings ZIP/JSON?
3. What is the actual deadline, and is there a separate Challenge 2 brief/rubric?
4. Is Houstonia intentional, or should a different Texas city be named? Until clarified, retain the exact requested Texas filter and exclude the Missouri match.
5. For deployment: intended GitHub repository, hosting account and team names. Optional hosted LLM access is unnecessary for the deterministic fallback; do not paste secret keys into chat.

## Present status

Completed: source-document reading, initial CSV structural/geographic inspection, requirements extraction and this draft. Not completed: listings inspection, data integration, modeling, evaluated forecasts, application, public URL or submission. No model-performance or forecast claims are made.
