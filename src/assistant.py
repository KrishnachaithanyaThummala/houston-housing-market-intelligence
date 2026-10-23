"""Deterministic, record-grounded Q&A fallback: no external service or fabricated facts."""
import re
import numpy as np
import pandas as pd

DISCLAIMER = 'Pricing categories are model-based screening indicators, not verified market valuations or guaranteed investment opportunities.'


def answer(question, property_row=None, forecast=None, regression_report=None):
    q = question.lower().strip()
    if not q:
        return 'Ask a question about the selected historical property or ZIP forecast.'
    if any(s in q for s in ['ignore previous', 'system prompt', 'guaranteed profit', 'buy now', 'investment advice']):
        return 'I can explain recorded data and model outputs. I cannot verify investment opportunities or guarantee returns.'
    if any(s in q for s in ['school', 'crime', 'flood', 'owner', 'agent', 'commute', 'mortgage', 'race', 'ethnic']):
        return 'That information is unavailable in the approved application data. I will not infer it.'
    row = property_row
    # Prevent accidental answers about an ID other than the selected record.
    ids = re.findall(r'\b\d{6,}\b', q)
    zips = re.findall(r'\b\d{5}\b', q)
    if row is not None and (any(i != str(row['property_id']) for i in ids)
                            or any(z != str(row['zip_code']) for z in zips)):
        return 'That identifier does not match the selected property. Select the matching record first.'
    source = f" Source: historical property {row['property_id']}, snapshot {row['snapshot_date']}." if row is not None else ''
    if any(s in q for s in ['limitations', 'reliable', 'uncertainty', 'accuracy']):
        extra = ''
        if regression_report:
            extra = f" The selected regressor's held-out MAE is ${regression_report['test']['mae']:,.0f}."
        return ('These are historical asking-price estimates, not appraisals or live inventory. '
                'ZHVI is a modeled ZIP-level index. Revised historical values and residual spatial dependence limit validation.'
                + extra + ' Forecast intervals are empirical and future coverage is not guaranteed.')
    if any(s in q for s in ['forecast', 'next 12', 'next 6', 'trend', 'zhvi']):
        if forecast is None or len(forecast) == 0:
            return 'A forecast is unavailable for the selected ZIP.'
        h = 6 if re.search(r'\b6\b', q) else 12
        match = forecast.loc[forecast.horizon.eq(h)]
        if match.empty:
            return f'The {h}-month forecast is unavailable.'
        f = match.iloc[0]
        return (f"ZIP {f.zip_code}: {f.method} forecasts ZHVI of ${f.prediction:,.0f} for {pd.Timestamp(f.date):%B %Y} "
                f"({(f.prediction/f.latest_zhvi-1)*100:+.1f}% relative to the latest observation). "
                f"Empirical interval: ${f.lower:,.0f}–${f.upper:,.0f}. This is a ZIP index, not a property sale-price forecast. "
                'Source: saved forecast artifact; origin September 2026.')
    if row is None:
        return 'Select a historical property before asking about property-specific details.'
    if any(s in q for s in ['bedroom', 'bathroom', 'bed', 'bath']):
        bed = 'unavailable' if pd.isna(row['bedrooms']) else f"{row['bedrooms']:g}"
        return f"The selected property has {bed} bedrooms and {row['bathrooms']:g} bathrooms." + source
    if 'zip' in q:
        return f"The selected property's ZIP code is {row['zip_code']}." + source
    if any(s in q for s in ['square', 'size', 'area']):
        return f"Recorded living area is {row['living_area']:,.0f} square feet." + source
    if any(s in q for s in ['overpriced', 'underpriced', 'fairly', 'category', 'gap', 'why flagged']):
        return (f"{row['pricing_category']}: the historical asking price (${row['price']:,.0f}) is "
                f"{row['pricing_gap']*100:+.1f}% relative to the out-of-sample estimate (${row['estimated_price']:,.0f}). "
                'Categories use configurable ±10% thresholds by default. ' + DISCLAIMER + source)
    if any(s in q for s in ['current', 'adjusted', 'today', 'live', 'available']):
        return (f"The approximate ZIP-index-adjusted estimate is ${row['market_adjusted_value']:,.0f}, using "
                f"{row['zhvi_reference_date']} and {row['latest_zhvi_date']} ZHVI. It is not a current listing price, "
                'appraisal or evidence this home is available.' + source)
    if any(s in q for s in ['estimate', 'fair value', 'valuation']):
        return (f"The historical model estimate is ${row['estimated_price']:,.0f}. It estimates historical asking price, "
                'not independently verified fair market value.' + source)
    if any(s in q for s in ['price', 'asking', 'listing']):
        return f"The historical asking price was ${row['price']:,.0f}; this is not a live listing price." + source
    if any(s in q for s in ['feature', 'influence', 'shap']):
        return ('Open the property explanation panel for SHAP contributions from the trained model. '
                'Contributions describe model behavior on the log-price scale; they do not establish causation.')
    return 'I cannot answer that from the approved records. Ask about price, size, bedrooms, ZIP, pricing gap, forecast or limitations.'
