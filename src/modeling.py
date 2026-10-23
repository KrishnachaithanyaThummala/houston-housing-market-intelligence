"""Fixed-budget regression comparisons and out-of-sample pricing-screen experiments."""
import json
from time import perf_counter

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (RandomForestRegressor, GradientBoostingRegressor,
                              RandomForestClassifier, GradientBoostingClassifier)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                             median_absolute_error, classification_report, confusion_matrix,
                             accuracy_score, f1_score)
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder

from src.data import NUMERIC, CATEGORICAL, MARKET, check_features, pricing_category

SEED = 42


def regression_models():
    from xgboost import XGBRegressor
    from lightgbm import LGBMRegressor
    return {
        'Ridge': Ridge(alpha=20),
        'Random Forest': RandomForestRegressor(n_estimators=120, min_samples_leaf=3, max_features=.85,
                                                random_state=SEED, n_jobs=2),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=120, max_depth=3, loss='huber',
                                                      random_state=SEED),
        'XGBoost': XGBRegressor(n_estimators=180, max_depth=4, learning_rate=.05, reg_lambda=10,
                               subsample=.9, colsample_bytree=.9, n_jobs=2, random_state=SEED),
        'LightGBM': LGBMRegressor(n_estimators=180, num_leaves=15, learning_rate=.05,
                                 min_child_samples=25, reg_lambda=5, verbosity=-1,
                                 n_jobs=2, random_state=SEED),
    }


def preprocessing(features):
    check_features(features)
    numeric = [c for c in features if c not in CATEGORICAL]
    return ColumnTransformer([
        ('numeric', Pipeline([('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
                              ('scale', StandardScaler())]), numeric),
        ('categorical', Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                                  ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]),
         [c for c in features if c in CATEGORICAL]),
    ], verbose_feature_names_out=False)


def reg_pipeline(model, features):
    return TransformedTargetRegressor(regressor=Pipeline([
        ('preprocess', preprocessing(features)), ('model', clone(model))]),
        func=np.log1p, inverse_func=np.expm1, check_inverse=True)


def metrics(y, pred):
    return {'mae': mean_absolute_error(y, pred), 'rmse': np.sqrt(mean_squared_error(y, pred)),
            'r2': r2_score(y, pred), 'median_absolute_error': median_absolute_error(y, pred),
            'median_absolute_percentage_error': float(np.median(np.abs((y-pred)/y))*100), 'n': len(y)}


