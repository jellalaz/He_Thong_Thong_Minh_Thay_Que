"""Check the hand-in bundle independently of the running web and its in-memory index."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch
import zipfile
from app.retrieval import load_knowledge
from app.settings import database
from app.main import graph_driver
from scripts.query_knowledge_export import verify_bundle, query_bundle

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'exports/diabetes'
checks=[]
manifest=verify_bundle(folder)
checks.append('All exported file sizes and SHA-256 checksums are valid')
kb=json.loads((folder/'kb/knowledge.json').read_text(encoding='utf-8'))
current=load_knowledge()
assert kb['documents']==current['documents']
assert set(kb['sources'])=={d['source'] for d in current['documents']}
graph=json.loads((folder/'kg/graph.json').read_text(encoding='utf-8'))
expected={(d['id'],*t) for d in kb['documents'] for t in d['triples']}
assert {(r['document'],r['source'],r['relation'],r['target']) for r in graph['relationships']}==expected
assert len(graph['nodes'])==manifest['nodes'] and len(graph['relationships'])==manifest['relationships']
checks.append('Exported KB and graph match the canonical documents and exact source triples')
with (folder/'kg/nodes.csv').open(encoding='utf-8-sig',newline='') as f:nodes=list(csv.DictReader(f))
with (folder/'kg/relationships.csv').open(encoding='utf-8-sig',newline='') as f:edges=list(csv.DictReader(f))
assert len(nodes)==manifest['nodes'] and len(edges)==manifest['relationships']
names={r['id']:r['name'] for r in nodes}
assert {(r['document'],names[r['source_id']],r['relation'],names[r['target_id']]) for r in edges}==expected
assert all(r['evidence']==next(d['text'] for d in kb['documents'] if d['id']==r['document']) for r in edges)
checks.append('UTF-8 CSV preserves Vietnamese, document IDs, endpoints and evidence')

with zipfile.ZipFile(folder.parent/'glucoguide_kb_kg_rag.zip') as archive:
    for name,record in manifest['files'].items():
        assert hashlib.sha256(archive.read('diabetes/'+name)).hexdigest()==record['sha256']
    assert json.loads(archive.read('diabetes/manifest.json'))==manifest
checks.append('ZIP contains the same verified files as the expanded bundle')

evaluation=json.loads((folder/'rag/evaluation.json').read_text(encoding='utf-8'))
with patch('socket.create_connection',side_effect=AssertionError('Offline query attempted network')),patch.object(socket.socket,'connect',side_effect=AssertionError('Offline query attempted network')):
    for case in evaluation['cases']:
        result=query_bundle(folder,case['question'],case.get('history'))
        assert result['sources']==case['selected'],case['id']
        selected={r['id'] for r in result['sources']}
        assert all(f['document'] in selected for f in result['graph_evidence'])
checks.append('All 22 exported retrieval results replay exactly with sockets disabled')

env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',PYTHONPATH='')
run=subprocess.run([sys.executable,'-B',str(folder/'code/scripts/query_knowledge_export.py'),str(folder),'--question','HbA1c là gì?'],cwd=folder,env=env,capture_output=True,text=True,encoding='utf-8',check=True)
replayed=json.loads(run.stdout)
assert replayed['graph_evidence'] and replayed['storage']=='exported-snapshot'
checks.append('The copied entry point runs from the bundle with its own modules and intent model')

with tempfile.TemporaryDirectory(prefix='verify-export-',dir=ROOT/'.runtime') as temporary:
    temporary=Path(temporary).resolve()
    assert temporary.is_relative_to((ROOT/'.runtime').resolve())
    copied=temporary/'diabetes';shutil.copytree(folder,copied)
    (copied/'rag/settings.json').write_text('{}',encoding='utf-8')
    try:verify_bundle(copied)
    except ValueError:pass
    else:raise AssertionError('Modified bundle accepted')
checks.append('A changed file fails the integrity check before index loading')

with graph_driver() as driver:
    # EXPLAIN parses and plans the exported Cypher without executing MERGE or SET.
    driver.execute_query('EXPLAIN '+(folder/'kg/import.cypher').read_text(encoding='utf-8').rstrip(';\n'),database_=database())
checks.append('Neo4j accepts exported Cypher syntax; validation makes no database writes')
result={'passed':len(checks),'checks':checks,'retrieval_roundtrip_cases':len(evaluation['cases']),'nodes':manifest['nodes'],'relationships':manifest['relationships']}
(ROOT/'results/knowledge_export_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result))
