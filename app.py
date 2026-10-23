"""Offline-artifact dashboard. Run: streamlit run app.py"""
import html
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.assistant import answer, DISCLAIMER
from src.data import pricing_category

ROOT = Path(os.environ.get('HOUSING_ARTIFACT_ROOT', Path(__file__).resolve().parent))
st.set_page_config(page_title='Houston Housing Market Intelligence', page_icon='⌂', layout='wide')
st.markdown('''<style>
.stApp {background: #f7f8fa; color:#132a38;}
[data-testid="stSidebar"] {background:#e9eef2;}
h1,h2,h3 {color:#15394b; letter-spacing:-.025em;}
[data-testid="stMetric"] {background:white;border:1px solid #dbe3e9;border-radius:12px;padding:18px;}
.hero {background:#15394b;color:#fff;padding:28px 32px;border-radius:16px;margin-bottom:22px;}
.hero h1 {color:#fff;font-size:2.2rem;margin:0;}
.hero p {color:#d7e7ed;max-width:850px;margin:8px 0 0;}
.eyebrow {font-size:.76rem;font-weight:700;letter-spacing:.16em;color:#9cddd4;margin-bottom:8px;}
</style>''', unsafe_allow_html=True)


@st.cache_data
def load_data():
    def report(name):
        return json.loads((ROOT / 'artifacts/evaluation' / name).read_text())
    return {
        'properties': pd.read_parquet(ROOT / 'artifacts/predictions/properties.parquet'),
        'history': pd.read_parquet(ROOT / 'data/processed/zhvi.parquet'),
        'metadata': pd.read_parquet(ROOT / 'data/processed/zip_metadata.parquet'),
        'forecasts': pd.read_parquet(ROOT / 'artifacts/forecasts/forecasts.parquet'),
        'regression': report('regression_report.json'), 'forecast_report': report('forecast_report.json'),
        'zhvi_audit': report('zhvi_audit.json'), 'listings_audit': report('listings_audit.json'),
        'integration': report('integration_audit.json'),
    }


@st.cache_resource
def load_model():
    return joblib.load(ROOT / 'artifacts/models/price_pipeline.joblib')


@st.cache_data
def explanation(property_id):
    from src.explain import explain_property
    all_rows = pd.read_parquet(ROOT / 'artifacts/predictions/properties.parquet')
    row = all_rows.loc[all_rows.property_id.eq(property_id)].iloc[[0]]
    return explain_property(load_model(), row)


def forecast_chart(zip_code):
    hist = data['history'].loc[data['history'].zip_code.eq(zip_code)].dropna()
    future = data['forecasts'].loc[data['forecasts'].zip_code.eq(zip_code)].sort_values('date')
    recent = hist[hist.date.ge('2015-01-01')]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent.date, y=recent.zhvi_value, name='Observed ZHVI', line=dict(color='#15394b', width=3)))
    if not future.empty:
        fig.add_trace(go.Scatter(x=future.date, y=future.upper, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=future.date, y=future.lower, fill='tonexty', fillcolor='rgba(13,148,136,.15)',
                                mode='lines', line=dict(width=0), name='Empirical 90% band'))
        last = hist.iloc[-1]
        fig.add_trace(go.Scatter(x=[last.date]+future.date.tolist(), y=[last.zhvi_value]+future.prediction.tolist(),
                                name='Forecast', line=dict(color='#0d9488', dash='dash',width=3)))
        fig.add_shape(type='line', x0=last.date, x1=last.date, y0=0, y1=1, yref='paper', line=dict(color='#738592',dash='dot'))
    fig.update_layout(height=430, yaxis_title='ZHVI ($; modeled typical home value)', xaxis_title=None,
                      paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=20,b=10), legend=dict(orientation='h'))
    st.plotly_chart(fig, use_container_width=True)
    return future


try:
    data = load_data()
