from pathlib import Path
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
r=Path(__file__).resolve().parents[1];c=TestClient(app);examples=json.loads((r/'data/examples.json').read_text())
cases=[('knowledge',{'question':'HbA1c là gì?'},200),('unknown',{'question':'zzzxxyy'},200),('classification',{'task':'classification','values':examples['classification']},200),('regression',{'task':'regression','values':examples['regression']},200),('missing',{'task':'classification','values':{}},200),('invalid',{'task':'classification','values':{**examples['classification'],'Age':'nan'}},422),('bad_task',{'task':'unknown'},422)]
results=[]
for name,payload,status in cases:
 response=c.post('/api/chat',json=payload);body=response.json();assert response.status_code==status,(name,body)
 if name=='unknown':assert body['sources']==[]
 if name=='knowledge':assert body['sources'][0]['id']=='a1c' and body['graph_evidence']
 if name=='classification':assert body['result']['label'] in ['High','Moderate','Low']
 if name=='regression':assert isinstance(body['result']['value'],float)
 if name=='missing':assert body['result'] is None
 results.append({'case':name,'status':status,'passed':True,'response':body})
with patch('app.main.graph_driver',side_effect=RuntimeError('controlled outage')):
 response=c.post('/api/chat',json={'question':'HbA1c'});body=response.json();assert response.status_code==200 and any(t['type']=='FAILURE' for t in body['trace'])
 assert c.get('/api/graph').status_code==503
 results.append({'case':'controlled_neo4j_outage','passed':True,'response':body})
g=c.get('/api/graph').json();assert g['storage']=='Neo4j' and len(g['nodes'])>0
(r/'results/api_scenarios.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(results),'nodes':len(g['nodes']),'edges':len(g['edges'])}))
