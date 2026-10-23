"""Generate reports, buyer charts and fixed-ground-truth assistant checks from real artifacts."""
import json
import sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.assistant import answer

root=Path(__file__).resolve().parents[1]
out=root/'reports'
(out/'charts').mkdir(exist_ok=True)
def read(name): return json.loads((root/'artifacts/evaluation'/name).read_text())
def write(name,text): (out/name).write_text(text.replace('$',r'\$'))
def table(frame): return frame.to_markdown(index=False,floatfmt='.3f')
props=pd.read_parquet(root/'artifacts/predictions/properties.parquet')
raw=pd.read_parquet(root/'data/processed/integrated.parquet')
history=pd.read_parquet(root/'data/processed/zhvi.parquet')
future=pd.read_parquet(root/'artifacts/forecasts/forecasts.parquet')
listing,zhvi,join,reg,cls,forecast=(read(x) for x in ['listings_audit.json','zhvi_audit.json',
    'integration_audit.json','regression_report.json','classification_report.json','forecast_report.json'])
reg_table=pd.read_csv(root/'artifacts/evaluation/regression_comparison.csv')
cls_table=pd.read_csv(root/'artifacts/evaluation/classification_comparison.csv')
fc_table=pd.read_csv(root/'artifacts/evaluation/forecast_comparison.csv')