except (FileNotFoundError, ValueError) as exc:
    st.title('Houston Housing Market Intelligence')
    st.error('Required offline artifacts are unavailable. Run the documented data and model pipeline before serving.')
    st.code(str(exc))
    st.stop()

properties = data['properties']
# Show held-out examples: explanations and displayed predictions come from the same evaluated model.
examples = properties.loc[properties.partition.isin(['validation','test'])].copy()
st.sidebar.title('Houston Housing')
st.sidebar.caption('Historical property intelligence')
if 'pending_property_id' in st.session_state:
    st.session_state['property_id'] = st.session_state.pop('pending_property_id')
if 'pending_page' in st.session_state:
    st.session_state['active_page'] = st.session_state.pop('pending_page')
page = st.sidebar.radio('Explore', ['Overview','Housing map','Property intelligence','Market forecasting',
                                   'Housing assistant','Model evaluation','Data & methodology'], key='active_page')
zip_options = ['All ZIPs'] + sorted(data['metadata'].zip_code)
zip_filter = st.sidebar.selectbox('ZIP scope', zip_options)
if zip_filter != 'All ZIPs':
    examples = examples.loc[examples.zip_code.eq(zip_filter)]
budget = st.sidebar.slider('Maximum historical asking price', 50000, 10000000, 2000000, step=50000, format='$%d')
minimum_beds = st.sidebar.select_slider('Minimum bedrooms', options=[0,1,2,3,4,5], value=0)
types = st.sidebar.multiselect('Property types', sorted(properties.property_type.unique()),
                              default=sorted(properties.property_type.unique()))
examples = examples.loc[examples.price.le(budget) & examples.bedrooms.fillna(0).ge(minimum_beds) & examples.property_type.isin(types)]
st.sidebar.caption(f'{len(examples):,} held-out historical examples match. No live listings.')
if not examples.empty:
    ids = examples.property_id.tolist()
    lookup = examples.set_index('property_id')
    if st.session_state.get('property_id') not in ids:
        st.session_state.property_id = ids[0]
    selected_id = st.sidebar.selectbox('Historical property', ids, key='property_id',
        format_func=lambda i: f"{lookup.loc[i,'address']} · ${lookup.loc[i,'price']:,.0f}")
    selected = lookup.loc[selected_id].to_dict()
    selected['property_id'] = selected_id
else:
    selected = None
    st.sidebar.info('No properties match. Adjust the filters; ZIP forecasts remain available.')
default_zip = zip_filter if zip_filter != 'All ZIPs' else (selected['zip_code'] if selected else '77084')
st.sidebar.caption('Snapshot: June 5, 2024\n\nLatest ZHVI: September 2026')

if page == 'Overview':
    st.markdown('''<div class="hero"><div class="eyebrow">HOUSTON · DATA TO DECISIONS</div>
    <h1>Understand the price.<br>See the wider market.</h1>
    <p>Explore historical asking prices, explainable model estimates and ZIP-level home-value forecasts in one place.</p></div>''', unsafe_allow_html=True)
    cols = st.columns(2) + st.columns(2)
    cols[0].metric('Residential records', f"{data['listings_audit']['clean_rows']:,}")
    cols[1].metric('ZIP market series', data['zhvi_audit']['selected_zips'])
    cols[2].metric('Held-out price MAE', f"${data['regression']['test']['mae']:,.0f}")
    cols[3].metric('Selected forecast', data['forecast_report']['winner'])
    st.subheader('A buyer’s starting point')
    left, right = st.columns([1,1.35])
    with left:
        st.write('Choose a historical home in the sidebar, compare its asking price with an out-of-sample model estimate, then examine its ZIP market history.')
        st.info('Historical asking-price estimates are screening tools. They do not establish appraised value, current availability or an investment opportunity.')
        st.write(f"**Selected regressor:** {data['regression']['selection']['model']}")
        st.write('Houston and South Houston city labels, Texas. No Houstonia, TX match was found; the Missouri city is excluded.')
    with right:
        st.caption(f'ZIP {default_zip} · historical index and forecast')
        forecast_chart(default_zip)
    st.caption('Explore only held-out property examples so displayed estimates and SHAP explanations use the same evaluated model. All counts and errors come from saved artifacts.')

