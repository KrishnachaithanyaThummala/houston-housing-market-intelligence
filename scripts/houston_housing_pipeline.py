"""Configurable offline entry point; serving never trains models."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd

from src.data import clean_zhvi, clean_listings, historical_market, integrate


def save_json(root, name, value):
    (root / 'artifacts/evaluation' / name).write_text(json.dumps(value, indent=2, default=str, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zhvi', type=Path)
    parser.add_argument('--listings', type=Path)
    parser.add_argument('--output-dir', type=Path, default=ROOT)
    parser.add_argument('--stage', choices=['data', 'regression', 'forecast', 'all'], default='all')
    parser.add_argument('--resume-forecast', action='store_true', help='Reuse backtests only for identical data/code/configuration')
    args = parser.parse_args()
    root = args.output_dir.resolve()
    for directory in ['data/processed', 'artifacts/evaluation', 'artifacts/models',
                      'artifacts/predictions', 'artifacts/forecasts', 'reports']:
        (root / directory).mkdir(parents=True, exist_ok=True)
    if args.stage in ['data', 'all']:
        if not args.zhvi or not args.listings:
            parser.error('--zhvi and --listings are required for data/all stage')
        metadata, long, zhvi_report = clean_zhvi(args.zhvi)
        listings, listing_report = clean_listings(args.listings)
        integrated, join_report = integrate(listings, historical_market(long))
        metadata.to_parquet(root / 'data/processed/zip_metadata.parquet', index=False)
        long.to_parquet(root / 'data/processed/zhvi.parquet', index=False)
        integrated.to_parquet(root / 'data/processed/integrated.parquet', index=False)
        save_json(root, 'zhvi_audit.json', zhvi_report)
        save_json(root, 'listings_audit.json', listing_report)
        save_json(root, 'integration_audit.json', join_report)
        print(json.dumps({'zhvi': zhvi_report, 'listings': {k:v for k,v in listing_report.items() if k!='flattened_columns'},
                          'integration': join_report}, indent=2), flush=True)
    if args.stage in ['regression', 'all']:
        from src.modeling import run_regression, run_classification
        properties, report = run_regression(pd.read_parquet(root / 'data/processed/integrated.parquet'), root)
        save_json(root, 'regression_report.json', report)
        save_json(root, 'classification_report.json', run_classification(properties, root))
    if args.stage in ['forecast', 'all']:
        from src.forecasting import forecast_all
        save_json(root, 'forecast_report.json', forecast_all(pd.read_parquet(root / 'data/processed/zhvi.parquet'), root, args.resume_forecast))
    save_json(root, f'last_run_{args.stage}.json', {'stage': args.stage, 'completed_at_utc': datetime.now(timezone.utc).isoformat()})


if __name__ == '__main__':
    main()