write('dataset_report.md',f'''# Dataset audit

Listings: Natasha Lekh / datadetective08, [Houston housing market 2024](https://www.kaggle.com/datasets/datadetective08/houston-housing-market-2024), version 1, CC BY-NC-SA 4.0. Downloaded only the light JSON. Exact raw count: {listing['raw_rows']:,}. No repeated property IDs. Publisher identifies June 5, 2024 as the snapshot; this is not each property's listing start date.

Texas and requested city-label scope: {listing['city_scope_rows']:,} records. Single-family, condo and townhouse subset: {listing['residential_rows']:,}. Invalid price/ZIP/living-area rows removed: {listing['invalid_price_zip_or_area_rows']}. Two additional residential prices below $20,000 were excluded as ambiguous sale-price entries; they are not asserted to be rentals. Clean residential records: {listing['clean_rows']:,}.

Year built is absent from the light file; no property-age feature was invented. Lot values are converted from acres to square feet only when source units are known. Missing lot area: {listing['missing_predictors']['lot_area_sqft']:,}; missing bedrooms: {listing['missing_predictors']['bedrooms']}. Missing predictors are imputed inside model folds. Tax assessments, Zestimates, rent estimates, prices and price changes are excluded from predictor construction. Full flattened schema and exclusion list: artifacts/evaluation/listings_audit.json.

ZHVI: {zhvi['source_rows']:,} national rows; {zhvi['monthly_columns']} months ({zhvi['first_month']}–{zhvi['last_month']}). Selected Texas city labels yield {zhvi['selected_zips']} unique ZIPs (Houston 97, South Houston 1). Houstonia exists only in Missouri in the supplied file and is excluded. Initial missing monthly observations: {zhvi['missing_monthly_values']}; none are silently filled. Every selected ZIP has the last month. City labels are not city boundaries or the full metro.

The source filename describes mid-tier smoothed seasonally adjusted SFR/condo values. [Zillow Research](https://www.zillow.com/research/data/) describes ZHVI as a modeled typical-home-value index. The source download date is unknown; inspection occurred October 23, 2026. Exact hashes and metadata are stored in artifacts/evaluation.
''')
write('dataset_integration_report.md',f'''# Dataset integration

- Listings before/after left join: {join['before']:,} / {join['after']:,}.
- Unique listing ZIPs / ZHVI ZIPs: {join['listing_zips']} / {join['zhvi_zips']}.
- Matched ZIP codes: {len(join['matched_zip_codes'])}.
- Matched listing rows: {join['matched_listing_rows']:,} ({join['matched_listing_fraction']:.2%}).
- Unmatched ZIPs: {', '.join(join['unmatched_zip_codes'])}; {join['before']-join['matched_listing_rows']} rows.
- Duplicate ZHVI ZIP keys: zero. Merge explicitly validates many-to-one cardinality.

Integrated rows remain in data/processed/integrated.parquet. The common A/B modeling cohort excludes the 36 unmatched rows, producing {reg['eligible_rows']:,} records. The app serves validation/test examples from that cohort, not unmatched or in-sample training estimates.

Historical feature date: April 30, 2024, before the June 5 snapshot, with 6/12-month changes. Latest September 2026 ZHVI is retained for display/adjustment only and is never a historical price predictor. The conservative lag does not establish 2024 release availability: this is a later revised vintage of ZHVI. Historical backtests are retrospective.
''')
write('price_prediction_results.md',f'''# Historical asking-price prediction

Selected using grouped training-only CV MAE: **{reg['selection']['model']}**, **{reg['selection']['experiment']}**. Fixed modest configurations and 3 folds; no exhaustive hyperparameter search. Both experiments share the same eligible records and persisted splits. All preprocessing is fit within folds. Log1p targets are inverse-transformed before dollar evaluation.

Partitions: {reg['partitions']}. Address/rounded coordinate connected groups prevent direct duplicate/near-coordinate overlap. This cannot eliminate all spatial dependence. Training-only ZIP holdout stress-test MAE: ${reg['zip_holdout_training_stress_test']['mae']:,.2f} on {reg['zip_holdout_training_stress_test']['n']} cases; its distribution differs from the final test.

{table(reg_table)}

Selected model test MAE: **${reg['test']['mae']:,.2f}**, RMSE **${reg['test']['rmse']:,.2f}**, R² **{reg['test']['r2']:.4f}**, median absolute error **${reg['test']['median_absolute_error']:,.2f}**. Median absolute percentage error: **{reg['test']['median_absolute_percentage_error']:.2f}%**. Median-price baseline MAE: **${reg['median_baseline_test']['mae']:,.2f}**. R² is not accuracy.

Some alternatives have lower final test MAE. We keep the earlier CV selection rather than reselecting on test results. Ridge's large test errors show instability after inverse-transforming extrapolated log predictions; all measured results remain visible.

Validation residual 90th-percentile radius: ${reg['empirical_90_interval_radius_dollars']:,.2f}. Held-out empirical coverage: {reg['test_interval_coverage']:.2%}, below the 90% target. This broad global band is not a formal appraisal interval. Training examples use nested cross-fitting and may use a different fold-selected model; the app shows held-out records so its SHAP explanation matches the displayed estimate.

Model predicts historical asking prices, not independently measured fair market value. Dataset vintage, listing-price target, outliers and shared Zillow provenance limit interpretation.
''')
write('classification_results.md',f'''# Pricing-gap pseudo-label evaluation

Production uses a configurable gap rule: (asking price − out-of-sample estimate) / estimate. Less than −10% is Potentially Underpriced, greater than +10% is Potentially Overpriced, and boundaries are included in Approximately Fairly Priced.

Training labels use 3 outer folds, with model family and feature set chosen on inner folds that omit each outer held-out record. Validation/test estimates come from the training-only selected regressor. These are pseudo-labels; none establish true bargains or market mispricing.

Classifier predictors exclude asking price, exact gap and regression estimate to avoid trivial formula reproduction. Selection uses validation macro F1, then frozen test evaluation. Selected reproduction model: {cls['winner_for_pseudo_label_reproduction']}. Class counts: {cls['class_distribution']}.

{table(cls_table)}

Full precision/recall/F1 and confusion matrices are saved in artifacts/evaluation/classification_report.json. The deterministic rule agrees with its own labels by definition; treating that agreement as independent 100% accuracy would be misleading. The auxiliary classifier is not used to override the production rule.
''')
write('forecasting_results.md',f'''# ZIP-level ZHVI forecasts

Methods actually executed: {', '.join(forecast['methods_requested'])}. Failed ZIP/method/origin runs: {len(forecast['failures'])}. Forecasts exist for {forecast['future_zip_count']} ZIPs.

Origins: {forecast['origins']}. Every origin uses only earlier observations. Initial gaps are trimmed; internal gaps restart contiguous training history. Minimum history is 60 months. Selection uses mean absolute error at months 6 and 12 across ZIPs and two earlier origins. One separate origin calibrates relative-error bands; the last origin is held out for evaluation. Comparisons use common cases, not favorable subsets. Hyperparameters are modest and fixed, not exhaustively tuned. Seasonality is disabled in Prophet for this seasonally adjusted series; ARIMA uses (1,1,0) with drift; lag XGBoost recursively predicts log returns.

Selected method: **{forecast['winner']}**. Its flat forecast is a measured baseline result. Some alternatives do better in the final held-out period; that does not justify changing selection using the test outcome.

{table(fc_table)}

Intervals: {forecast['interval_method']}. Coverage: 6 months {forecast['test_interval_coverage_by_horizon']['6']:.2%}; 12 months {forecast['test_interval_coverage_by_horizon']['12']:.2%}. Target is 90%; spatial dependence among ZIPs and time-varying errors limit calibration. These are empirical forecast bands, not invented confidence bounds. Full monthly backtests are stored separately from endpoint summaries.

Future observations run October 2026–September 2027. Forecasts describe ZIP-level modeled home values, not future sale prices of individual houses. All historical evaluations use the supplied revised ZHVI vintage and cannot verify real-time historical performance.
''')

