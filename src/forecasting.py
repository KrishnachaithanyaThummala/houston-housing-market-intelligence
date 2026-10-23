"""Five-method rolling-origin evaluation with separated selection/calibration/test origins."""
import logging
import hashlib
import json
from pathlib import Path
import warnings
from time import perf_counter

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

METHODS = ['Naive', 'Damped trend', 'ARIMA', 'Prophet', 'XGBoost lags']
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)


def predict_path(values, method, horizon=12):
    y = np.asarray(values, dtype=float)
    if len(y) < 60 or not np.isfinite(y).all() or (y <= 0).any():
        raise ValueError('Need 60 positive contiguous monthly observations')
    if method == 'Naive':
        return np.repeat(y[-1], horizon)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        if method == 'Damped trend':
            return np.maximum(ExponentialSmoothing(y, trend='add', damped_trend=True,
                initialization_method='estimated').fit(optimized=True).forecast(horizon), 1)
        if method == 'ARIMA':
            return np.exp(
                ARIMA(np.log(y), order=(1, 1, 0), trend='t').fit().forecast(horizon).clip(-20, 30))
        if method == 'Prophet':
            from prophet import Prophet
            dates = pd.date_range('2000-01-31', periods=len(y), freq='ME')
            model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False,
                            uncertainty_samples=0, changepoint_prior_scale=.01)
            model.fit(pd.DataFrame({'ds': dates, 'y': y / y[-1]}))
            future = pd.date_range(dates[-1] + pd.offsets.MonthEnd(), periods=horizon, freq='ME')
            return np.maximum(model.predict(pd.DataFrame({'ds': future})).yhat.to_numpy() * y[-1], 1)
        if method == 'XGBoost lags':
            from xgboost import XGBRegressor
            # Predict monthly log returns using only prior returns. Scale-free recursive model.
            r = np.diff(np.log(y))
            def features(v):
                return [v[-1], v[-3:].mean(), v[-6:].mean(), v[-12:].mean(), v[-12:].std()]
            x = np.array([features(r[:i]) for i in range(12, len(r))])
            model = XGBRegressor(n_estimators=60, max_depth=2, learning_rate=.04,
                                 reg_lambda=10, n_jobs=1, random_state=42)
            model.fit(x, r[12:])
            result, history, level = [], list(r), y[-1]
            for _ in range(horizon):
                ret = float(model.predict(np.array([features(np.array(history))]))[0])
                level *= np.exp(np.clip(ret, -.2, .2))
                result.append(level)
                history.append(ret)
            return np.array(result)
    raise ValueError(f'Unknown method {method}')


