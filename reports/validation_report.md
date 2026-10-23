# Validation report

Executed October 23, 2026 from the project directory using Python 3.13 / Anaconda with project-local optional libraries.

- 23 automated tests passed. Coverage includes ZIP normalization, leakage allowlist, join cardinality, geographic scope, historical feature independence from future values, split-group isolation, persisted-model prediction equality, forecast horizons/dates, all five forecast methods, assistant identity/refusal behavior, actual SHAP additivity, boundary validity, all seven app sections and empty-filter behavior.
- Fixed assistant benchmark: 60/60 expected-fact checks passed across six held-out properties. This narrow deterministic test does not establish general LLM accuracy.
- Fresh serving dependency resolution succeeded for requirements.txt using pip dry-run with installed packages ignored. This verifies resolution on the current platform, not every future hosting environment.
- Source manifest, model metrics, common forecast cases and split IDs are saved in artifacts/evaluation. Model artifact predictions match exported held-out estimates.
- Browser inspection verified overview values, light-theme contrast, responsive metric cards, map tiles, choropleth legend, clustering/zoom and property-marker popup. Currency text is escaped for Streamlit Markdown rather than interpreted as mathematical notation.
- Seven generalized Census polygons were repaired; all 98 final polygons passed validity checks. Of 8,340 modeled records, 8,320 points fall inside the selected ZCTA union. Twenty outside-union points are hidden from the map; 8,214 lie inside their corresponding same-numbered ZCTA. Postal ZIP/ZCTA differences remain explicit.
- Local app runs at http://127.0.0.1:8501 . Local serving is not public hosting.
- Public repository created and checked: https://github.com/KrishnachaithanyaThummala/houston-housing-market-intelligence . Remote tree excludes raw downloads and local optional runtime packages. A focused source secret-pattern scan found no matching credentials; environment secrets are ignored.
- Public application hosting is unverified. Streamlit Community Cloud displayed a sign-in page with terms acceptance; the user must review and complete that step. No public app URL has been claimed.

Known remaining items: actual Challenge 2 rubric/deadline, team names, final slide deck and four untested LLM configurations. These are not marked complete by the local file-manifest validator.
