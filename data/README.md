# Data storage and provenance

Raw source downloads are local-only under raw/ and excluded from Git. Reproduction uses scripts/download_listings.py plus the supplied Zillow CSV. No Zillow listing images or agent contacts are published.

processed/integrated.parquet: cleaned residential records, with validated ZIP-level historical and latest index metadata. Unmatched rows remain in this table. processed/zhvi.parquet: 98 ZIP monthly histories, including explicit missing values. processed/zip_metadata.parquet: unique Texas city-label scope metadata. geographic/houston_zcta.geojson: repaired, generalized 2020 Census ZCTA polygons in EPSG:4326; the source copy remains local under raw/.

Saved app predictions include nested OOF training records and selected-model validation/test records. The interface shows held-out records to keep displayed predictions and SHAP consistent. Source licenses/attribution and transformation notes are in DATA_ATTRIBUTION.md. Exact schemas, hashes, download metadata and audit counts are under artifacts/evaluation. Do not describe the records as current live listings.