elif page == 'Housing map':
    st.title('A local view of the market')
    st.caption('Census 2020 ZCTAs approximate postal ZIPs. This map does not depict Houston city limits.')
    metric = st.selectbox('Map layer', ['Latest ZHVI','Historical 12-month change','Forecast 12-month change','Median historical asking price','Listing count'])
    reset = st.button('Reset map view')
    if reset:
        st.session_state['map_revision'] = st.session_state.get('map_revision',0)+1
    try:
        import folium
        from folium.plugins import MarkerCluster
        from streamlit_folium import st_folium
        boundary = json.loads((ROOT / 'data/geographic/houston_zcta.geojson').read_text())
        recent = data['history'].sort_values('date').groupby('zip_code').tail(1).set_index('zip_code').zhvi_value
        if metric == 'Latest ZHVI':
            values = recent
        elif metric == 'Historical 12-month change':
            history_wide = data['history'].pivot(index='zip_code',columns='date',values='zhvi_value')
            values = (history_wide.iloc[:,-1]/history_wide.iloc[:,-13]-1)*100
        elif metric == 'Forecast 12-month change':
            f = data['forecasts'].loc[data['forecasts'].horizon.eq(12)].set_index('zip_code')
            values = (f.prediction/f.latest_zhvi-1)*100
        elif metric == 'Listing count':
            values = properties.groupby('zip_code').size()
        else:
            values = properties.groupby('zip_code').price.median()
        for feature in boundary['features']:
            z = feature['properties']['zip_code']
            value = values.get(z, np.nan)
            feature['properties']['display_value'] = 'Unavailable' if pd.isna(value) else f'{value:,.1f}'
        view = folium.Map(location=[29.80,-95.38], zoom_start=10, tiles='OpenStreetMap')
        # Folium choropleth cannot create unique bins for a constant naive forecast layer.
        finite = values.dropna()
        if len(finite) and finite.nunique() > 1:
            dollars = metric in ['Latest ZHVI', 'Median historical asking price']
            map_values = values / 1000 if dollars else values
            label = metric + ' ($ thousands)' if dollars else metric
            folium.Choropleth(geo_data=boundary, data=map_values.rename('value').reset_index(), bins=5,
                columns=['zip_code','value'], key_on='feature.properties.zip_code', fill_color='YlGnBu',
                fill_opacity=.48, line_opacity=.35, nan_fill_color='#dedede', legend_name=label, name=metric).add_to(view)
        else:
            st.info('This metric is constant across available ZIPs; boundaries use a single fill color.')
        folium.GeoJson(boundary, name='ZIP details',
            style_function=lambda f: {'fillOpacity':.06,'color':'#547381','weight':.7},
            highlight_function=lambda f: {'weight':3,'fillOpacity':.2},
            tooltip=folium.GeoJsonTooltip(fields=['zip_code','display_value'], aliases=['ZCTA','Selected metric'])).add_to(view)
        chosen_boundary = {'type':'FeatureCollection','features':[f for f in boundary['features'] if f['properties']['zip_code']==default_zip]}
        folium.GeoJson(chosen_boundary,name='Selected ZIP', style_function=lambda f:{'fillOpacity':0,'color':'#0d9488','weight':3}).add_to(view)
        points = examples.loc[examples.map_eligible].head(1000).copy()
        if selected and selected['property_id'] not in set(points.property_id):
            points = pd.concat([points, examples.loc[examples.property_id.eq(selected['property_id'])]])
        cluster = MarkerCluster(name='Historical properties').add_to(view)
        for row in points.itertuples():
            folium.Marker([row.latitude,row.longitude],
                tooltip=html.escape(f'{row.address} · ${row.price:,.0f}'),
                popup=folium.Popup(html.escape(f'Property {row.property_id} | {row.address} | Historical asking price ${row.price:,.0f}'),max_width=300)).add_to(cluster)
        folium.LayerControl().add_to(view)
        event = st_folium(view, height=600, use_container_width=True,
            key=f'housing_map_{st.session_state.get("map_revision",0)}',
            returned_objects=['last_object_clicked_popup'])
        popup = event.get('last_object_clicked_popup') if event else None
        if popup:
            import re
            match = re.search(r'Property (\d+)', popup)
            if match and match[1] in set(examples.property_id):
                hit = examples.loc[examples.property_id.eq(match[1])].iloc[0]
                st.subheader(hit.address)
                st.write(f"Historical asking price **${hit.price:,.0f}** · estimate **${hit.estimated_price:,.0f}** · {hit.pricing_category}")
                if st.button('Open this property'):
                    # Sidebar widget cannot be mutated after instantiation; route through a pending ID.
                    st.session_state['pending_property_id'] = hit.property_id
                    st.session_state['pending_page'] = 'Property intelligence'
                    st.rerun()
        st.caption(f'Showing {len(points):,} of {len(examples):,} filtered examples; narrow filters to see other points. Attribution: U.S. Census Bureau; OpenStreetMap contributors; Zillow; Natasha Lekh / Kaggle.')
    except (ImportError, FileNotFoundError) as exc:
        st.warning(f'Map dependency or boundaries unavailable: {exc}')

