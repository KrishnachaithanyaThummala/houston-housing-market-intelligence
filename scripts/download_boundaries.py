"""Download only selected 2020 Census ZCTA polygons, WGS84 GeoJSON."""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
zips = sorted(pd.read_parquet(root / 'data/processed/zip_metadata.parquet').zip_code)
url = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/2/query'
params = {'where': 'ZCTA5 IN (' + ','.join("'" + z + "'" for z in zips) + ')',
          'outFields': 'ZCTA5,NAME,CENTLAT,CENTLON', 'returnGeometry': 'true',
          'outSR': '4326', 'f': 'geojson', 'maxAllowableOffset': '0.0003'}
request_url = url + '?' + urllib.parse.urlencode(params)
result = json.load(urllib.request.urlopen(request_url,timeout=90))
assert result.get('type') == 'FeatureCollection', result
assert not result.get('exceededTransferLimit'), 'Incomplete Census response'
for feature in result['features']:
    feature['properties']['zip_code'] = feature['properties']['ZCTA5']
found = {f['properties']['zip_code'] for f in result['features']}
assert found.issubset(set(zips))
(root/'data/geographic/houston_zcta.geojson').write_text(json.dumps(result))
(root/'artifacts/evaluation/boundary_source.json').write_text(json.dumps({
    'source': 'U.S. Census Bureau TIGERweb; 2020 Census ZCTAs in current service',
    'url': request_url, 'crs': 'EPSG:4326', 'generalization_degrees': .0003,
    'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
    'requested': len(zips), 'returned': len(found), 'missing': sorted(set(zips)-found),
    'limitation': 'ZCTA areas approximate postal ZIPs; city-label ZIP selection is not a city boundary.'},indent=2))
print('Downloaded',len(found),'ZCTAs; missing',sorted(set(zips)-found))
