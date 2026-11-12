"""Verify the restored Mac runtime while preserving the historical report artifacts."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.local_stack import status

OUT = ROOT / '.runtime/macos-verification'
CHECKS = {
    'metal': [str(ROOT / '.runtime/llama-metal/llama-server'), '--list-devices'],
    'graph': [sys.executable, '-m', 'scripts.test_graph_coverage'],
    'safety': [sys.executable, '-m', 'scripts.test_safety_offline'],
    'intent': [sys.executable, '-m', 'scripts.test_intent'],
    'feedback': [sys.executable, '-m', 'scripts.test_local_feedback'],
    'knowledge_agents': [sys.executable, '-m', 'scripts.test_knowledge_agents'],
    'sources_support': [sys.executable, '-m', 'scripts.test_sources_support'],
    'api': [sys.executable, '-m', 'scripts.test_scenarios'],
    'export': [sys.executable, '-m', 'scripts.test_knowledge_export'],
    'graph_ui': [str(ROOT / '.runtime/node/bin/node'), 'scripts/test_graph_view.cjs'],
    'support_ui': [str(ROOT / '.runtime/node/bin/node'), 'scripts/test_support_view.cjs'],
    'live_qwen': [sys.executable, '-m', 'scripts.evaluate_chat_local'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', help='Comma-separated check names; default: all')
    args = parser.parse_args()
    names = args.only.split(',') if args.only else list(CHECKS)
    if any(name not in CHECKS for name in names):
        parser.error('Unknown check')
    OUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GLUCOGUIDE_LOCAL_LLM='0', PYTHONUNBUFFERED='1',
               NODE_PATH=str(ROOT / '.runtime/ui-tests/node_modules'),
               MPLCONFIGDIR=str(ROOT / '.runtime/matplotlib'))
    report_file = ROOT / 'results/macos_setup_checks.json'
    report = json.loads(report_file.read_text()) if args.only and report_file.exists() else {'checks': {}}
    report.update(checked_at=datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),
                  platform=platform.platform(), architecture=platform.machine(), python=sys.version,
                  python_executable=sys.executable)
    for name in names:
        # Existing scripts write their Windows-era report paths. Keep their new
        # evidence separately and restore those inputs byte-for-byte afterward.
        originals = {p: p.read_bytes() for folder in ['results', 'reports']
                     for p in (ROOT / folder).rglob('*') if p.is_file() and p != report_file}
        destination = OUT / name
        destination.mkdir(exist_ok=True)
        start = time.monotonic()
        print('Checking ' + name, flush=True)
        try:
            result = subprocess.run(CHECKS[name], cwd=ROOT, env=env, capture_output=True,
                                    text=True, timeout=600)
            log = result.stdout + result.stderr
            passed = result.returncode == 0
            if name == 'metal':
                passed = passed and 'MTL0:' in log and 'Apple' in log
            if name == 'live_qwen' and passed:
                responses = json.loads((ROOT / 'results/dialogue_live_checks.json').read_text())
                generated = [r for r in responses if r['response_mode'] == 'qwen4-rag']
                passed = bool(generated) and any(r['graph_context_supplied'] for r in generated)
                log += '\nVerified actual Qwen+KG responses: ' + str(len(generated)) + '\n'
        except subprocess.TimeoutExpired as exc:
            passed = False
            log = 'Timed out: ' + str(exc)
        finally:
            for folder in ['results', 'reports']:
                for p in (ROOT / folder).rglob('*'):
                    if not p.is_file() or p == report_file:
                        continue
                    current = p.read_bytes()
                    if p not in originals or current != originals[p]:
                        saved = destination / p.relative_to(ROOT)
                        saved.parent.mkdir(parents=True, exist_ok=True)
                        saved.write_bytes(current)
                        if p in originals:
                            p.write_bytes(originals[p])
                        else:
                            p.unlink()
        (destination / 'output.log').write_text(log)
        report['checks'][name] = {'passed': passed, 'seconds': round(time.monotonic() - start, 2),
                                  'log': str((destination / 'output.log').relative_to(ROOT))}
        print(('PASS ' if passed else 'FAIL ') + name + '\n' + log[-1800:], flush=True)
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    report['services'] = status()
    report['passed'] = all(x['passed'] for x in report['checks'].values()) and report['services']['ready']
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
