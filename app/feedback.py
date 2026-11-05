"""Local one-step Q learning over presentation styles; never changes medical guards."""
import json,secrets,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'.local-training/feedback_q.json'
LOCK=threading.Lock()
PENDING={}
def choose(topic):
 with LOCK:
  q=json.loads(FILE.read_text()) if FILE.exists() else {'knowledge':[0.0,0.0],'ratings':0}
  action=max(range(2),key=lambda i:q['knowledge'][i])
  token=secrets.token_urlsafe(16)
  PENDING[token]=action
  if len(PENDING)>500:PENDING.pop(next(iter(PENDING)))
  return token,action

def record(token,helpful):
 with LOCK:
  action=PENDING.pop(token,None)
  if action is None:return None
  q=json.loads(FILE.read_text()) if FILE.exists() else {'knowledge':[0.0,0.0],'ratings':0}
  reward=1.0 if helpful else -1.0
  q['knowledge'][action]+=0.2*(reward-q['knowledge'][action])
  q['ratings']+=1
  FILE.parent.mkdir(parents=True,exist_ok=True)
  tmp=FILE.with_suffix('.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(FILE)
  return {'saved':True,'strategy':('trực tiếp','từng bước')[action],'ratings':q['ratings']}