def group_ids(frame):
    # Shared address OR near-identical coordinates must stay together (connected components).
    parents = list(range(len(frame)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    for i, row in enumerate(frame.itertuples()):
        keys = [('address', row.address_group)]
        if np.isfinite(row.latitude) and np.isfinite(row.longitude):
            keys.append(('coordinate_cell', round(row.latitude, 3), round(row.longitude, 3)))
        for key in keys:
            if key in seen:
                parents[find(i)] = find(seen[key])
            else:
                seen[key] = i
    return np.array([str(find(i)) for i in range(len(frame))])


def run_regression(frame, root):
    # Same complete market-feature cohort for A/B; missing-cohort exclusions are reported.
    eligible = frame[MARKET].notna().all(axis=1)
    frame = frame.loc[eligible].reset_index(drop=True).copy()
    groups = group_ids(frame)
    trainval, test = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=SEED).split(frame, groups=groups))
    inner_train, inner_val = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=SEED+1).split(
        frame.iloc[trainval], groups=groups[trainval]))
    train, val = trainval[inner_train], trainval[inner_val]
    fold = np.full(len(frame), 'test', dtype=object)
    fold[train], fold[val] = 'train', 'validation'
    frame['partition'] = fold
    pd.DataFrame({'property_id': frame.property_id, 'group': groups, 'partition': fold}).to_csv(
        root / 'artifacts/evaluation/splits.csv', index=False)
    results, candidates = [], {}
    models = regression_models()
    cv = GroupKFold(n_splits=3)
    for experiment, features in [('A: property only', NUMERIC+CATEGORICAL),
                                  ('B: property + historical ZHVI', NUMERIC+CATEGORICAL+MARKET)]:
        x, y = frame[features], frame.price
        for name, model in models.items():
            pipe = reg_pipeline(model, features)
            scores = -cross_val_score(pipe, x.iloc[train], y.iloc[train], groups=groups[train],
                                     cv=cv, scoring='neg_mean_absolute_error', n_jobs=1)
            pipe.fit(x.iloc[train], y.iloc[train])
            pred = pipe.predict(x.iloc[val])
            results.append({'experiment': experiment, 'model': name, 'cv_mae': scores.mean(),
                            'cv_mae_std': scores.std(), 'validation_mae': mean_absolute_error(y.iloc[val], pred)})
            candidates[(experiment, name)] = (pipe, features)
            print(f'{experiment} / {name}: CV MAE ${scores.mean():,.0f}', flush=True)
    comparison = pd.DataFrame(results)
    best = comparison.sort_values(['cv_mae', 'model']).iloc[0]
    key = (best.experiment, best.model)
    selected, features = candidates[key]
    # Selection is locked using training CV before inspecting final test outcomes.
    selection = {'experiment': best.experiment, 'model': best.model, 'selection_metric': 'training grouped CV MAE',
                 'cv_mae': float(best.cv_mae), 'features': features}
    (root / 'artifacts/evaluation/regression_selection.json').write_text(json.dumps(selection, indent=2))
    for row in results:
        pipe, cols = candidates[(row['experiment'], row['model'])]
        t = perf_counter()
        pred = pipe.predict(frame.iloc[test][cols])
        row.update({'test_' + k: v for k, v in metrics(frame.price.iloc[test], pred).items()})
        row['milliseconds_per_prediction'] = (perf_counter()-t)*1000/len(test)
    pd.DataFrame(results).to_csv(root / 'artifacts/evaluation/regression_comparison.csv', index=False)
    baseline = DummyRegressor(strategy='median').fit(frame.iloc[train][features], frame.price.iloc[train])
    baseline_metrics = metrics(frame.price.iloc[test], baseline.predict(frame.iloc[test][features]))
    # Independent validation set calibrates empirical absolute-dollar screening uncertainty.
    val_pred = selected.predict(frame.iloc[val][features])
    radius = float(np.quantile(np.abs(frame.price.iloc[val]-val_pred), .9, method='higher'))
    test_pred = selected.predict(frame.iloc[test][features])
    test_metrics = metrics(frame.price.iloc[test], test_pred)
    coverage = float(np.mean(np.abs(frame.price.iloc[test]-test_pred) <= radius))
    # Nested cross-fitting: the held-out training fold is absent from both model selection and fitting.
    oof = np.full(len(train), np.nan)
    for outer, (fit, held) in enumerate(cv.split(frame.iloc[train], groups=groups[train]), 1):
        fit_ids, held_ids = train[fit], train[held]
        choices = []
        for feature_label, fold_features in [('A', NUMERIC+CATEGORICAL), ('B', NUMERIC+CATEGORICAL+MARKET)]:
            for name, model in models.items():
                pipe = reg_pipeline(model, fold_features)
                score = -cross_val_score(pipe, frame.iloc[fit_ids][fold_features], frame.price.iloc[fit_ids],
                                        groups=groups[fit_ids], cv=GroupKFold(2),
                                        scoring='neg_mean_absolute_error').mean()
                choices.append((score, name, feature_label))
        _, name, feature_label = min(choices)
        fold_features = NUMERIC+CATEGORICAL+(MARKET if feature_label == 'B' else [])
        pipe = reg_pipeline(models[name], fold_features).fit(frame.iloc[fit_ids][fold_features], frame.price.iloc[fit_ids])
        oof[held] = pipe.predict(frame.iloc[held_ids][fold_features])
        print(f'Nested OOF fold {outer}/3: {name}', flush=True)
    estimates = np.full(len(frame), np.nan)
    estimates[train], estimates[val], estimates[test] = oof, val_pred, test_pred
    if not np.isfinite(estimates).all() or (estimates <= 0).any():
        raise ValueError('Invalid out-of-sample price predictions')
    frame['estimated_price'] = estimates
    frame['estimate_lower'] = np.maximum(0, estimates-radius)
    frame['estimate_upper'] = estimates+radius
    frame['pricing_gap'] = frame.price / frame.estimated_price - 1
    frame['pricing_category'] = frame.pricing_gap.map(pricing_category)
    frame['market_adjusted_value'] = frame.estimated_price * frame.latest_zhvi / frame.historical_zhvi
    frame['estimate_method'] = np.where(frame.partition.eq('train'), 'Nested out-of-fold regressor', str(best.model))
    frame.to_parquet(root / 'artifacts/predictions/properties.parquet', index=False)
    # Keep the evaluated model trained only on training partition; artifact validation is reproducible.
    joblib.dump({'pipeline': selected, 'features': features, 'selection': selection, 'radius_90': radius},
                root / 'artifacts/models/price_pipeline.joblib')
    errors = frame.iloc[test].copy()
    errors['abs_error'] = (errors.price-errors.estimated_price).abs()
    errors.groupby('zip_code').agg(n=('price','size'), mae=('abs_error','mean')).to_csv(root / 'artifacts/evaluation/error_by_zip.csv')
    errors['price_range'] = pd.cut(errors.price, [0,250000,500000,1000000,np.inf])
    errors.groupby('price_range', observed=True).agg(n=('price','size'),mae=('abs_error','mean')).to_csv(
        root / 'artifacts/evaluation/error_by_price.csv')
    # Additional geographic extrapolation stress test restricted to original training data.
    geo_train, geo_test = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=SEED).split(
        frame.iloc[train], groups=frame.iloc[train].zip_code))
    geo_pipe = clone(selected).fit(frame.iloc[train[geo_train]][features], frame.price.iloc[train[geo_train]])
    geo_metrics = metrics(frame.price.iloc[train[geo_test]], geo_pipe.predict(frame.iloc[train[geo_test]][features]))
    report = {'selection': selection, 'eligible_rows': len(frame), 'excluded_missing_market_rows': int((~eligible).sum()),
              'partitions': frame.partition.value_counts().to_dict(), 'test': test_metrics,
              'median_baseline_test': baseline_metrics, 'zip_holdout_training_stress_test': geo_metrics,
              'empirical_90_interval_radius_dollars': radius, 'test_interval_coverage': coverage,
              'uncertainty_limit': 'Validation absolute residual quantile; global, empirical, not an appraisal interval. OOF models differ from calibrated model.',
              'grouping': 'Connected address / rounded 0.001-degree coordinate groups; residual spatial dependence remains',
              'fixed_budget': 'Fixed hyperparameters, 3 grouped CV folds; no exhaustive search',
              'pseudo_label_limit': 'Outer-fold model family and feature set selected on inner folds; labels remain screening proxies, not independent mispricing truth'}
    return frame, report


