"""Download official free local inference assets; no inference requests leave the machine."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import time
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'Qwen3-4B-Q4_K_M.gguf'
URL = 'https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/' + MODEL


def main():
    target = ROOT/'.local-models'/MODEL
    parts = ROOT/'.local-models/qwen4-parts'
    parts.mkdir(parents=True, exist_ok=True)
    metadata = requests.get('https://huggingface.co/api/models/Qwen/Qwen3-4B-GGUF/tree/main', params={'expand': 'true'}, timeout=30)
    metadata.raise_for_status()
    info = next(x for x in metadata.json() if x['path'] == MODEL)
    size = info['size']
    expected = info.get('lfs', {}).get('oid')
    if not expected:
        raise RuntimeError('Official file hash missing')
    if not target.exists() or target.stat().st_size != size:
        chunk = 32 * 1024 * 1024
        jobs = [(i, a, min(a+chunk, size)-1) for i, a in enumerate(range(0, size, chunk))]
        def fetch(job):
            i, a, b = job
            path = parts/str(i)
            if path.exists() and path.stat().st_size == b-a+1:
                return
            for trial in range(4):
                try:
                    response = requests.get(URL+f'?download=true&part={i}&attempt={trial}', headers={'Range': f'bytes={a}-{b}'}, timeout=(30,120))
                    response.raise_for_status()
                    assert response.headers.get('Content-Range', '').startswith(f'bytes {a}-{b}/')
                    assert len(response.content) == b-a+1
                    path.write_bytes(response.content)
                    return
                except Exception:
                    if trial == 3: raise
                    time.sleep(2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for n, _ in enumerate(pool.map(fetch, jobs), 1):
                print(f'MODEL {n}/{len(jobs)} parts', flush=True)
        with target.with_suffix('.partial').open('wb') as out:
            for i, _, _ in jobs:
                out.write((parts/str(i)).read_bytes())
        os.replace(target.with_suffix('.partial'), target)
    digest = hashlib.file_digest(target.open('rb'), 'sha256').hexdigest()
    assert digest == expected, 'Model hash mismatch'
    print('MODEL SHA256 verified', flush=True)
    for part in parts.iterdir():
        if part.is_file() and part.name.isdigit(): part.unlink()
    runtime = ROOT/'.runtime/llama-vulkan'
    runtime.mkdir(exist_ok=True)
    if not (runtime/'llama-server.exe').exists():
        releases = requests.get('https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=8', timeout=30).json()
        asset = next(a for r in releases for a in r.get('assets', []) if a['name'].endswith('-bin-win-vulkan-x64.zip') and a['name'].startswith('llama-'))
        archive = ROOT/'.runtime'/asset['name']
        with requests.get(asset['browser_download_url'], stream=True, timeout=(30,120)) as response:
            response.raise_for_status()
            with archive.open('wb') as out:
                for data in response.iter_content(2**20): out.write(data)
        assert archive.stat().st_size == asset['size']
        if asset.get('digest'):
            assert 'sha256:'+hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() == asset['digest']
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if name.endswith('/'):continue
                (runtime/Path(name).name).write_bytes(z.read(name))
    (ROOT/'.runtime/local-model-manifest.json').write_text(json.dumps({'model': 'Qwen/Qwen3-4B-GGUF', 'file': MODEL, 'sha256': digest, 'bytes': size, 'runtime': 'llama.cpp Vulkan'}, indent=2))
    print('Local model ready', flush=True)


if __name__ == '__main__': main()
