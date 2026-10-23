from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import pytest
from src.data import normalize_zip, pricing_category, check_features, integrate, MARKET, historical_market
from src.forecasting import predict_path
from src.assistant import answer

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('value,expected', [('77004-1234','77004'),('01234','01234'),(1234,'01234'),
    ('77004.0','77004'),(None,None),('bad',None),('770041',None)])
def test_zip(value,expected):
    assert normalize_zip(value)==expected


def test_gap_boundaries():
    assert pricing_category(-.10001)=='Potentially Underpriced'
    assert pricing_category(-.1)=='Approximately Fairly Priced'
    assert pricing_category(.1)=='Approximately Fairly Priced'
    assert pricing_category(.10001)=='Potentially Overpriced'
    assert pricing_category(np.nan)=='Unavailable'
    with pytest.raises(ValueError): pricing_category(0,0)


def test_feature_leakage():
    for col in ['zestimate','price','pricePerSquareFoot','unknown_feature']:
        with pytest.raises(ValueError): check_features(['bedrooms',col])


def test_duplicate_join_rejected():
    left=pd.DataFrame({'zip_code':['77004','77004']})
    right=pd.DataFrame({'zip_code':['77004','77004']})
    with pytest.raises(pd.errors.MergeError): integrate(left,right)


def test_actual_join_cardinality():
    report=json.loads((ROOT/'artifacts/evaluation/integration_audit.json').read_text())
    data=pd.read_parquet(ROOT/'data/processed/integrated.parquet')
    assert report['before']==report['after']==len(data)
    assert data.property_id.is_unique
    assert len(report['unmatched_zip_codes'])==2


def test_geographic_filter():
    meta=pd.read_parquet(ROOT/'data/processed/zip_metadata.parquet')
    assert meta.State.eq('TX').all()
    assert set(meta.City)=={'Houston','South Houston'}
    assert meta.zip_code.str.fullmatch(r'\d{5}').all()
    assert len(meta)==98


def test_historical_features_do_not_read_future():
    history=pd.read_parquet(ROOT/'data/processed/zhvi.parquet')
    original=historical_market(history)
    altered=history.copy()
    altered.loc[altered.date.gt('2024-04-30'),'zhvi_value'] *= 100
    changed=historical_market(altered)
    pd.testing.assert_frame_equal(original[['zip_code']+MARKET],changed[['zip_code']+MARKET])


def test_split_groups_disjoint():
    split=pd.read_csv(ROOT/'artifacts/evaluation/splits.csv')
    assert split.groupby('group').partition.nunique().eq(1).all()
    assert split.property_id.is_unique
    assert set(split.partition)=={'train','validation','test'}


def test_serving_model_reproduces_test_predictions():
    bundle=joblib.load(ROOT/'artifacts/models/price_pipeline.joblib')
    props=pd.read_parquet(ROOT/'artifacts/predictions/properties.parquet')
    sample=props.loc[props.partition.eq('test')].head(12)
    pred=bundle['pipeline'].predict(sample[bundle['features']])
    np.testing.assert_allclose(pred,sample.estimated_price,rtol=1e-6)


def test_naive_horizon_and_gap_rejection():
    values=np.linspace(100000,200000,80)
    assert np.array_equal(predict_path(values,'Naive'),np.repeat(200000,12))
    values[10]=np.nan
    with pytest.raises(ValueError): predict_path(values,'Naive')


def test_forecast_artifacts_and_dates():
    f=pd.read_parquet(ROOT/'artifacts/forecasts/forecasts.parquet')
    assert f.groupby('zip_code').horizon.apply(lambda s:set(s)==set(range(1,13))).all()
    assert f.date.min()==pd.Timestamp('2026-10-31')
    assert f.date.max()==pd.Timestamp('2027-09-30')
    assert (f.lower<=f.prediction).all() and (f.prediction<=f.upper).all()
    assert not f.duplicated(['zip_code','horizon']).any()


def test_forecast_origins_and_all_methods():
    back=pd.read_parquet(ROOT/'artifacts/forecasts/backtests.parquet')
    assert back.method.nunique()==5
    assert (pd.to_datetime(back.origin)<back.date).all()
    assert set(back.phase)=={'selection','calibration','test'}


def test_chatbot_grounding_and_identity():
    prop=pd.read_parquet(ROOT/'artifacts/predictions/properties.parquet').iloc[0].to_dict()
    assert f"${prop['price']:,.0f}" in answer('historical listing price',prop)
    assert 'unavailable' in answer('What is the flood risk?',prop)
    assert 'does not match' in answer('What about property 999999999999?',prop)
    assert 'unavailable' in answer('forecast',prop,pd.DataFrame())


def test_actual_shap_additivity():
    from src.explain import explain_property
    bundle=joblib.load(ROOT/'artifacts/models/price_pipeline.joblib')
    props=pd.read_parquet(ROOT/'artifacts/predictions/properties.parquet')
    row=props.loc[props.partition.eq('test')].head(1)
    effects,base=explain_property(bundle,row)
    assert np.isclose(np.expm1(base+effects.contribution.sum()),row.estimated_price.iloc[0],rtol=1e-5)


def test_map_geometry_validity():
    from shapely.geometry import shape
    doc=json.loads((ROOT/'data/geographic/houston_zcta.geojson').read_text())
    assert len(doc['features'])==98
    for f in doc['features']:
        geom=shape(f['geometry'])
        assert geom.is_valid and not geom.is_empty
        minx,miny,maxx,maxy=geom.bounds
        assert -180<=minx<=maxx<=180 and -90<=miny<=maxy<=90
