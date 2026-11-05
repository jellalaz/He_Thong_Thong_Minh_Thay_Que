"""Check the public deployment, including real Neo4j reads and model inference."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
base = sys.argv[1].rstrip('/')
checks = []
with httpx.Client(base_url=base, timeout=60) as client:
    def get(path):
        response = client.get(path)
        response.raise_for_status()
        return response

    def chat(payload):
        response = client.post('/api/chat', json=payload)
        response.raise_for_status()
        return response.json()

    assert 'GlucoGuide' in get('/').text
    for path in ['/assets/style.css', '/assets/app.js', '/assets/data_catalog.json']:
        assert get(path).content
    checks.append('page_and_assets')
    status = get('/api/status').json()
    assert status['neo4j'] and status['nodes'] == 60 and status['edges'] == 32
    checks.append('neo4j_live_connection')
    graph = get('/api/graph').json()
    assert graph['storage'] == 'Neo4j' and len(graph['edges']) == 32
    checks.append('graph_relations')
    first = chat({'question': 'HbA1c 6,2% nghĩa là gì?'})
    assert first['sources'][0]['id'] == 'a1c' and first['graph_evidence']
    checks.append('sourced_answer_with_graph')
    follow = chat({'question':'Vậy 7,1% thì sao?', 'history':[{'role':'user','content':'HbA1c là gì?'}]})
    assert follow['context_used'] and '7.1%' in follow['answer']
    checks.append('contextual_followup')
    assert not chat({'question':'zzzxxyy'})['sources']
    checks.append('unknown_question')
    assert 'bổ sung đơn vị' in chat({'question':'Đường huyết 7 thì sao?'})['answer']
    checks.append('missing_measurement_unit')
    assert chat({'question':'Bố tôi đang bất tỉnh'})['tone'] == 'urgent'
    checks.append('urgent_routing')
    samples = get('/api/examples').json()
    classification = chat({'task':'classification','values':samples['classification']})['result']
    assert classification['label'] == 'High' and abs(sum(classification['scores'].values()) - 1) < 1e-8
    checks.append('classification')
    prediction = chat({'task':'regression','values':samples['regression']})['result']['value']
    assert abs(prediction - 207.53) < .01
    changed = dict(samples['regression'], bmi=28)
    second = chat({'task':'regression','values':changed})['result']['value']
    assert abs(second - prediction) > 1
    checks.append('regression_and_changed_input')
    assert chat({'task':'classification','values':{}})['result'] is None
    assert client.post('/api/chat',json={'task':'unknown'}).status_code == 422
    assert client.post('/api/chat',json={'task':'classification','values':dict(samples['classification'],Age='nan')}).status_code == 422
    checks.append('input_validation')
    assert get('/api/knowledge?q=duong%20huyet').json()['documents']
    checks.append('knowledge_search')
result = {'url':base, 'checked_at':datetime.now(timezone.utc).isoformat(), 'passed':len(checks), 'checks':checks, 'graph':status, 'classification':classification, 'regression':prediction}
(root/'results/deployment_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'url':base,'passed':len(checks),'nodes':status['nodes'],'edges':status['edges']}))
