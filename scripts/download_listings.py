"""Download only the publisher's light file after verifying Kaggle metadata."""
import hashlib
import json
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'data/raw'
out.mkdir(parents=True, exist_ok=True)
base = 'https://www.kaggle.com/api/v1/datasets/'
ref = 'datadetective08/houston-housing-market-2024'
metadata = json.load(urllib.request.urlopen(base + 'view/' + ref, timeout=60))
files = json.load(urllib.request.urlopen(base + 'list/' + ref, timeout=60))
assert metadata['licenseName'] == 'CC BY-NC-SA 4.0', 'Review changed license before download'
name = 'houston_housing market 2024_light.json'
assert any(f['name'] == name for f in files['datasetFiles'])
url = base + 'download/' + ref + '/' + urllib.parse.quote(name)
path = out / 'houston_listings_light.download'
if not path.exists():
    urllib.request.urlretrieve(url, path)
if zipfile.is_zipfile(path):
    with zipfile.ZipFile(path) as archive:
        print('Archive members:', [(i.filename, i.file_size) for i in archive.infolist()])
        members = [i for i in archive.infolist() if Path(i.filename).name == name]
        assert len(members) == 1
        target = out / name
        with archive.open(members[0]) as src, target.open('wb') as dst:
            import shutil
            shutil.copyfileobj(src, dst)
else:
    target = out / name
    path.replace(target)
manifest = {'retrieved_at_utc': datetime.now(timezone.utc).isoformat(), 'source_url': url,
            'metadata': metadata, 'files': files, 'file': name,
            'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
(root / 'artifacts/evaluation/listings_source.json').write_text(json.dumps(manifest, indent=2))
print('Saved', target, target.stat().st_size)