elif page == 'Property intelligence':
    st.title('Put the asking price in context')
    if selected is None:
        st.info('Adjust filters to select a historical property.')
    else:
        st.subheader(selected['address'])
        st.caption(f"Property {selected['property_id']} · {selected['property_type']} · {selected['partition']} partition · snapshot June 5, 2024")
        cols = st.columns(2)
        cols[0].metric('Historical asking price',f"${selected['price']:,.0f}")
        cols[1].metric('Historical model estimate',f"${selected['estimated_price']:,.0f}")
        st.metric('Pricing gap',f"{selected['pricing_gap']*100:+.1f}%")
        threshold = st.slider('Screening threshold (%)',5,30,10,step=1)/100
        st.info(pricing_category(selected['pricing_gap'],threshold))
        st.caption(DISCLAIMER)
        st.write(f"**{selected['bedrooms']:g} bedrooms · {selected['bathrooms']:g} bathrooms · {selected['living_area']:,.0f} sq ft · ZIP {selected['zip_code']}**")
        st.write(f"Empirical historical estimate band: **${selected['estimate_lower']:,.0f}–${selected['estimate_upper']:,.0f}**. "
                 f"Observed test coverage: {data['regression']['test_interval_coverage']:.1%}; target 90%. This global band is not a property appraisal interval.")
        st.subheader('Market-level adjustment')
        st.metric('Approximate index-adjusted estimate',f"${selected['market_adjusted_value']:,.0f}")
        st.write(f"Historical estimate × September 2026 ZHVI / April 2024 ZHVI. ZIP index: "
                 f"${selected['historical_zhvi']:,.0f} → ${selected['latest_zhvi']:,.0f}. This is not a current asking price or fresh appraisal.")
        st.subheader('What influenced the model?')
        try:
            effects, base = explanation(selected['property_id'])
            top = effects.head(10).sort_values('contribution')
            fig = px.bar(top,x='contribution',y='feature',orientation='h',color='contribution',
                color_continuous_scale=['#b45344','#dce6e9','#0d9488'])
            fig.update_layout(height=390,coloraxis_showscale=False,xaxis_title='SHAP contribution to log(1 + asking price)',yaxis_title=None)
            st.plotly_chart(fig,use_container_width=True)
            st.caption(f'Actual selected-model SHAP; baseline log-price {base:.3f}. Contributions explain the model, not causal effects or dollar changes.')
        except (ImportError,ValueError,TypeError) as exc:
            st.warning(f'Explanation unavailable: {exc}')
        st.subheader(f"ZIP {selected['zip_code']} market history")
        forecast_chart(selected['zip_code'])

