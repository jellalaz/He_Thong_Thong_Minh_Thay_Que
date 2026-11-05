import json, os, math, re, unicodedata
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
from app.agents import Agent, MessageBus
from sklearn.feature_extraction.text import TfidfVectorizer
ROOT=Path(__file__).resolve().parents[1]
for line in (ROOT/'.env').read_text().splitlines() if (ROOT/'.env').exists() else []:
 if '=' in line:
  k,v=line.split('=',1);os.environ.setdefault(k,v)
kb=json.loads((ROOT/'data/knowledge.json').read_text(encoding='utf-8'))
docs=kb['documents']
vec=TfidfVectorizer(strip_accents='unicode',ngram_range=(1,2))
mat=vec.fit_transform([d['title']+' '+' '.join(d['terms'])+' '+d['text'] for d in docs])
schema=json.loads((ROOT/'models/schema.json').read_text())
models={k:joblib.load(ROOT/'models'/f'{v}.joblib') for k,v in [('classification','MLPClassifier'),('regression','MLPRegressor')]}
app=FastAPI(title='GlucoGuide • Giang KT')
app.mount('/assets',StaticFiles(directory=ROOT/'web'),name='assets')
class Request(BaseModel):
 question:str=Field(default='',max_length=3000)
 task:str='knowledge'
 values:dict=Field(default_factory=dict)
def graph_driver():
 return GraphDatabase.driver(os.environ.get('NEO4J_URI','bolt://127.0.0.1:7687'),auth=(os.environ.get('NEO4J_USER','neo4j'),os.environ.get('NEO4J_PASSWORD','')),connection_timeout=3,connection_acquisition_timeout=4,max_transaction_retry_time=0)
@app.get('/')
def home():return FileResponse(ROOT/'web/index.html')
@app.get('/api/metrics')
def metrics():return json.loads((ROOT/'results/model_metrics.json').read_text())
@app.get('/api/schema')
def fields():return schema
@app.get('/api/examples')
def examples():return json.loads((ROOT/'data/examples.json').read_text(encoding='utf-8'))
@app.get('/api/graph')
def graph():
 try:
  with graph_driver() as driver:
   rows=driver.execute_query('MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) RETURN a.name AS source,b.name AS target,r.label AS label,r.document AS document LIMIT 500').records
   edges=[dict(r) for r in rows]
   return {'storage':'Neo4j','nodes':sorted(set(e[k] for e in edges for k in ['source','target'])),'edges':edges}
 except Exception:raise HTTPException(503,'Neo4j chưa kết nối được. Khởi động cơ sở dữ liệu và kiểm tra cấu hình .env.')
@app.post('/api/chat')
def chat(req:Request):
 bus=MessageBus();trace=bus.trace
 bus.register(Agent("Mô hình",lambda payload,b: models[payload["task"]].predict(payload["x"])[0]))
 bus.register(Agent("Truy xuất",lambda payload,b: (mat@vec.transform([payload]).T).toarray().ravel()))
 bus.register(Agent("Đối chiếu",lambda payload,b: {"scope":payload.get("scope","Kiến thức có nguồn"),"allow_diagnosis":False}))
 bus.register(Agent("Phản hồi",lambda payload,b: "\n\n".join(d["text"]+" ["+d["id"]+"]" for d in payload)))
 def msg(sender,receiver,kind,content):trace.append(dict(sender=sender,receiver=receiver,type=kind,content=content))
 msg('Người dùng','Điều phối','REQUEST',req.question or req.task)
 if req.task not in ['knowledge','classification','regression']:raise HTTPException(422,'Bài toán không hợp lệ')
 result=None
 if req.task!='knowledge':
  fields=schema[req.task];missing=[f for f in fields if f not in req.values or req.values[f] in ['',None]]
  if missing:
   msg('Kiểm tra','Phản hồi','REQUEST','Bổ sung: '+', '.join(missing))
   return {'answer':'Cần bổ sung các trường: '+', '.join(missing),'trace':trace,'sources':[],'result':None}
  try:
   values=[float(req.values[f]) for f in fields]
   if not all(math.isfinite(v) for v in values):raise ValueError()
   if any(abs(v)>10000 for v in values):raise ValueError()
  except (ValueError,TypeError):raise HTTPException(422,'Các giá trị phải là số hữu hạn trong miền nhập liệu.')
  model=models[req.task];x=pd.DataFrame([values],columns=fields) if req.task=='classification' else np.array([values])
  pred=bus.request('Điều phối','Mô hình',{'task':req.task,'x':x})
  if req.task=='classification':
   result={'label':str(pred),'scores':dict(zip(map(str,model.classes_),map(float,model.predict_proba(x)[0]))),'scope':'Nhãn dữ liệu tổng hợp; không phải chẩn đoán hay xác suất mắc bệnh.'}
  else:result={'value':float(pred),'scope':'Điểm tiến triển bệnh nghiên cứu; không phải glucose hoặc HbA1c.'}
  msg('Mô hình','Đối chiếu','INFORM',json.dumps(result,ensure_ascii=False))
 q=req.question or ('phân loại nhãn tổng hợp classification High Moderate Low' if req.task=='classification' else 'điểm tiến triển diabetes')
 scores=bus.request('Điều phối','Truy xuất',q)
 selected=[docs[i] for i in np.argsort(-scores)[:3] if scores[i]>max(.04,float(scores.max())*.65)]
 msg('Điều phối','Tri thức','REQUEST',q)
 msg('Tri thức','Đối chiếu','INFORM','Đã truy xuất: '+', '.join(d['id'] for d in selected))
 graph_evidence=[]
 try:
  with graph_driver() as driver:
   graph_evidence=[dict(r) for r in driver.execute_query('MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) WHERE r.document IN $ids RETURN a.name AS source,r.label AS relation,b.name AS target LIMIT 12',ids=[d['id'] for d in selected]).records]
  msg('Neo4j','Tri thức','INFORM',str(len(graph_evidence))+' quan hệ có nguồn')
 except Exception:msg('Neo4j','Tri thức','FAILURE','Không kết nối; câu trả lời chỉ dùng truy xuất văn bản.')
 # Learned workflow policy; rules constrain output when no evidence exists.
 policy=json.loads((ROOT/'models/workflow_policy.json').read_text(encoding='utf-8'))
 state=int(result is not None)*2+int(bool(selected)); action=int(np.argmax(policy['q'][state]))
 if not selected:action=0
 msg('Chính sách RL','Phản hồi','INFORM',{'state':state,'action':policy['actions'][action],'rule':'Thiếu bằng chứng thì yêu cầu làm rõ'})
 answer=bus.request('Điều phối','Phản hồi',selected) if action in (1,2) else 'Tôi chưa tìm thấy bằng chứng phù hợp trong kho tri thức. Bạn hãy nêu rõ chỉ số hoặc chủ đề cần tìm hiểu.'
 if result:
  verdict=bus.request('Điều phối','Đối chiếu',result)
  answer=verdict['scope']+'\n\n'+answer
 msg('Đối chiếu','Phản hồi','INFORM','Giữ đúng phạm vi mô hình, dẫn nguồn tài liệu; không suy ra chẩn đoán từ nhãn tổng hợp.')
 msg('Phản hồi','Người dùng','INFORM','Hoàn thành')
 return {'answer':answer,'result':result,'trace':trace,'sources':[{'id':d['id'],'title':d['title'],'source':kb.get('sources',{}).get(d.get('source'),{})} for d in selected],'graph_evidence':graph_evidence,'generator':'Tổng hợp trích đoạn xác định, không gọi LLM'}