# Fixed, independently derived expected facts; include identity, numerical and refusal cases.
checks=[]
sample=props.loc[props.partition.eq('test')].sort_values('property_id').head(6)
for _,row in sample.iterrows():
    r=row.to_dict(); f=future.loc[future.zip_code.eq(row.zip_code)]
    cases=[('What is the historical listing price?',f"${row.price:,.0f}"),
           ('What is the model estimate?',f"${row.estimated_price:,.0f}"),
           ('What is the ZIP code?',row.zip_code),
           ('How many bedrooms and bathrooms?',f'{row.bathrooms:g} bathrooms'),
           ('What is the living area?',f'{row.living_area:,.0f}'),
           ('Why is it overpriced?',f'{row.pricing_gap*100:+.1f}%'),
           ('What is its flood risk?','unavailable'),
           ('What about property 999999999999?','does not match'),
           ('What is the 12 month forecast?',f"${f.loc[f.horizon.eq(12)].iloc[0].prediction:,.0f}"),
           ('Is it currently available?','not a current listing price')]
    for question,expected in cases:
        t=perf_counter(); response=answer(question,r,f,reg); elapsed=perf_counter()-t
        checks.append({'property_id':row.property_id,'question':question,'expected_substring':expected,
                       'response':response,'passed':str(expected) in response,'seconds':elapsed})
pd.DataFrame(checks).to_json(root/'artifacts/evaluation/chatbot_cases.json',orient='records',indent=2)
assistant_report={'configuration':'Deterministic tool-grounded templates', 'configurations_tested':1,
    'cases':len(checks),'passed':sum(c['passed'] for c in checks),
    'exact_expected_fact_pass_rate':sum(c['passed'] for c in checks)/len(checks),
    'mean_latency_seconds':np.mean([c['seconds'] for c in checks]),'external_api_cost':0,
    'limits':'Fixed phrasing and expected substrings; not a broad natural-language or generative-LLM evaluation.',
    'not_evaluated':['Local LLM','Hosted tool-grounded LLM','RAG LLM','Alternative grounded LLM configuration']}