elif page == 'Market forecasting':
    st.title('The ZIP market, looking forward')
    zips = sorted(data['metadata'].zip_code)
    z = st.selectbox('Forecast ZIP',zips,index=zips.index(default_zip))
    future = forecast_chart(z)
    if not future.empty:
        st.metric('Latest observed ZHVI',f"${future.iloc[0].latest_zhvi:,.0f}")
        cols = st.columns(2)
        for col,h in zip(cols,[6,12]):
            f=future.loc[future.horizon.eq(h)].iloc[0]
            col.metric(f'{h}-month ZIP forecast',f'${f.prediction:,.0f}',f'{(f.prediction/f.latest_zhvi-1)*100:+.1f}%')
        st.write(f"**Selected method:** {future.iloc[0].method}. A flat forecast is the evaluated baseline, not missing model output.")
        st.caption('Forecast starts after September 2026. Bands use a separate historical calibration origin; pooled across ZIPs, with no guarantee of future coverage.')
        coverage=data['forecast_report']['test_interval_coverage_by_horizon']
        st.write(f"Observed interval coverage on the final held-out period: 6 months **{coverage.get('6',float('nan')):.1%}**; 12 months **{coverage.get('12',float('nan')):.1%}**. Target: 90%.")
        with st.expander('Monthly forecast values'):
            st.dataframe(future[['date','horizon','prediction','lower','upper']],hide_index=True,use_container_width=True)
        backtests=pd.read_parquet(ROOT/'artifacts/forecasts/backtests.parquet')
        local=backtests.loc[backtests.zip_code.eq(z)&backtests.phase.eq('test')&backtests.horizon.isin([6,12])]
        st.subheader('This ZIP: final held-out endpoint errors')
        st.dataframe(local[['method','horizon','actual','prediction','abs_error','smape']],hide_index=True,use_container_width=True)

elif page == 'Housing assistant':
    st.title('Ask about the evidence')
    st.caption('Grounded deterministic Q&A · no paid API · answers use selected records and saved model outputs.')
    st.write(f"Selected: **{selected['address']}**" if selected else 'No property selected. ZIP forecast questions remain available.')
    question = st.text_input('Your question',placeholder='Why is this property flagged as overpriced?')
    suggestions=['What is the historical listing price?','How many bedrooms and bathrooms?','What is the pricing category?',
                 'What is the 12 month forecast?','How reliable is this estimate?']
    suggestion=st.selectbox('Or try a question', ['Choose a question']+suggestions)
    q=question or (suggestion if suggestion!='Choose a question' else '')
    if q:
        with st.chat_message('user'): st.write(q)
        with st.chat_message('assistant'):
            st.write(answer(q,selected,data['forecasts'].loc[data['forecasts'].zip_code.eq(default_zip)],data['regression']))
    st.caption('One deterministic configuration is implemented. Local/hosted LLM and RAG comparisons have not been run. The predictive models power the analytics; this fallback does not claim generative-LLM behavior.')

