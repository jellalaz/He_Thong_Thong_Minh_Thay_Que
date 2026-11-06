from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.answer_display import clean_answer
from app import local_llm

assert clean_answer('Đây là phần giải thích. [overview]') == 'Đây là phần giải thích.'
assert clean_answer('Một bữa ăn. Ví dụ này được lấy từ [meal_example].') == 'Một bữa ăn.'
assert clean_answer('Theo [overview], Tiểu đường là bệnh mạn tính.') == 'Tiểu đường là bệnh mạn tính.'
assert clean_answer('Đây là phần giải thích. Thông tin này không được đề cập trong [overview].') == 'Đây là phần giải thích.'
assert clean_answer('Xem [a1c] và [testing].') == 'Xem và.'
draft='Triệu chứng có thể do nhiều nguyên nhân. Thông tin này không được đề cập trong [overview].'
r=local_llm.verify({'draft':draft,'documents':[{'id':'overview','text':'Định nghĩa tiểu đường.'}],'fallback':'KB'},None)
assert r['mode']=='rules'
with patch('app.main.graph_driver',side_effect=RuntimeError('test')):
 c=TestClient(app)
 d=c.post('/api/chat',json={'question':'bị tiểu đường thì đi tiểu có ra máu không'}).json()
 assert not d['sources'] and '[overview]' not in d['answer']
 assert 'nhiễm trùng' not in d['answer'] and d['safety']['level']=='URGENT'
 d=c.post('/api/chat',json={'question':'HbA1c 6,2% là gì?'}).json()
 assert '[a1c]' not in d['answer'] and d['sources'][0]['id']=='a1c'
print('8 citation display and unsupported-source checks passed')
