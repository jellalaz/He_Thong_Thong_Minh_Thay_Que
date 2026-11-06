"""Graph provenance, prompt integration, outage and safety tests with local fixtures."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.agents import Agent, MessageBus
from app.graph_knowledge import GraphKnowledgeAgent, ground_facts, FACT_QUERY
from app.local_prompt import build_messages
from app.main import app, kb

checks=[]
rows=[dict(source=t[0],relation=t[1],target=t[2],document=d['id'],evidence=d['text'],source_url=kb['sources'][d['source']]['url']) for d in kb['documents'] for t in d['triples']]
class Driver:
    calls=[]
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def execute_query(self,query,**params):
        assert query==FACT_QUERY
        self.calls.append(params['ids'])
        return SimpleNamespace(records=[r for r in rows if r['document'] in params['ids']])

bus=MessageBus();kg=GraphKnowledgeAgent(kb,Driver,lambda:'neo4j')
bus.register(Agent('Đồ thị tri thức',kg.receive))
result=bus.request('test','Đồ thị tri thức',{'document_ids':['a1c']})
assert result['facts'] and all(r['document']=='a1c' for r in result['facts'])
assert bus.agents['Đồ thị tri thức'].memory['calls']==1 and [t['type'] for t in bus.trace]==['REQUEST','INFORM']
checks.append('Real graph agent receives a request and returns source-checked facts')
before=len(Driver.calls)
assert kg.receive({'document_ids':["a1c' MATCH (n) DETACH DELETE n //"]},None)['storage']=='not-requested'
assert len(Driver.calls)==before
checks.append('Unknown or injected IDs never become Cypher code or trigger a query')
doc=next(d for d in kb['documents'] if d['id']=='a1c')
valid=result['facts'][0]
for change in [{'source_url':'https://invalid.example'},{'evidence':'unsupported excerpt'},{'relation':'chắc chắn chẩn đoán'},{'document':'unknown'}]:
    good,bad=ground_facts([dict(valid,**change)],[doc],kb['sources'])
    assert not good and bad==1
    checks.append('Reject graph tampering: '+next(iter(change)))
good,bad=ground_facts([valid,valid],[doc],kb['sources'])
assert good==[valid] and bad==0
checks.append('Duplicate graph rows do not duplicate prompt facts')
payload={'documents':[doc],'graph_evidence':[valid],'plan':{},'question':'HbA1c là gì?'}
prompt=build_messages(payload)[0]['content']
assert 'QUAN HỆ ĐỒ THỊ' in prompt and valid['source']+' → '+valid['relation']+' → '+valid['target'] in prompt
payload['graph_evidence']=[dict(valid,relation='unsupported')]
assert 'unsupported' not in build_messages(payload)[0]['content']
checks.append('Only grounded graph facts enter the actual Qwen message builder')

captured=[]
def generate(payload):
    captured.append(build_messages(payload))
    d=payload['documents'][0]
    return d['text']+' ['+d['id']+']'
with patch.dict(os.environ,{'GLUCOGUIDE_LOCAL_LLM':'1','GLUCOGUIDE_LLAMA_URL':'http://127.0.0.1:11435'}),patch('app.main.graph_driver',Driver),patch('app.local_llm.llama_generate',side_effect=generate):
    client=TestClient(app)
    d=client.post('/api/chat',json={'question':'Type 1 khác type 2 thế nào?'}).json()
    assert d['graph_context_supplied'] and d['graph_status']=='Neo4j'
    assert any(t['receiver']=='Đồ thị tri thức' and t['type']=='REQUEST' for t in d['trace'])
    assert 'QUAN HỆ ĐỒ THỊ' in captured[-1][0]['content']
    checks.append('Production chat passes validated KG through MessageBus into Qwen context')
    with patch('app.main.graph_driver',side_effect=RuntimeError('controlled local outage')):
        d=client.post('/api/chat',json={'question':'Type 1 khác type 2 thế nào?'}).json()
    assert d['graph_status']=='unavailable' and not d['graph_evidence'] and not d['graph_context_supplied']
    assert any(t['sender']=='Đồ thị tri thức' and t['type']=='FAILURE' for t in d['trace'])
    checks.append('Neo4j outage is traced and text RAG remains available without fake graph facts')
    with patch('app.main.graph_driver',side_effect=AssertionError('Safety must return first')),patch('app.local_llm.llama_generate',side_effect=AssertionError('Safety must bypass generation')):
        d=client.post('/api/chat',json={'question':'Đường huyết 350 mg/dL, nôn ói và đau bụng'}).json()
    assert d['safety']['level']=='EMERGENCY' and not d['graph_evidence']
    checks.append('Emergency handling still bypasses graph and language generation')
Path('results/knowledge_agent_tests.json').write_text(json.dumps({'passed':len(checks),'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(checks),'graph-agent checks passed')
