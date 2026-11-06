"""Local RAG integration and privacy boundaries, without requiring GPU inference."""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.local_llm import llama_generate

c=TestClient(app)
cases=[
 ('identity','Bạn có thể giúp gì cho tôi?',None,'social'),
 ('thanks','cảm ơn nhé',None,'social'),
 ('complaint','Bạn trả lời lan man quá',None,'social'),
 ('types','Type 1 khác type 2 thế nào?','types_compare','diabetes'),
 ('fruit','Tiểu đường có ăn xoài được không?','fruit_whole','fruit'),
 ('rice','Có cần bỏ hẳn cơm trắng không?','rice_portion','meal'),
 ('drink','Trà sữa ít đường có ổn không?','drinks','meal'),
 ('alcohol','Người tiểu đường uống bia được không?','alcohol','meal'),
 ('medicine','Metformin dùng để làm gì?','metformin_info','medicine'),
 ('insulin','Tiêm insulin có phải giai đoạn cuối không?','insulin_info','medicine'),
 ('support','Tôi mới được chẩn đoán tiểu đường, lo quá','new_diagnosis','support'),
 ('log','Lập bảng nhật ký đường huyết giúp tôi','glucose_log','monitor'),
 ('unknown','zzzxxyy',None,None),
 ('outside','Viết cho tôi chương trình python',None,'outside'),
]
with patch('app.main.graph_driver',side_effect=RuntimeError('unit test local graph')):
 for name,q,expected,topic in cases:
  print('CHECK',name,flush=True)
  r=c.post('/api/chat',json={'question':q});assert r.status_code==200,(name,r.text)
  d=r.json();ids=[s['id'] for s in d['sources']]
  if expected:assert expected in ids,(name,ids)
  else:assert not ids,(name,ids)
  if topic:assert d['topic']==topic,(name,d['topic'])
  assert all(s['id'] not in {'meanpressure','triglyceride','model'} for s in d['sources'])
 for q in ['Tôi không ăn cá, thay bằng gì?','Cho tôi ví dụ cụ thể hơn']:
  d=c.post('/api/chat',json={'question':q,'history':[{'role':'user','content':'Gợi ý một bữa trưa dễ nấu cho người tiểu đường'}]}).json()
  assert d['context_used'] and 'meal_example' in [s['id'] for s in d['sources']],d
 d=c.post('/api/chat',json={'question':'Huyết áp 150 có ổn không?'}).json()
 assert 'số trên' in d['answer'] and d['topic']=='bloodpressure'
 assert c.post('/api/chat',json={'question':'Tôi muốn ăn uống tốt hơn','preferred_format':'invalid'}).status_code==422

with patch.dict(os.environ,{'GLUCOGUIDE_LLAMA_URL':'https://example.com'}):
 with patch('httpx.Client') as client:
  try:llama_generate({})
  except RuntimeError:pass
  else:raise AssertionError('External model endpoint accepted')
  client.assert_not_called()
print('19 local dialogue and privacy checks passed')
