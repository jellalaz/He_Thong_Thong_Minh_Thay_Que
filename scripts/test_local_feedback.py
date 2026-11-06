import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app import feedback
old=feedback.FILE
feedback.FILE=Path('.runtime/feedback-test.json')
if feedback.FILE.exists():feedback.FILE.unlink()
os.environ['GLUCOGUIDE_LOCAL_LLM']='1'
try:
 c=TestClient(app)
 token,action=feedback.choose('meal');assert action==0
 r=c.post('/api/feedback',json={'response_id':token,'helpful':False});assert r.status_code==200 and r.json()['ratings']==1
 assert c.post('/api/feedback',json={'response_id':token,'helpful':False}).status_code==409
 token2,action2=feedback.choose('meal');assert action2==1
 r=c.post('/api/feedback',json={'response_id':token2,'helpful':True});assert r.status_code==200
 token3,action3=feedback.choose('meal','explain');assert action3==2
 assert c.post('/api/feedback',json={'response_id':token3,'helpful':True}).json()['strategy']=='explain'
 _,other_action=feedback.choose('medicine');assert other_action==0
 assert feedback.FILE.exists()
 print('Local feedback learns per topic, honors explicit format, and rejects duplicate ratings')
finally:
 feedback.PENDING.clear()
 feedback.FILE.unlink(missing_ok=True)
 feedback.FILE=old
 os.environ.pop('GLUCOGUIDE_LOCAL_LLM',None)
