"""Source inspection and explicit, leakage-aware data preparation."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

CITIES = ('Houston', 'Houstonia', 'South Houston')
SNAPSHOT = pd.Timestamp('2024-06-05')  # publisher's documented snapshot, not listing start dates
REFERENCE = pd.Timestamp('2024-04-30')  # conservative complete-month lag; not vintage verification
NUMERIC = ['bedrooms', 'bathrooms', 'living_area', 'lot_area_sqft', 'latitude', 'longitude']
CATEGORICAL = ['zip_code', 'property_type']
MARKET = ['historical_zhvi', 'zhvi_change_6m', 'zhvi_change_12m']
FORBIDDEN = {'price', 'zestimate', 'rentZestimate', 'pricePerSquareFoot', 'pricing_gap', 'estimated_price'}


def normalize_zip(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if re.fullmatch(r'\d{5}(?:-\d{4})?', text):
        return text[:5]
    if re.fullmatch(r'\d{1,5}(?:\.0)?', text):
        return text.split('.')[0].zfill(5)
    return None


def source_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(2**20), b''):
            h.update(chunk)
    return h.hexdigest()


def clean_zhvi(path):
    raw = pd.read_csv(path, dtype={'RegionName': str})
    required = {'RegionName', 'State', 'City', 'RegionID'}
    if not required.issubset(raw):
        raise ValueError(f'Missing metadata: {required - set(raw.columns)}')
    dates = [c for c in raw if re.fullmatch(r'\d{4}-\d{2}-\d{2}', c)]
    if not dates or sorted(dates) != dates:
        raise ValueError('Monthly dates missing or unordered')
    selected = raw.loc[raw.State.eq('TX') & raw.City.isin(CITIES)].copy()
    selected['zip_code'] = selected.RegionName.map(normalize_zip)
    if selected.zip_code.isna().any() or selected.zip_code.duplicated().any():
        raise ValueError('Invalid or duplicate ZIP in ZHVI source')
    values = selected[dates].apply(pd.to_numeric, errors='raise')
    if (values <= 0).any().any():
        raise ValueError('Nonpositive ZHVI')
    metadata = selected.drop(columns=dates).copy()
    long = selected.melt(id_vars='zip_code', value_vars=dates, var_name='date', value_name='zhvi_value')
    long['date'] = pd.to_datetime(long.date)
    long = long.sort_values(['zip_code', 'date']).reset_index(drop=True)
    expected = pd.date_range(dates[0], dates[-1], freq='ME')
    if len(expected) != len(dates):
        raise ValueError('Missing month columns')
    report = {'source_rows': len(raw), 'source_columns': len(raw.columns), 'monthly_columns': len(dates),
              'first_month': dates[0], 'last_month': dates[-1], 'selected_zips': len(metadata),
              'city_counts': metadata.City.value_counts().to_dict(),
              'unmatched_requested_texas_cities': [c for c in CITIES if c not in set(metadata.City)],
              'missing_monthly_values': int(values.isna().sum().sum()),
              'latest_available_zips': int(values[dates[-1]].notna().sum()),
              'duplicate_selected_zips': 0, 'sha256': source_hash(path)}
    return metadata, long, report


def read_listings(path):
    with Path(path).open() as f:
        obj = json.load(f)
    if not isinstance(obj, list) or not all(isinstance(x, dict) for x in obj):
        raise ValueError('Expected inspected list-of-records JSON; schema changed')
    return pd.json_normalize(obj)


def clean_listings(path):
    raw = read_listings(path)
    required = ['zpid', 'address', 'addressCity', 'addressState', 'addressZipcode',
                'unformattedPrice', 'beds', 'baths', 'area', 'latLong.latitude',
                'latLong.longitude', 'hdpData.homeInfo.homeType']
    if not set(required).issubset(raw):
        raise ValueError('Listings schema changed; inspect before mapping')
    mapping = {'zpid': 'property_id', 'address': 'address', 'addressCity': 'city',
               'addressState': 'state', 'addressZipcode': 'zip_code', 'unformattedPrice': 'price',
               'beds': 'bedrooms', 'baths': 'bathrooms', 'area': 'living_area',
               'latLong.latitude': 'latitude', 'latLong.longitude': 'longitude',
               'hdpData.homeInfo.homeType': 'property_type'}
    frame = raw[list(mapping)].rename(columns=mapping)
    frame['zip_code'] = frame.zip_code.map(normalize_zip)
    frame['property_id'] = frame.property_id.astype(str)
    lot = pd.to_numeric(raw.get('hdpData.homeInfo.lotAreaValue'), errors='coerce')
    unit = raw.get('hdpData.homeInfo.lotAreaUnit')
    frame['lot_area_sqft'] = np.where(unit.eq('acres'), lot * 43560, np.where(unit.eq('sqft'), lot, np.nan))
    for c in NUMERIC + ['price']:
        frame[c] = pd.to_numeric(frame[c], errors='coerce')
    report = {'raw_rows': len(raw), 'flattened_columns': list(raw.columns),
              'duplicate_property_ids': int(frame.property_id.duplicated().sum()),
              'raw_property_types': frame.property_type.value_counts().to_dict(),
              'available_predictors': NUMERIC + CATEGORICAL,
              'absent_predictors': ['year_built'], 'snapshot_date': str(SNAPSHOT.date()),
              'snapshot_source': 'Kaggle publisher description; not individual listing start date',
              'excluded_fields': ['zestimate', 'rentZestimate', 'taxAssessedValue', 'priceForHDP',
                                  'priceChange', 'priceReduction', 'datePriceChanged', 'daysOnZillow',
                                  'timeOnZillow', 'brokerName', 'images', 'openHouse', 'pricePerSquareFoot']}
    frame = frame.loc[frame.state.eq('TX') & frame.city.isin(CITIES)].copy()
    report['city_scope_rows'] = len(frame)
    report['city_scope_property_types'] = frame.property_type.value_counts().to_dict()
    frame = frame.loc[frame.property_type.isin(['SINGLE_FAMILY', 'CONDO', 'TOWNHOUSE'])].copy()
    report['residential_rows'] = len(frame)
    valid = frame.price.gt(0) & frame.zip_code.notna() & frame.living_area.gt(0)
    report['invalid_price_zip_or_area_rows'] = int((~valid).sum())
    frame = frame.loc[valid].drop_duplicates('property_id').copy()
    # Two residential asking prices ($1,050/$1,400) resemble rent despite FOR_SALE status.
    # Exclude from sale-price learning under an explicit minimum, without asserting true rent status.
    suspicious = frame.price.lt(20000)
    report['excluded_residential_prices_below_20000'] = frame.loc[suspicious, ['property_id', 'price']].to_dict('records')
    frame = frame.loc[~suspicious].copy()
    # A repeated address may represent repeated records or units without a unique unit field.
    frame['address_group'] = frame.address.str.lower().str.replace(r'\s+', ' ', regex=True).str.strip()
    frame = frame.drop_duplicates(['address_group', 'price', 'living_area', 'bedrooms', 'bathrooms'])
    # Invalid physical attributes remain explicitly missing, not implausible measurements.
    for c in ['bedrooms', 'bathrooms', 'lot_area_sqft']:
        frame.loc[frame[c].lt(0), c] = np.nan
    valid_coord = frame.latitude.between(28.5, 31.0) & frame.longitude.between(-97, -94)
    report['invalid_or_outside_regional_coordinate_rows'] = int((~valid_coord).sum())
    frame['map_eligible'] = valid_coord
    frame.loc[~valid_coord, ['latitude', 'longitude']] = np.nan
    frame['snapshot_date'] = str(SNAPSHOT.date())
    report['clean_rows'] = len(frame)
    report['missing_predictors'] = frame[NUMERIC + CATEGORICAL].isna().sum().to_dict()
    report['price_summary'] = frame.price.describe().to_dict()
    return frame.reset_index(drop=True), report


def historical_market(long):
    wide = long.pivot(index='zip_code', columns='date', values='zhvi_value')
    reference = REFERENCE
    if reference not in wide:
        raise ValueError('Reference month absent')
    out = pd.DataFrame(index=wide.index)
    out['historical_zhvi'] = wide[reference]
    for months in (6, 12):
        prior = reference - pd.offsets.MonthEnd(months)
        out[f'zhvi_change_{months}m'] = wide[reference] / wide[prior] - 1
    out['latest_zhvi'] = wide.iloc[:, -1]
    out['zhvi_reference_date'] = reference.strftime('%Y-%m-%d')
    out['latest_zhvi_date'] = wide.columns[-1].strftime('%Y-%m-%d')
    return out.reset_index()


def integrate(listings, market):
    before = len(listings)
    out = listings.merge(market, on='zip_code', how='left', validate='many_to_one', indicator=True)
    assert len(out) == before
    report = {'before': before, 'after': len(out), 'listing_zips': int(listings.zip_code.nunique()),
              'zhvi_zips': int(market.zip_code.nunique()),
              'matched_listing_rows': int(out._merge.eq('both').sum()),
              'matched_listing_fraction': float(out._merge.eq('both').mean()),
              'matched_zip_codes': sorted(set(listings.zip_code) & set(market.zip_code)),
              'unmatched_zip_codes': sorted(set(listings.zip_code) - set(market.zip_code)),
              'missing_market_features': out[MARKET].isna().sum().to_dict()}
    return out.drop(columns='_merge'), report


def pricing_category(gap, threshold=.10):
    if threshold <= 0:
        raise ValueError('Threshold must be positive')
    if not np.isfinite(gap):
        return 'Unavailable'
    if gap < -threshold:
        return 'Potentially Underpriced'
    if gap > threshold:
        return 'Potentially Overpriced'
    return 'Approximately Fairly Priced'


def check_features(columns):
    allowed = set(NUMERIC + CATEGORICAL + MARKET)
    unexpected = set(columns) - allowed
    if unexpected or set(columns) & FORBIDDEN:
        raise ValueError(f'Predictor allowlist violation: {unexpected}')