def forecast_all(long, root, resume=False):
    wide = long.pivot(index='date', columns='zip_code', values='zhvi_value').sort_index()
    n = len(wide)
    # Nonoverlapping 12-month blocks: selection, calibration, final held-out test.
    origins = [(n - 48, 'selection'), (n - 36, 'selection'),
               (n - 24, 'calibration'), (n - 12, 'test')]
    records, failures = [], []
    completed = set()
    fingerprint = hashlib.sha256(pd.util.hash_pandas_object(long, index=True).values.tobytes()
                                 + Path(__file__).read_bytes()).hexdigest()
    fingerprint_path = root / 'artifacts/evaluation/forecast_fingerprint.json'
    if resume and (root / 'artifacts/forecasts/backtests.parquet').exists():
        if not fingerprint_path.exists() or json.loads(fingerprint_path.read_text())['fingerprint'] != fingerprint:
            raise ValueError('Forecast cache data/code fingerprint changed; rerun without --resume-forecast')
        previous = pd.read_parquet(root / 'artifacts/forecasts/backtests.parquet')
        records = previous.drop(columns=['error', 'abs_error', 'squared_error', 'smape'], errors='ignore').to_dict('records')
        completed = set(map(tuple, previous[['zip_code', 'method', 'phase', 'origin']].drop_duplicates().to_numpy()))
    for count, zip_code in enumerate(wide, 1):
        series = wide[zip_code]
        # Initial gaps are removed. Later gaps require restarting the contiguous history.
        last_gap = np.flatnonzero(series.isna().to_numpy())
        start = int(last_gap[-1] + 1) if len(last_gap) else 0
        for end, phase in origins:
            train, actual = series.iloc[start:end], series.iloc[end:end + 12]
            for method in METHODS:
                if (zip_code, method, phase, str(wide.index[end-1].date())) in completed:
                    continue
                try:
                    t = perf_counter()
                    pred = predict_path(train.to_numpy(), method)
                    if len(actual) != 12 or actual.isna().any() or not np.isfinite(pred).all():
                        raise ValueError('Incomplete forecast evaluation window')
                    elapsed = perf_counter() - t
                    for h, (date, true, estimate) in enumerate(zip(actual.index, actual, pred), 1):
                        records.append({'zip_code': zip_code, 'method': method, 'phase': phase,
                            'origin': str(wide.index[end - 1].date()), 'date': date, 'horizon': h,
                            'actual': true, 'prediction': float(estimate), 'fit_predict_seconds': elapsed})
                except Exception as exc:
                    failures.append({'zip_code': zip_code, 'method': method, 'phase': phase, 'reason': str(exc)})
        if count % 10 == 0:
            print(f'Forecast backtests: {count}/{len(wide.columns)} ZIPs', flush=True)
    backtests = pd.DataFrame(records)
    backtests['error'] = backtests.prediction - backtests.actual
    backtests['abs_error'] = backtests.error.abs()
    backtests['squared_error'] = backtests.error**2
    backtests['smape'] = 200 * backtests.abs_error / (backtests.prediction.abs() + backtests.actual.abs())
    # Compare methods on common ZIP-origin-horizon cases; a failing method cannot win on an easy subset.
    required = ['zip_code', 'origin', 'horizon']
    complete = backtests.groupby(required).method.nunique().eq(len(METHODS))
    common = complete[complete].reset_index()[required]
    if common.empty:
        # Explicitly drop entirely unavailable methods; retain all recorded failures in report.
        available = sorted(set(backtests.method))
        complete = backtests.groupby(required).method.nunique().eq(len(available))
        common = complete[complete].reset_index()[required]
    comparable = backtests.merge(common, on=required, validate='many_to_one')
    if comparable.empty:
        raise ValueError('No common backtest cases')
    endpoints = comparable[comparable.horizon.isin([6, 12])]
    summary = endpoints.groupby(['phase', 'method', 'horizon']).agg(
        mae=('abs_error', 'mean'), mse=('squared_error', 'mean'), smape=('smape', 'mean'),
        bias=('error', 'mean'), n=('error', 'size')).reset_index()
    summary['rmse'] = np.sqrt(summary.pop('mse'))
    naive = summary[summary.method.eq('Naive')][['phase', 'horizon', 'mae']].rename(columns={'mae': 'naive_mae'})
    summary = summary.merge(naive, on=['phase', 'horizon'], validate='many_to_one')
    summary['mae_skill_vs_naive'] = 1 - summary.mae / summary.naive_mae
    winner = endpoints[endpoints.phase.eq('selection')].groupby('method').abs_error.mean().idxmin()
    print('Forecast selected on earlier origins:', winner, flush=True)
    # Relative-error quantiles from the calibration origin, by horizon; empirical pooled intervals.
    calibration = comparable[comparable.phase.eq('calibration') & comparable.method.eq(winner)].copy()
    calibration['relative_abs_error'] = calibration.abs_error / calibration.prediction
    quantiles = calibration.groupby('horizon').relative_abs_error.quantile(.90, interpolation='higher')
    selected_test = comparable[comparable.phase.eq('test') & comparable.method.eq(winner)].copy()
    selected_test['radius'] = selected_test.horizon.map(quantiles) * selected_test.prediction
    selected_test['covered'] = selected_test.abs_error <= selected_test.radius
    coverage = selected_test.groupby('horizon').covered.mean().to_dict()
    future_rows = []
    for zip_code in wide:
        s = wide[zip_code]
        gaps = np.flatnonzero(s.isna().to_numpy())
        start = int(gaps[-1] + 1) if len(gaps) else 0
        try:
            preds = predict_path(s.iloc[start:].to_numpy(), winner)
            for h, value in enumerate(preds, 1):
                q = quantiles.get(h, np.nan)
                future_rows.append({'zip_code': zip_code, 'date': s.index[-1] + pd.offsets.MonthEnd(h),
                    'horizon': h, 'prediction': float(value), 'lower': max(0, value * (1-q)),
                    'upper': value * (1+q), 'latest_zhvi': float(s.iloc[-1]), 'method': winner})
        except Exception as exc:
            failures.append({'zip_code': zip_code, 'method': winner, 'phase': 'future', 'reason': str(exc)})
    backtests.to_parquet(root / 'artifacts/forecasts/backtests.parquet', index=False)
    summary.to_csv(root / 'artifacts/evaluation/forecast_comparison.csv', index=False)
    pd.DataFrame(future_rows).to_parquet(root / 'artifacts/forecasts/forecasts.parquet', index=False)
    fingerprint_path.write_text(json.dumps({'fingerprint': fingerprint, 'methods': METHODS}, indent=2))
    return {'winner': winner, 'methods_requested': METHODS, 'failures': failures,
            'common_endpoint_rows': len(endpoints), 'test_interval_coverage_by_horizon': coverage,
            'interval_method': 'Pooled ZIP relative absolute errors, 90th percentile, separate calibration origin; not guaranteed coverage',
            'origins': [{'cutoff': str(wide.index[e-1].date()), 'phase': p} for e,p in origins],
            'future_zip_count': len({r['zip_code'] for r in future_rows})}
