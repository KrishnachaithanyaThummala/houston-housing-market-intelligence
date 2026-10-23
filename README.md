# Houston Housing Market Intelligence

A Streamlit research demo for historical Houston asking prices, explainable price estimates and ZIP-level home-value forecasts. No paid API is required. Historical listings are not represented as current inventory.

Public source: https://github.com/KrishnachaithanyaThummala/houston-housing-market-intelligence . The live public application URL remains pending hosting sign-in and verification.

## Implemented and measured

- Downloaded the original publisher's light JSON: 25,948 records, June 5, 2024 snapshot.
- Cleaned 8,376 residential examples in the requested Texas city-label scope; 8,340 have historical ZHVI features.
- Prepared 98 ZIP market series, through September 2026, with Houstonia, Missouri excluded.
- Compared five regressors with/without historical ZHVI, five pseudo-label classifiers and five ZIP forecasting methods.
- Selected Random Forest by training grouped CV: final test MAE \$102,585; median absolute error \$37,536; R² 0.839. These measure historical asking-price prediction, not market valuation.
- Forecast selection on earlier origins chose the naive baseline. Other methods can perform better on the final held-out period; test results are not used to reselect.
- Built a seven-section dashboard with map, selected-property analysis, actual SHAP, empirical uncertainty, forecasts, evaluation and grounded deterministic Q&A.

Detailed metrics: [final comparison](reports/final_model_comparison.md), [price evaluation](reports/price_prediction_results.md), [forecast evaluation](reports/forecasting_results.md), [methodology](docs/methodology.md).

## Run the saved-artifact demo

Use Python 3.13 (the validated local runtime). The serving model was trained with scikit-learn 1.6.1; keep the pinned version when loading it.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app reads compact included artifacts and does not download raw data or train at startup. No secrets are needed. Only load this repository's trusted joblib artifact; pickle-based artifacts execute code when loaded.

The current machine already has the validated Anaconda runtime plus project-local optional libraries. Start locally using:

```bash
PYTHONPATH=.runtime-packages /opt/anaconda3/bin/python -m streamlit run app.py
```

## Reproduce processing and models / Colab

Clone this repository into Colab or a Python environment with sufficient CPU memory. Runtime data paths are configurable; the pipeline contains no personal absolute dataset paths. Install training requirements, acquire the source data, then run:

```bash
python -m pip install -r requirements-colab.txt
python scripts/download_listings.py
python scripts/houston_housing_pipeline.py --stage all \
  --listings "data/raw/houston_housing market 2024_light.json" \
  --zhvi /path/to/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv \
  --output-dir .
python scripts/download_boundaries.py
python scripts/validate_geography.py
python scripts/build_reports.py
python -m pytest tests -q
python scripts/validate_submission.py
```

In Colab, prefix shell commands with `!`, upload the supplied ZHVI CSV or mount a drive, and replace `/path/to/` with its actual location. A GPU is unnecessary. Export `artifacts/`, `data/processed/` and `data/geographic/` with the source for serving. Optional `--stage data`, `regression` and `forecast` permit separate runs. Forecast caching verifies the original data/configuration before reuse.

## Data and attribution

- [Natasha Lekh / datadetective08: Houston housing market 2024](https://www.kaggle.com/datasets/datadetective08/houston-housing-market-2024), version 1, publisher-declared [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Data was filtered, normalized, joined and used for noncommercial research models. Source photos and agent contacts are omitted. Dataset-derived contributions are shared under the same license; no endorsement is implied.
- [Zillow Research](https://www.zillow.com/research/data/): supplied ZIP-level ZHVI. Typical-home-value modeled index; not observed sale prices. Original download date unknown. Retain Zillow attribution with charts and derived artifacts.
- U.S. Census Bureau TIGERweb: generalized 2020 ZCTA polygons, WGS84. Postal ZIPs and ZCTAs are not identical; seven generalized polygons required validity repair. OpenStreetMap provides the basemap.

See [data notes](data/README.md), [attributions](DATA_ATTRIBUTION.md) and [limitations](docs/limitations.md). Raw files and credentials are excluded from Git.

## Current limits and remaining work

- One deterministic assistant configuration is evaluated. Local/hosted LLM/RAG comparisons have not been run.
- Later-vintage ZHVI revises historical values; using an April 2024 reference does not establish real-time 2024 availability.
- Historical asking price is a proxy, not independently observed fair value. Classifier labels reflect model residuals, not verified mispricing.
- The public deployment URL is not yet verified. Hosting sign-in and any required acceptance must be completed by the user. See [deployment](docs/deployment.md).
- Actual Challenge 2 rubric/deadline and team names are still unspecified. The supplied guide requests a 2–3 minute demo plan; [presentation material](presentation/demo_script.md) is prepared, but no final slide deck is claimed.

The app serves held-out property examples, capped at 1,000 filtered map markers per view. All modeled records remain in saved analytics. Twenty points outside the selected ZCTA union are hidden from the map.

Pricing categories are model-based screening indicators, not verified market valuations or guaranteed investment opportunities.