elif page == 'Model evaluation':
    st.title('Measured performance, visible limits')
    tabs=st.tabs(['Asking-price regression','Pricing-screen classification','ZIP forecasting','Assistant'])
    with tabs[0]:
        st.write('Selection: training-only grouped cross-validation MAE in dollars. Final test results are reported after locking selection.')
        st.dataframe(pd.read_csv(ROOT/'artifacts/evaluation/regression_comparison.csv'),hide_index=True,use_container_width=True)
        st.json(data['regression'])
        test=properties.loc[properties.partition.eq('test')].copy()
        test['residual']=test.price-test.estimated_price
        cols=st.columns(2)
        with cols[0]:
            st.plotly_chart(px.scatter(test,x='price',y='estimated_price',log_x=True,log_y=True,
                labels={'price':'Historical asking price ($)','estimated_price':'Predicted asking price ($)'}),use_container_width=True)
        with cols[1]: st.plotly_chart(px.histogram(test,x='residual',nbins=70),use_container_width=True)
        with st.expander('Error by ZIP and price range'):
            st.dataframe(pd.read_csv(ROOT/'artifacts/evaluation/error_by_zip.csv'),hide_index=True)
            st.dataframe(pd.read_csv(ROOT/'artifacts/evaluation/error_by_price.csv'),hide_index=True)
    with tabs[1]:
        st.warning('These labels are model-derived pricing-gap categories, not independently verified bargains or mispricing.')
        st.dataframe(pd.read_csv(ROOT/'artifacts/evaluation/classification_comparison.csv'),hide_index=True,use_container_width=True)
        st.json(json.loads((ROOT/'artifacts/evaluation/classification_report.json').read_text()))
    with tabs[2]:
        st.write('Selection origins precede a separate calibration origin and final test origin. Forecasts use revised ZHVI history.')
        st.dataframe(pd.read_csv(ROOT/'artifacts/evaluation/forecast_comparison.csv'),hide_index=True,use_container_width=True)
        st.json(data['forecast_report'])
    with tabs[3]:
        path=ROOT/'artifacts/evaluation/chatbot_evaluation.json'
        if path.exists(): st.json(json.loads(path.read_text()))
        else: st.info('Assistant evaluation has not yet been generated.')

elif page == 'Data & methodology':
    st.title('Know what the data can tell you')
    st.markdown('''**Property data:** [Natasha Lekh / datadetective08, Houston housing market 2024](https://www.kaggle.com/datasets/datadetective08/houston-housing-market-2024), version 1. Publisher snapshot: June 5, 2024. License: CC BY-NC-SA 4.0. Cleaned and filtered for this noncommercial research demonstration; no source images or agent contacts are used.

**Market data:** [Zillow Research ZHVI](https://www.zillow.com/research/data/), supplied ZIP-level mid-tier smoothed seasonally adjusted series. Monthly observations through September 2026. ZHVI is a modeled typical-home-value index, not observed sale prices. Original download date is unknown.

**Geography:** U.S. Census Bureau TIGERweb, 2020 ZCTAs, WGS84. A ZCTA is an approximation of a postal ZIP. Texas plus exact city labels Houston/South Houston defines the initial scope. Houstonia exists only in Missouri in this file and is excluded. No city-boundary membership claim is made.

**Historical alignment:** June 2024 snapshot with April 2024 ZHVI reference and historical 6/12-month changes. This conservative lag does not eliminate revisions in the supplied later-vintage series. Results are retrospective, not a verified real-time historical trading simulation.

**Regression:** Predicts asking prices. Duplicate addresses and nearby coordinate cells are grouped. Preprocessing is fitted inside folds. Selection uses training-only CV. Test results do not decide the winner. A separate ZIP holdout stress test probes extrapolation; spatial dependence can remain.

**Pricing screens:** Cross-fitted regression residuals define provisional ±10% categories. The production rule is transparent. Classifier metrics measure pseudo-label reproduction only.

**Uncertainty:** Empirical historical errors calibrate bands. Observed coverage is reported; it can miss the nominal level. Historical trends and model estimates do not guarantee future prices.

**Scope limits:** Single historical snapshot, asking rather than transaction prices, no year-built field in the light file, no live availability, shared Zillow origin, no causal attribution and no independently verified mispricing labels.''')
    for name in ['zhvi_audit','listings_audit','integration']:
        with st.expander(name.replace('_',' ').title()): st.json(data[name])

st.caption('Houston Housing Market Intelligence · historical research demo · data and model outputs, with their limits made visible')
