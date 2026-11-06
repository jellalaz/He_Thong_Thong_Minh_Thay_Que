"""Check the expanded RAG topics and model-to-conversation handoff."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def ask(**payload):
    response = client.post('/api/chat', json=payload)
    assert response.status_code == 200, response.text
    return response.json()


for question, expected in [
    ('Tôi bị ốm và sốt thì theo dõi sao?', 'sick_day'),
    ('Làm sao kiểm tra bàn chân mỗi ngày?', 'foot_care'),
    ('UACR và eGFR dùng để làm gì?', 'kidney_checks'),
    ('Tôi muốn bắt đầu đi bộ', 'activity_plan'),
]:
    reply = ask(question=question)
    assert expected in [source['id'] for source in reply['sources']], (question, reply['sources'])
    assert any(source['source'].get('url', '').startswith('https://') for source in reply['sources'])

classification = ask(
    question='Giải thích nhãn của mẫu vừa nhập',
    task='classification',
    values={'Age': 32, 'BMI': 19.8, 'HbA1c': 10.4, 'Fasting_Blood_Sugar': 149.5,
            'Blood_Glucose': 88.4, 'Blood_Pressure_Systolic': 94, 'HDL': 40.1, 'LDL': 152.3},
)
assert classification['result']['label'] in ('High', 'Moderate', 'Low')
assert 'macro-F1' in classification['answer'] and 'không phải xác suất' in classification['answer']
assert [s['id'] for s in classification['sources']] == ['classification_scope']

regression = ask(
    question='Giải thích điểm dự đoán của mẫu vừa nhập',
    task='regression',
    values={'age': 59, 'sex': 2, 'bmi': 32.1, 'bp': 101, 's1': 157, 's2': 93.2,
            's3': 38, 's4': 4, 's5': 4.8598, 's6': 87},
)
assert isinstance(regression['result']['value'], float)
assert 'sai số tuyệt đối' in regression['answer'] and 'không phải đường huyết' in regression['answer']
assert [s['id'] for s in regression['sources']] == ['model']

assert client.get('/api/knowledge').json()['total'] == 46
print('7 expanded RAG and model explanation checks passed')
