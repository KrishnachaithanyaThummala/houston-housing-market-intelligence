# Deployment

## Local verified preview

The app runs from precomputed artifacts. Python 3.13 and the pinned dependencies match the validated environment. Launch with `python -m streamlit run app.py`; the local preview is http://127.0.0.1:8501 . A local URL is not a public judge-submission URL.

## Streamlit Community Cloud

Official deployment documentation: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app .

1. Put the repository source, requirements.txt, .streamlit/config.toml, artifacts/, data/processed/ and data/geographic/ in the intended GitHub repository. Exclude data/raw/, .runtime-packages/, environment secrets, caches and logs. Retain DATA_ATTRIBUTION.md and source notices.
2. Sign in at https://share.streamlit.io . The account sign-in page includes acceptance of deployment terms; the user must review and complete this step. No paid API credentials are needed.
3. Choose Create app, use the repository and its branch, and set main file path `app.py`.
4. Select Python 3.13 in advanced settings. Keep scikit-learn 1.6.1 for model compatibility. Do not train during deployment. The saved selected model is about 14 MB.
5. Deploy. If asked for a public app address, choose an available descriptive name. Do not record a guessed address as the live URL.
6. Open the resulting public URL in a fresh unauthenticated session. Verify all seven sections, map tiles, boundary layers, filters, marker selection, selected property prediction, SHAP, forecasts, assistant and missing-result behavior. Ensure the model files are tracked and retrieved correctly.
7. Record the exact verified URL, check date and commit in the submission status report. Only then mark public deployment complete.

## Fallback and current status

The deterministic assistant works without any external API. Raw data is never fetched by the serving process. Tile services still require browser internet connectivity; model outputs and charts remain available without a paid service.

At preparation time GitHub CLI authentication was verified with network access. Streamlit Community Cloud showed a sign-in screen; no public URL has been claimed. Account/terms completion remains a user step. If deployment fails, the local app and source remain reviewable, and the guide allows a shared notebook alternative if the team chooses it.
