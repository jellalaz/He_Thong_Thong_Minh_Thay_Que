"""Fetch two public research datasets and a local LaTeX engine; never modify conda base."""
import hashlib
import json
from pathlib import Path
import tarfile
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/v2'
TOOLS = ROOT / '.runtime/tectonic'


def fetch(url, path):
    if not path.exists():
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    records = {}
    url = 'https://archive.ics.uci.edu/static/public/529/early+stage+diabetes+risk+prediction+dataset.zip'
    path = RAW / 'early_stage.zip'
    records['early_stage'] = {'url': url, 'sha256': fetch(url, path),
                              'source': 'https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction+dataset'}
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith('.csv'))
        (RAW / 'early_stage.csv').write_bytes(z.read(name))
    metadata_url = 'https://www.openml.org/api/v1/json/data/37'
    r = requests.get(metadata_url, timeout=45); r.raise_for_status()
    meta = r.json()['data_set_description']
    (RAW / 'pima_metadata.json').write_text(json.dumps(meta, indent=2))
    url = meta['url']
    records['pima'] = {'url': url, 'sha256': fetch(url, RAW / 'pima.arff'),
                        'source': 'https://www.openml.org/d/37', 'version': meta['version']}
    (RAW / 'sources.json').write_text(json.dumps(records, indent=2) + '\n')
    # These two small, public research sources are also packaged for offline retraining.
    import shutil
    packaged = ROOT / 'data/v2/sources'; packaged.mkdir(parents=True, exist_ok=True)
    for name in ['early_stage.zip', 'early_stage.csv', 'pima.arff', 'pima_metadata.json', 'sources.json']:
        shutil.copy2(RAW / name, packaged / name)
    print(json.dumps(records, indent=2), flush=True)
    TOOLS.mkdir(parents=True, exist_ok=True)
    if not (TOOLS / 'tectonic').exists():
        r = requests.get('https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest', timeout=45)
        r.raise_for_status()
        asset = next(a for a in r.json()['assets'] if 'aarch64-apple-darwin' in a['name'] and a['name'].endswith('.tar.gz'))
        path = TOOLS / asset['name']
        digest = fetch(asset['browser_download_url'], path)
        if asset.get('digest'):
            assert asset['digest'] == 'sha256:' + digest
        with tarfile.open(path) as tar:
            tar.extractall(TOOLS, filter='data')
        (TOOLS / 'manifest.json').write_text(json.dumps({'url': asset['browser_download_url'], 'sha256': digest}, indent=2))
    print('Datasets and local Tectonic ready.', flush=True)


if __name__ == '__main__': main()
