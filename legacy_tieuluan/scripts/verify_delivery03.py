"""Kiểm tra gói bàn giao và tạo checksum, không in nội dung secret."""
from pathlib import Path
from hashlib import sha256
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
required=['tieuluan03_06_02_giangkt.254.docx','tieuluan03_06_02_giangkt.254.pdf',
          'main.ipynb','README.md','CHANGELOG.md','EXPERIMENT_RESULTS.md','FINAL_VERIFICATION.md','PROJECT_REPORT.md']
assert all((ROOT/p).is_file() for p in required)
nb=json.loads((ROOT/'main.ipynb').read_text());code=[c for c in nb['cells'] if c['cell_type']=='code']
assert [c['execution_count'] for c in code]==list(range(1,len(code)+1))
assert not any(o.get('output_type')=='error' for c in code for o in c.get('outputs',[]))
clone=Path('/tmp/httm_tl03_remote')
staged=subprocess.check_output(['git','diff','--name-only','-z','0b4447b'],cwd=clone).decode().split('\0')
secret=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|VERCEL_OIDC_TOKEN\s*=\s*[A-Za-z0-9])')
violations=[];scanned=0
for name in filter(None,staged):
    p=clone/name
    if any(x in p.parts for x in ['.vercel','raw','node_modules','__pycache__']) or p.name.startswith('.env'):
        violations.append(name);continue
    if p.suffix.lower() in ['.md','.py','.js','.cjs','.html','.json','.ipynb','.txt']:
        scanned+=1
        if secret.search(p.read_bytes()):violations.append(name)
assert not violations,violations
out={'required_files':{p:{'bytes':(ROOT/p).stat().st_size,'sha256':sha256((ROOT/p).read_bytes()).hexdigest()} for p in required},
     'notebook_cells':len(nb['cells']),'executed_code_cells':len(code),'notebook_error_outputs':0,
     'changed_text_files_scanned':scanned,'known_secret_patterns_found':False,
     'note':'Pattern scan supplements manual inspection; not a guarantee against every possible secret.'}
(ROOT/'artifacts_tl03/data/delivery_verified.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Required files:',len(required),'Code cells:',len(code),'Secret scan:',scanned,'text files, no matches')
