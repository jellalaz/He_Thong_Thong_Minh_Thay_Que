"""Install portable Apple Silicon runtimes inside this repository, not conda base."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import tarfile

import requests

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
NEO4J_VERSION = '2026.10.1'
NODE_VERSION = 'v24.22.3'
PLAYWRIGHT_VERSION = '1.65.0'


def download(url, target, expected=None):
    if not target.exists():
        print('Downloading ' + target.name, flush=True)
        partial = target.with_suffix(target.suffix + '.partial')
        with requests.get(url, stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            with partial.open('wb') as out:
                for chunk in response.iter_content(1024 * 1024):
                    out.write(chunk)
        partial.replace(target)
    digest = hashlib.file_digest(target.open('rb'), 'sha256').hexdigest()
    if expected and digest != expected:
        raise RuntimeError('Checksum mismatch: ' + target.name)
    return digest


def java_environment():
    env = dict(os.environ)
    # Locate the installed Java 21 instead of keeping the Windows JAVA_HOME.
    env['JAVA_HOME'] = subprocess.check_output(
        ['/usr/libexec/java_home', '-v', '21'], text=True).strip()
    return env


def restore_data():
    """Restore the raw inputs used by the current training/audit scripts."""
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    cora = json.loads((ROOT / 'results/cora/summary.json').read_text())
    (raw / 'cora').mkdir(exist_ok=True)
    for name, expected in cora['sha256'].items():
        download(cora['source'] + name, raw / 'cora' / name, expected)
    audit = json.loads((ROOT / 'results/data_audit.json').read_text())
    url = 'https://www.kaggle.com/api/v1/datasets/download/mobeenfatimah/diabetes-risk-prediction-dataset-50k-patients'
    download(url, raw / 'diabetes.zip', audit['classification']['sha256'])
    print('Raw diabetes and Cora inputs match the recorded checksums.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-only', action='store_true')
    args = parser.parse_args()
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise SystemExit('This installer is for macOS Apple Silicon.')
    if sys.prefix == sys.base_prefix:
        raise SystemExit('Run using .venv/bin/python, or bash setup-macos.sh.')
    if args.data_only:
        restore_data()
        return
    RUNTIME.mkdir(exist_ok=True)
    manifest = {}
    neo_home = RUNTIME / ('neo4j-community-' + NEO4J_VERSION)
    if not neo_home.exists():
        filename = neo_home.name + '-unix.tar.gz'
        url = 'https://dist.neo4j.org/' + filename
        archive = RUNTIME / filename
        # Neo4j publishes SHA-256 separately from the binary.
        checksum = requests.get(url + '.sha256', timeout=30)
        checksum.raise_for_status()
        expected = checksum.text.split()[0]
        digest = download(url, archive, expected)
        with tarfile.open(archive) as tar:
            tar.extractall(RUNTIME, filter='data')
        manifest['neo4j'] = {'version': NEO4J_VERSION, 'url': url, 'sha256': digest}
    config = neo_home / 'conf/neo4j.conf'
    # Only update these local settings; preserve all unrelated distro defaults.
    settings = {
        'server.default_listen_address': '127.0.0.1',
        'server.default_advertised_address': 'localhost',
        'server.bolt.listen_address': '127.0.0.1:7687',
        'server.http.listen_address': '127.0.0.1:7474',
        'server.memory.heap.initial_size': '256m',
        'server.memory.heap.max_size': '512m',
        'server.memory.pagecache.size': '256m',
        'dbms.usage_report.enabled': 'false',
    }
    lines = [line for line in config.read_text().splitlines()
             if line.split('=', 1)[0].strip() not in settings]
    config.write_text('\n'.join(lines) + '\n' + '\n'.join(k + '=' + v for k, v in settings.items()) + '\n')
    env_file = ROOT / '.env'
    if not env_file.exists():
        password = secrets.token_urlsafe(24)
        env_file.write_text('NEO4J_URI=bolt://127.0.0.1:7687\nNEO4J_USER=neo4j\n'
                            'NEO4J_PASSWORD=' + password + '\nNEO4J_DATABASE=neo4j\n')
        env_file.chmod(0o600)
    values = dict(line.split('=', 1) for line in env_file.read_text().splitlines()
                  if '=' in line and not line.startswith('#'))
    if not (neo_home / 'data/dbms/auth.ini').exists() and not (neo_home / 'data/databases/system').exists():
        subprocess.run([str(neo_home / 'bin/neo4j-admin'), 'dbms', 'set-initial-password',
                        values['NEO4J_PASSWORD']], env=java_environment(), check=True,
                       stdout=subprocess.DEVNULL)

    # Node is needed only by the existing Playwright UI checks. Install locally.
    node_home = RUNTIME / 'node'
    if not (node_home / 'bin/node').exists():
        version = NODE_VERSION
        filename = 'node-' + version + '-darwin-arm64.tar.gz'
        base = 'https://nodejs.org/dist/' + version + '/'
        response = requests.get(base + 'SHASUMS256.txt', timeout=30)
        response.raise_for_status()
        expected = next(line.split()[0] for line in response.text.splitlines() if line.endswith(filename))
        digest = download(base + filename, RUNTIME / filename, expected)
        with tarfile.open(RUNTIME / filename) as tar:
            tar.extractall(RUNTIME, filter='data')
        node_home.symlink_to('node-' + version + '-darwin-arm64', target_is_directory=True)
        manifest['node'] = {'version': version, 'sha256': digest, 'url': base + filename}
    node_env = dict(os.environ, PATH=str(node_home / 'bin') + os.pathsep + os.environ['PATH'],
                    npm_config_cache=str(RUNTIME / 'npm-cache'), PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1')
    ui = RUNTIME / 'ui-tests'
    subprocess.run([str(node_home / 'bin/npm'), 'install', '--prefix', str(ui),
                    '--no-audit', '--no-fund', '--save-exact', 'playwright@' + PLAYWRIGHT_VERSION],
                   env=node_env, check=True)
    manifest_file = RUNTIME / 'macos-install.json'
    previous = json.loads(manifest_file.read_text()) if manifest_file.exists() else {}
    manifest_file.write_text(json.dumps(dict(previous, **manifest), indent=2) + '\n')
    subprocess.run([sys.executable, str(ROOT / 'scripts/setup_local_qwen4.py')], cwd=ROOT, check=True)
    print('Portable macOS runtimes ready; conda base was not modified.', flush=True)


if __name__ == '__main__':
    main()