def run_classification(frame, root):
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier
    features = NUMERIC + CATEGORICAL + MARKET  # deliberately exclude asking price, prediction and exact gap
    encoder = LabelEncoder().fit(frame.pricing_category)
    y = encoder.transform(frame.pricing_category)
    train = frame.partition.eq('train').to_numpy()
    val = frame.partition.eq('validation').to_numpy()
    test = frame.partition.eq('test').to_numpy()
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1500, class_weight='balanced', random_state=SEED),
        'Random Forest': RandomForestClassifier(n_estimators=120, min_samples_leaf=4, class_weight='balanced', n_jobs=2, random_state=SEED),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=80, max_depth=2, random_state=SEED),
        'XGBoost': XGBClassifier(n_estimators=100, max_depth=3, n_jobs=2, random_state=SEED),
        'LightGBM': LGBMClassifier(n_estimators=100, num_leaves=15, verbosity=-1, n_jobs=2, random_state=SEED),
    }
    results, fitted = [], {}
    for name, model in models.items():
        pipe = Pipeline([('preprocess', preprocessing(features)), ('model', model)])
        pipe.fit(frame.loc[train, features], y[train])
        pred = pipe.predict(frame.loc[val, features])
        results.append({'model': name, 'validation_macro_f1': f1_score(y[val],pred,average='macro',zero_division=0)})
        fitted[name] = pipe
    winner = max(results, key=lambda r:r['validation_macro_f1'])['model']
    details = {}
    for row in results:
        pred = fitted[row['model']].predict(frame.loc[test, features])
        row.update(test_accuracy=accuracy_score(y[test],pred), test_macro_f1=f1_score(y[test],pred,average='macro',zero_division=0))
        details[row['model']] = {'per_class': classification_report(y[test],pred,labels=np.arange(len(encoder.classes_)),
                target_names=encoder.classes_,output_dict=True,zero_division=0),
                'confusion_matrix': confusion_matrix(y[test],pred,labels=np.arange(len(encoder.classes_))).tolist()}
    pd.DataFrame(results).to_csv(root / 'artifacts/evaluation/classification_comparison.csv', index=False)
    return {'winner_for_pseudo_label_reproduction': winner, 'production_method': 'Deterministic pricing gap rule',
            'class_names': encoder.classes_.tolist(), 'class_distribution': frame.pricing_category.value_counts().to_dict(),
            'details': details, 'reference_rule': 'Exact label definition; 100% agreement is tautological, not independent accuracy',
            'interpretation': 'Evaluates reproduction of cross-fitted model residual categories, not real market mispricing.'}
