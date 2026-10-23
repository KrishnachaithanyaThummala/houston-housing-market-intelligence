"""Repair generalization artifacts and audit point coverage without inventing coordinates."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from shapely import make_valid
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union

root=Path(__file__).resolve().parents[1]
path=root/'data/geographic/houston_zcta.geojson'
original=root/'data/raw/houston_zcta_source.geojson'
if not original.exists(): original.write_bytes(path.read_bytes())
doc=json.loads(original.read_text())
repaired=[]
geometries={}
for feature in doc['features']:
    geom=shape(feature['geometry'])
    if not geom.is_valid:
        geom=make_valid(geom)
        if geom.geom_type=='GeometryCollection':
            geom=unary_union([g for g in geom.geoms if g.geom_type in ['Polygon','MultiPolygon']])
        repaired.append(feature['properties']['zip_code'])
    assert geom.is_valid and geom.geom_type in ['Polygon','MultiPolygon']
    feature['geometry']=mapping(geom)
    geometries[feature['properties']['zip_code']]=geom
path.write_text(json.dumps(doc))
region=unary_union(list(geometries.values()))
props=pd.read_parquet(root/'artifacts/predictions/properties.parquet')
inside=[]
matching=[]
for row in props.itertuples():
    point=Point(row.longitude,row.latitude)
    inside.append(region.covers(point))
    matching.append(geometries[row.zip_code].covers(point))
props['map_eligible']=inside
props.to_parquet(root/'artifacts/predictions/properties.parquet',index=False)
report={'repaired_generalized_zcta_count':len(repaired),'repaired_zips':repaired,
        'method':'Shapely make_valid; polygonal components only; source copy retained locally',
        'modeled_properties':len(props),'inside_selected_zcta_union':sum(inside),
        'outside_selected_zcta_union':len(props)-sum(inside),
        'inside_matching_zcta':sum(matching),
        'interpretation':'Postal ZIP labels and ZCTA polygons need not agree. Outside-union points remain in analytics but are hidden from map.'}
(root/'artifacts/evaluation/geography_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
