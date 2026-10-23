"""Explanations from actual fitted pipelines; log-target units are explicit."""
import numpy as np
import pandas as pd


def explain_property(bundle, row):
    import shap
    pipe = bundle['pipeline'].regressor_
    transformed = pipe['preprocess'].transform(row[bundle['features']])
    names = pipe['preprocess'].get_feature_names_out()
    model = pipe['model']
    if hasattr(model, 'coef_'):
        # SHAP LinearExplainer requires a training background; ridge support is intentionally explicit.
        raise ValueError('Linear SHAP background unavailable; do not substitute coefficients for SHAP.')
    explainer = shap.TreeExplainer(model)
    values = np.asarray(explainer.shap_values(transformed, check_additivity=False))[0]
    baseline = float(np.asarray(explainer.expected_value).reshape(-1)[0])
    actual_log_prediction = float(model.predict(transformed)[0])
    if not np.isclose(baseline + values.sum(), actual_log_prediction, atol=1e-4):
        raise ValueError('SHAP additivity check failed')
    return pd.DataFrame({'feature': names, 'contribution': values}).assign(
        absolute=lambda x: x.contribution.abs()).sort_values('absolute', ascending=False), baseline
