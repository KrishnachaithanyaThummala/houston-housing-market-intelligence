"""Check concrete serving deliverables; never equate local readiness with public deployment."""
import hashlib
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
required=['app.py','requirements.txt','requirements-colab.txt','README.md','DATA_ATTRIBUTION.md',
          '.streamlit/config.toml','artifacts/models/price_pipeline.joblib',
          'artifacts/predictions/properties.parquet','artifacts/forecasts/forecasts.parquet',
          'artifacts/forecasts/backtests.parquet','data/processed/zhvi.parquet',
          'data/processed/zip_metadata.parquet','data/geographic/houston_zcta.geojson',
          'reports/dataset_report.md','reports/dataset_integration_report.md','reports/eda_report.md',
          'reports/price_prediction_results.md','reports/classification_results.md','reports/forecasting_results.md',
          'reports/chatbot_evaluation.md','reports/final_model_comparison.md','docs/deployment.md',
          'presentation/demo_script.md','presentation/judge_qa.md']
missing=[p for p in required if not (root/p).is_file() or (root/p).stat().st_size==0]
manifest={p:{'bytes':(root/p).stat().st_size,
             'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in required if p not in missing}
result={'local_deliverables_present':not missing,'missing':missing,
        'manifest':manifest,'public_url':None,'public_deployment_verified':False,
        'remaining':['Streamlit account/terms sign-in and public deployment verification',
                     'Challenge 2 rubric and actual deadline', 'Team names',
                     'Four untested LLM configurations', 'Final slide deck']}
(root/'artifacts/evaluation/submission_validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='manifest'},indent=2))
sys.exit(1 if missing else 0)
