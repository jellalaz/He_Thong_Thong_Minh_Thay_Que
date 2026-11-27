"""Check V3 model selection and parity with saved test scores through the API."""
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app import deep_study
from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def main():
    client = TestClient(app)
    with patch('app.main.graph_driver', side_effect=RuntimeError('offline model verification')):
        for dataset, record in deep_study.results()['datasets'].items():
            assert sorted(record['summary']) == ['cnn', 'mlp', 'transformer']
            assert record['ranking'][0] == max(record['summary'], key=lambda f: record['summary'][f]['validation_f1'])
            test = record['test']
            frame = pd.read_csv(ROOT / 'data/v2' / f'{dataset}.csv').drop(columns=['split', 'target'])
            for family in record['ranking']:
                weights, _ = deep_study.checkpoint(dataset, family)
                actual = deep_study.probabilities(family, frame.iloc[test['rows']].to_numpy(), weights)
                np.testing.assert_allclose(actual, test['scores'][family], atol=2e-6, rtol=2e-6)
            expected, peer = record['ranking'][:2]
            for version in (None, 'auto'):
                payload = {'workflow': 'v3', 'dataset': dataset, 'values': record['demo']['values']}
                if version:
                    payload['version'] = version
                response = client.post('/api/v2/predict', json=payload)
                response.raise_for_status()
                status = response.json()
                prediction = status['prediction']
                assert prediction['family'] == expected
                assert prediction['checkpoint_file'] == record['summary'][expected]['checkpoint']['file']
                assert prediction['checkpoint_sha256'] == record['summary'][expected]['checkpoint']['sha256']
                assert status['comparison']['peer_version'] == peer
                assert status['comparison']['sensitivity']
                assert not status['rules']['allow_diagnosis']
                assert {m['model_version'] for m in status['trace']} == {prediction['model_version']}
                np.testing.assert_allclose(prediction['positive_label_score'], record['demo']['scores'][expected], atol=2e-6)
            print(dataset, expected, 'selected model and retained test parity')
            historic = client.post('/api/v2/predict', json=dict(
                workflow='v2', dataset=dataset, values=record['demo']['values'])).json()
            assert historic['prediction']['model_version'] == f'{dataset}-v2-seed254'
        with patch('app.deep_study.predict', side_effect=AssertionError('Emergency must bypass inference')):
            urgent = client.post('/api/v2/predict', json={
                'workflow': 'v3', 'question': 'Mẹ tôi đang bất tỉnh',
            }).json()
            assert urgent['prediction'] is None and urgent['safety']['level'] == 'EMERGENCY'
    print('V2 compatibility and priority-safety check passed')


if __name__ == '__main__':
    main()
