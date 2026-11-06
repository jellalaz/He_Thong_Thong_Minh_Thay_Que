"""Offline provenance and model-to-support regression checks; no outside services."""
import hashlib
import json
import os
import socket
import ipaddress
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app, kb
from app.local_prompt import build_messages
from scripts.build_sourced_kb import compact
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
checks=[]
examples=json.loads((ROOT/'data/examples.json').read_text())
curated=[d for d in kb['documents'] if d.get('provenance')]
pdfs={}
for d in curated:
 p=d['provenance'];f=ROOT/p['local_file']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==p['sha256']
 if p['kind']=='pdf':
  pdfs.setdefault(str(f),PdfReader(f))
  assert compact(p['quote']) in compact(pdfs[str(f)].pages[p['page']-1].extract_text())
 else:
  text=' '.join(json.loads(f.read_text(encoding='utf-8'))['excerpts']) if f.suffix=='.json' else f.read_text(encoding='utf-8')
  assert compact(p['quote']) in compact(text)
checks.append('All reviewed excerpts, physical PDF pages and source hashes match local source files')
assert any(d['provenance']['kind']=='pdf' for d in curated) and any(d['source'].startswith('vinmec_') for d in curated)
checks.append('KB contains real PDF and Vinmec sources with inspectable provenance')
client=TestClient(app)
original_connect=socket.socket.connect
def local_connect(sock,address):
 if not isinstance(address,tuple) or not ipaddress.ip_address(address[0]).is_loopback:
  raise AssertionError('External network disabled in offline tests')
 return original_connect(sock,address)
with patch.dict(os.environ,{'GLUCOGUIDE_LOCAL_LLM':'0'}),patch('socket.socket.connect',local_connect):
 for task in ['classification','regression']:
  response=client.post('/api/chat',json={'task':task,'values':examples[task]})
  assert response.status_code==200,response.text
  body=response.json();assert body['model_review']['allow_diagnosis'] is False
  assert body['result'] and body['response_mode']=='model-support' and len(body['support']['cards'])==3
  ids={d['id'] for d in body['sources']}
  assert all(set(c['source_ids'])<=ids for c in body['support']['cards'])
  requested={t['receiver'] for t in body['trace'] if t['type']=='REQUEST'}
  assert {'Mô hình','Nhận xét mô hình','Hỗ trợ người dùng'}<=requested
  checks.append(task+': real model, bounded review and three evidence-backed support cards')
  body=client.post('/api/chat',json={'question':'Gợi ý một bữa trưa dễ chuẩn bị','model_context':{'task':task,'values':examples[task]}}).json()
  assert body['model_review']['task']==task and body['result'] is None and body['topic']=='meal'
  assert body['sources']
  checks.append(task+': follow-up carries recalculated research context and preserves current meal intent')
  body=client.post('/api/chat',json={'question':'Giải thích kết quả vừa rồi','model_context':{'task':task,'values':examples[task]}}).json()
  assert body['response_mode']=='model-support' and len(body['support']['cards'])==3 and body['model_review']['task']==task
  assert ('High' if task=='classification' else '207.5') in body['answer']
  checks.append(task+': a result follow-up uses the recomputed label or value')
 body=client.post('/api/chat',json={'question':'Gợi ý bữa trưa'}).json()
 assert body['model_review'] is None
 checks.append('A fresh chat has no implicit model context')
 for values,code in [({},200),({**examples['classification'],'Age':'nan'},422),({**examples['classification'],'Age':'inf'},422)]:
  assert client.post('/api/chat',json={'question':'Gợi ý bữa ăn','model_context':{'task':'classification','values':values}}).status_code==code
 checks.append('Missing or non-finite context values are validated before model use')
 with patch('app.main.models',{}):
  body=client.post('/api/chat',json={'question':'Đường huyết 350 mg/dL, nôn đau bụng','model_context':{'task':'classification','values':{}}}).json()
 assert body['safety']['level']=='EMERGENCY' and body['result'] is None
 checks.append('Emergency takes precedence over model context, graph and generation')
 response=client.get('/api/source/pdf_nutrition')
 assert response.status_code==200 and response.content[:4]==b'%PDF'
 assert client.get('/api/source/missing').status_code==404
 checks.append('Only known local source documents are served; PDF bytes remain intact')
 doc=next(d for d in curated if d['id']=='pdf_nutrition')
 prompt=build_messages({'documents':[doc],'plan':{},'question':'Ăn gì?','model_review':{'scope':'Nhãn nghiên cứu, không chẩn đoán'}})[0]['content']
 assert 'NGỮ CẢNH MÔ HÌNH NGHIÊN CỨU' in prompt
 checks.append('The local Qwen prompt receives explicit research scope for model follow-up')
result={'passed':len(checks),'reviewed_chunks':len(curated),'checks':checks,'external_network_calls':0}
(ROOT/'results/sources_support_tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