(root/'artifacts/evaluation/chatbot_evaluation.json').write_text(json.dumps(assistant_report,indent=2))
write('chatbot_evaluation.md',f'''# Grounded assistant evaluation

One deterministic configuration tested on {len(checks)} fixed questions across six held-out properties. Exact expected-fact checks passed: {assistant_report['passed']}/{len(checks)}. Mean measured local response latency: {assistant_report['mean_latency_seconds']:.6f} seconds. External API cost: $0. Cases include property identity mismatch, missing flood data, bedroom/bathroom attributes, prices, forecasts and current-availability distinctions.

Question set, expected values, full responses and timings: artifacts/evaluation/chatbot_cases.json. Matching expected substrings is a narrow factual test, not evidence of unrestricted conversational competence. No LLM credentials were supplied or paid calls made. The four LLM configurations in the full prompt remain unevaluated. Do not claim a five-chatbot comparison.
''')

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained')
ax[0,0].hist(np.log10(raw.price),bins=45,color='#15394b');ax[0,0].set(xlabel='log10 historical asking price ($)',ylabel='Properties',title='A long upper price tail')
ax[0,1].scatter(raw.living_area,raw.price,s=5,alpha=.25,color='#0d9488');ax[0,1].set(xscale='log',yscale='log',xlabel='Living area (sq ft)',ylabel='Historical asking price ($)',title='Size and asking price')
raw.property_type.value_counts().plot.bar(ax=ax[1,0],color='#15394b',rot=0);ax[1,0].set(title='Residential study cohort',ylabel='Properties',xlabel='Property type')
wide=history.pivot(index='date',columns='zip_code',values='zhvi_value')
wide.median(axis=1).plot(ax=ax[1,1],color='#0d9488');ax[1,1].set(title='Unweighted median across 98 ZIP indices',ylabel='ZHVI ($)',xlabel='Month')
fig.savefig(out/'charts/eda_overview.png',dpi=160);plt.close(fig)
test=props.loc[props.partition.eq('test')]
fig,ax=plt.subplots(1,2,figsize=(12,4),layout='constrained')
ax[0].scatter(test.price,test.estimated_price,s=7,alpha=.35,color='#15394b')
lo,hi=min(test.price.min(),test.estimated_price.min()),max(test.price.max(),test.estimated_price.max())
ax[0].plot([lo,hi],[lo,hi],color='#0d9488');ax[0].set(xscale='log',yscale='log',xlabel='Actual historical asking price ($)',ylabel='Predicted price ($)',title='Selected model: held-out properties')
ax[1].hist(test.price-test.estimated_price,bins=70,color='#15394b');ax[1].set(xlabel='Actual − predicted ($)',ylabel='Properties',title='Test residuals (full range)')
fig.savefig(out/'charts/regression_diagnostics.png',dpi=160);plt.close(fig)
latest=wide.iloc[-1]; yearly=(latest/wide.iloc[-13]-1)*100
correlation=raw[['price','living_area','bedrooms','bathrooms']].corr(method='spearman')
write('eda_report.md',f'''# Exploratory analysis

![Price, property type, size and history](charts/eda_overview.png)

The clean residential cohort contains {len(raw):,} historical examples. Median asking price is ${raw.price.median():,.0f}; the middle half spans ${raw.price.quantile(.25):,.0f}–${raw.price.quantile(.75):,.0f}. Maximum ${raw.price.max():,.0f} indicates a strong upper tail. No percentile trimming was applied to hide difficult expensive examples. Log-target modeling addresses scale but does not remove outliers.

Spearman associations with price: living area {correlation.loc['price','living_area']:.3f}; bedrooms {correlation.loc['price','bedrooms']:.3f}; bathrooms {correlation.loc['price','bathrooms']:.3f}. Associations are not causal effects. Missing lot area is handled inside modeling folds; no year-built distribution is available in this file. City filtering excludes broader-metro listings rather than silently expanding scope.

Latest year-over-year ZIP ZHVI changes: median {yearly.median():+.2f}%, minimum {yearly.min():+.2f}%, maximum {yearly.max():+.2f}%. These are ZIP-level modeled values, not realized property returns. The plotted median across ZIPs is an unweighted summary, not an official citywide Zillow index.

ZIP-level listing counts/median prices, missingness, coordinate coverage and model errors are available in the dashboard and saved audit tables. Geographic validation independently reports ZIP/ZCTA mismatches and excludes outside-region map points.

![Held-out diagnostics](charts/regression_diagnostics.png)
''')
write('final_model_comparison.md',f'''# Final model comparison and current status

- Regression: five model families × two feature sets evaluated; selected {reg['selection']['model']}, held-out MAE ${reg['test']['mae']:,.2f}. Selection uses training CV, not the test leaderboard.
- Classification: five models evaluated for pseudo-label reproduction; selected {cls['winner_for_pseudo_label_reproduction']}. Production remains the deterministic gap rule.
- Forecasting: five methods evaluated at four origins for 98 ZIPs; selected {forecast['winner']} using earlier origins. All 12 future months exported.
- Assistant: one deterministic grounded configuration, {assistant_report['passed']}/{len(checks)} narrow fixed checks. Four LLM configurations remain unevaluated.
- SHAP: actual selected-model TreeExplainer with additivity check; log-target contributions.
- Map: 98 Census ZCTA boundaries and filtered historical property markers. Generalized polygons are repaired; outside-region points are hidden.
- App: seven functional sections, saved artifacts, no training at startup. Local tests and browser verification are documented separately.
- Still pending: public deployment and verified public URL, actual deadline/Challenge 2 rubric, final team names, generative-LLM comparison and a final presentation deck. Pitch outline, demo script and judge Q&A accompany the project.
''')
print('Reports and charts generated. Assistant checks:',assistant_report['passed'],'/',len(checks))
