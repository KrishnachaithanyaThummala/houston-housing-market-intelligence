# Architecture

```mermaid
flowchart TD
    A[Kaggle light JSON] --> C[Schema audit and cleaning]
    B[Supplied ZHVI CSV] --> D[Texas city-label filter and monthly checks]
    C --> E[Validated ZIP join and historical feature alignment]
    D --> E
    E --> F[Grouped CV and nested cross-fitting]
    D --> G[Chronological forecasting backtests]
    F --> H[Saved pipeline, predictions and evaluations]
    G --> I[Saved monthly forecasts and empirical intervals]
    J[Census ZCTA polygons] --> K[Geometry repair and coverage checks]
    H --> L[Streamlit dashboard]
    I --> L
    K --> L
    L --> M[Actual SHAP explanations]
    L --> N[Record-grounded deterministic Q&A]
```

Training and serving are separate. Only the offline pipeline reads raw files and performs model fits. The application loads compact saved artifacts with caching and uses the trusted selected pipeline for SHAP. No large downloads, paid API or retraining occurs on app startup. Source acquisition, model choice, partitions and metrics are recorded in artifacts/evaluation.
