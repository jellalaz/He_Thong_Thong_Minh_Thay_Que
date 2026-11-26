"""Replay the paired held-out predictions and exercise the V3 policy in isolation."""
import json
import random
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app import feedback, v2
from app.main import app
from app.study_review import presentation_policy

ROOT = Path(__file__).resolve().parents[1]


def evaluate_models(dataset):
    frame = pd.read_csv(ROOT / 'data/v2' / f'{dataset}.csv')
    stored = pd.read_csv(ROOT / 'results/v2' / f'{dataset}_test_predictions.csv')
    test = frame.loc[stored.row]
    assert test.split.eq('test').all() and set(stored.row) == set(frame.index[frame.split.eq('test')])
    y = test.target.to_numpy()
    x = test.drop(columns=['split', 'target'])
    labels = {}
    for version in ('v1', 'v2'):
        model, _ = v2.checkpoint(dataset, version)
        scores = model.predict_proba(x)[:, list(model.classes_).index(1)]
        np.testing.assert_allclose(scores, stored[f'{version}_254_prob'], atol=1e-12, rtol=0)
        labels[version] = scores >= .5
    same = labels['v1'] == labels['v2']
    index = int(test.index[np.flatnonzero(~same)[0]])
    example = {name: None if pd.isna(value) else float(value) for name, value in x.loc[index].items()}
    demo = {'row':index, 'values':example, 'actual':int(test.loc[index, 'target']),
            'v1_score':float(stored.loc[stored.row==index, 'v1_254_prob'].iloc[0]),
            'v2_score':float(stored.loc[stored.row==index, 'v2_254_prob'].iloc[0])}
    return {'demo':demo, 'test_n': len(y), 'agree': int(same.sum()), 'both_correct': int(((labels['v1']==y)&same).sum()),
            'both_wrong': int(((labels['v1']!=y)&same).sum()), 'disagree': int((~same).sum()),
            'only_v1_correct': int(((labels['v1']==y)&~same).sum()),
            'only_v2_correct': int(((labels['v2']==y)&~same).sum())}


def evaluate_policy():
    # Three explicit simulated preferences, one per context. Freeze Q during evaluation.
    rng = random.Random(254)
    contexts = ['agree', 'missing', 'disagree']
    with patch('app.feedback.secrets.randbelow', rng.randrange):
        for i in range(600):
            k = i % len(contexts)
            p = presentation_policy({'dataset':'pima', 'context':contexts[k]}, None)
            feedback.record(p['feedback_id'], p['style'] == feedback.FORMATS[k])
    learned = feedback.state()['topics']
    best = [int(np.argmax(learned['study/pima/'+context])) for context in contexts]
    assert best == [0, 1, 2]
    return {'simulated_ratings':600, 'seed':254, 'initial_greedy_correct':1,
            'final_greedy_correct':3, 'contexts':contexts, 'greedy_actions':best}


def main():
    output = {'datasets': {key:evaluate_models(key) for key in ('pima','early_stage')}}
    checks = []
    with TemporaryDirectory() as tmp, patch.object(v2, 'AUDIT', Path(tmp)/'legacy.jsonl'), \
         patch.object(feedback, 'FILE', Path(tmp)/'q.json'), patch.dict('os.environ', GLUCOGUIDE_LOCAL_LLM='1'):
        client = TestClient(app)
        for dataset, spec in v2.registry()['datasets'].items():
            for version in ('v1','v2'):
                args = dict(workflow='v3', dataset=dataset, version=version, values=spec['example'])
                response = client.post('/api/v2/predict', json=args)
                response.raise_for_status()
                body = response.json()
                assert body['system_version']=='3.0' and body['graph_status']=='Neo4j' and body['sources']
                assert body['audit']['stored'] and len(body['comparison']['sensitivity'])==3
                assert len({row['receiver'] for row in body['trace'] if row['type']=='REQUEST'})==8
                ref = client.post('/api/v2/predict', json={**args, 'workflow':'v2'}).json()
                assert ref['prediction'] == body['prediction'] and ref['system_version'] == '2.0'
                other = 'v2' if version=='v1' else 'v1'
                peer_ref = client.post('/api/v2/predict', json={**args, 'workflow':'v2', 'version':other}).json()
                assert np.isclose(body['comparison']['peer_score'], peer_ref['prediction']['positive_label_score'])
                for row in body['comparison']['sensitivity']:
                    masked = dict(args['values'], **{row['feature']:None})
                    modified = v2.validate_data({**args, 'values':masked}, None)
                    score = v2.predict({**args, 'data':modified}, None)['positive_label_score']
                    assert np.isclose(score - body['prediction']['positive_label_score'], row['delta'])
                token = body['presentation']['feedback_id']
                with patch.object(feedback, 'FILE', Path(tmp)/'api-votes.json'):
                    vote = {'response_id':token, 'helpful':False}
                    assert client.post('/api/feedback', json=vote).json()['reward']==-1
                    assert client.post('/api/feedback', json=vote).status_code==409
                checks.append(f'{dataset}/{version}')
        with patch.object(v2,'checkpoint',side_effect=AssertionError('priority must bypass inference')):
            emergency = client.post('/api/v2/predict', json={'workflow':'v3','question':'Mẹ tôi bất tỉnh'}).json()
            assert emergency['prediction'] is None and 'presentation' not in emergency
            assert client.post('/api/v2/predict', json={'workflow':'v3','values':{}}).status_code==422
        records=[json.loads(line) for line in (Path(tmp)/'audit-v3.jsonl').read_text().splitlines()]
        assert len(records)==6 and all(r['system_version']=='3.0' for r in records)
        output['policy'] = evaluate_policy()
    output['integration'] = checks + ['priority bypass','invalid input','audit','single-use feedback','V2 parity','peer parity','individual masking parity']
    target = ROOT/'results/v3/study_review.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
