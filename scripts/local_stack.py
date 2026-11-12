"""Start, inspect and stop this project's macOS services without system installs."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.setup_macos import java_environment, NEO4J_VERSION
from app.settings import load_environment

RUNTIME = ROOT / '.runtime'
NEO_HOME = RUNTIME / ('neo4j-community-' + NEO4J_VERSION)
STATE = RUNTIME / 'macos-processes.json'


def environment():
    load_environment()
    env = java_environment()
    env.update(GLUCOGUIDE_LOCAL_LLM='1', GLUCOGUIDE_LOCAL_ONLY='1',
               GLUCOGUIDE_LLAMA_URL='http://127.0.0.1:11435',
               GLUCOGUIDE_LLAMA_KEY_FILE=str(RUNTIME / 'llama-api.key'),
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
               MPLCONFIGDIR=str(RUNTIME / 'matplotlib'))
    return env


def model_headers():
    key = RUNTIME / 'llama-api.key'
    return {'Authorization': 'Bearer ' + key.read_text().strip()} if key.exists() else {}


def get(url, headers=None):
    try:
        with httpx.Client(trust_env=False, timeout=3) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            return r.json()
    except (httpx.HTTPError, ValueError):
        return None


def status():
    web = get('http://127.0.0.1:8765/api/status')
    model = get('http://127.0.0.1:11435/health', model_headers())
    graph = get('http://127.0.0.1:7474/')
    return {'web': web, 'qwen': model, 'neo4j_http': bool(graph),
            'ready': bool(web and web.get('neo4j') and web.get('local_llm')
                          and web.get('local_only') and model and model.get('status') == 'ok')}


def spawn(name, command, env):
    # Keep each service in a separate session so it survives closing Terminal.
    with (RUNTIME / (name + '.log')).open('ab') as log:
        child = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    state[name] = {'pid': child.pid, 'command': command, 'started_at': time.time()}
    STATE.write_text(json.dumps(state, indent=2) + '\n')
    print('Started ' + name + '; log: .runtime/' + name + '.log', flush=True)
    return child


def wait_ready(name, probe, child, seconds=120):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if probe():
            print(name + ' ready', flush=True)
            return
        if child is not None and child.poll() is not None:
            raise RuntimeError(name + ' stopped. Read .runtime/' + name + '.log')
        time.sleep(1)
    raise RuntimeError(name + ' startup timed out. Read .runtime/' + name + '.log')


def start():
    import secrets
    RUNTIME.mkdir(exist_ok=True)
    model = ROOT / '.local-models/Qwen3-4B-Q4_K_M.gguf'
    server = RUNTIME / 'llama-metal/llama-server'
    for path in [model, server, NEO_HOME / 'bin/neo4j']:
        if not path.exists():
            raise RuntimeError('Missing ' + str(path.relative_to(ROOT)) + '; run bash setup-macos.sh')
    env = environment()
    key = RUNTIME / 'llama-api.key'
    if not key.exists():
        key.write_text(secrets.token_urlsafe(48) + '\n')
        key.chmod(0o600)
    if not get('http://127.0.0.1:7474/'):
        child = spawn('neo4j', [str(NEO_HOME / 'bin/neo4j'), 'console'], env)
        wait_ready('neo4j', lambda: get('http://127.0.0.1:7474/'), child)
    # MERGE is idempotent: reconstruct the graph from the versioned KB.
    subprocess.run([sys.executable, 'scripts/ingest_graph.py'], cwd=ROOT, env=env, check=True)
    if not get('http://127.0.0.1:11435/health', model_headers()):
        child = spawn('qwen', [str(server), '-m', str(model), '--host', '127.0.0.1',
                      '--port', '11435', '--device', 'MTL0', '-ngl', '99', '-c', '8192',
                      '-np', '1', '-t', '6', '--jinja', '--no-ui', '--api-key-file', str(key)], env)
        wait_ready('qwen', lambda: get('http://127.0.0.1:11435/health', model_headers()), child)
    web = get('http://127.0.0.1:8765/api/status')
    if web:
        if not web.get('local_only') or not web.get('local_llm'):
            raise RuntimeError('Port 8765 has another app/configuration. Stop it before starting.')
    else:
        child = spawn('web', [sys.executable, '-m', 'uvicorn', 'app.main:app',
                      '--host', '127.0.0.1', '--port', '8765'], env)
        wait_ready('web', lambda: get('http://127.0.0.1:8765/api/status'), child)
    result = status()
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if not result['ready']:
        raise RuntimeError('One or more services are not ready.')
    print('GlucoGuide: http://localhost:8765\nNeo4j Browser: http://localhost:7474/browser/')


def stop():
    if not STATE.exists():
        print('No project-managed processes.')
        return
    state = json.loads(STATE.read_text())
    for name in ['web', 'qwen', 'neo4j']:
        record = state.get(name)
        if not record:
            continue
        pid = record['pid']
        # Refuse a reused PID belonging to another program.
        actual = subprocess.run(['ps', '-p', str(pid), '-o', 'command='],
                                capture_output=True, text=True).stdout
        expected = 'app.main:app' if name == 'web' else str(ROOT)
        if expected in actual and str(ROOT) in actual:
            os.killpg(pid, signal.SIGTERM)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                process = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='],
                                         capture_output=True, text=True).stdout.strip()
                if not process or process.startswith('Z'):
                    break
                time.sleep(.25)
            else:
                raise RuntimeError(name + ' is still stopping; retry later.')
            print('Stopped ' + name)
        elif actual.strip():
            raise RuntimeError('PID changed ownership; refusing to stop ' + name)
        state.pop(name, None)
    STATE.write_text(json.dumps(state, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'status'], nargs='?', default='start')
    args = parser.parse_args()
    if args.command == 'restart':
        stop()
        start()
    elif args.command == 'start':
        start()
    elif args.command == 'stop':
        stop()
    else:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
