"""Real checkpoint parity, dataset split integrity, version contracts and failure paths."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from app import v2

ROOT=Path(__file__).resolve().parents[1]
checks=[]
client=TestClient(app)
registry=client.get('/api/v2/study').json()
audit=ROOT/'.runtime/v2-test-audit.jsonl'
audit.unlink(missing_ok=True)
examples=[]
with patch.object(v2,'AUDIT',audit):
 for dataset in ['pima','early_stage']:
  data=pd.read_csv(ROOT/'data/v2'/f'{dataset}.csv')
  features=[f['name'] for f in registry['datasets'][dataset]['features']]
  assert not data[features].duplicated().any()
  groups={s:set(data.index[data.split==s]) for s in ['train','validation','test']}
  assert all(not groups[a]&groups[b] for a,b in [('train','test'),('train','validation'),('validation','test')])
  checks.append(dataset+': unique feature rows and disjoint train/validation/test')
  pred=pd.read_csv(ROOT/'results/v2'/f'{dataset}_test_predictions.csv')
  assert np.array_equal(data.loc[pred.row,'target'].to_numpy(),pred.actual.to_numpy())
  for version in ['v1','v2']:
   model=joblib.load(ROOT/'models/v2'/f'{dataset}_{version}.joblib')
   prob=model.predict_proba(data.loc[pred.row,features])[:,1]
   assert np.allclose(prob,pred[f'{version}_254_prob'],rtol=0,atol=1e-12)
   request={'dataset':dataset,'version':version,'values':registry['datasets'][dataset]['example'],'question':'HbA1c là gì?'}
   response=client.post('/api/v2/predict',json=request);assert response.status_code==200,response.text
   body=response.json();examples.append(body)
   assert body['prediction']['model_version']==dataset+'-'+version+'-seed254'
   expected_layers = [64, 32, 16, 8, 4] if version == 'v2' else [64, 32, 16]
   assert body['prediction']['hidden_layers'] == expected_layers
   assert body['sources'] and body['graph_evidence'] and body['audit']['stored']
   roles={m['receiver'] for m in body['trace'] if m['type']=='REQUEST'}
   assert roles=={'Data','Prediction','Rule','KG/RAG','Explanation','Monitoring'}
   assert all(m['request_id']==body['request_id'] and m['system_version']=='2.0' for m in body['trace'])
   assert body['rules']['allow_diagnosis'] is False
   checks.append(dataset+'/'+version+': checkpoint/test probability parity; real six-role workflow and grounded graph')
  bad={'dataset':dataset,'values':{}}
  assert client.post('/api/v2/predict',json=bad).status_code==422
  values=dict(registry['datasets'][dataset]['example']);values[features[0]]='nan'
  assert client.post('/api/v2/predict',json={'dataset':dataset,'values':values}).status_code==422
  checks.append(dataset+': missing fields and non-finite values rejected')
 with patch('app.v2.checkpoint',side_effect=AssertionError('Model must be bypassed')):
  body=client.post('/api/v2/predict',json={'question':'Mẹ tôi đang bất tỉnh','values':{}}).json()
  assert body['prediction'] is None and body['safety']['level']=='EMERGENCY'
 checks.append('Priority safety bypasses model and feature validation')
 with patch('app.main.graph_driver',side_effect=RuntimeError('controlled graph outage')):
  body=client.post('/api/v2/predict',json={'values':registry['datasets']['pima']['example']}).json()
  assert body['graph_status']=='unavailable' and body['sources'] and not body['graph_evidence']
 checks.append('Controlled graph outage is explicit and retains KB evidence')
 records=[json.loads(line) for line in audit.read_text().splitlines()]
 assert len({r['request_id'] for r in records})==len(records)
 assert not any(key in r for r in records for key in ['values','features','question','answer','trace'])
 checks.append('Persistent audit contains request/version metadata without raw inputs or answer text')
 (ROOT/'results/v2/agent_examples.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n')
result={'passed':len(checks),'checks':checks}
(ROOT/'results/v2/integration_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
audit.unlink(missing_ok=True)
