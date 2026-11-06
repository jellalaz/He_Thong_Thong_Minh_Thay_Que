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
from app.conversation import route
from app.dialogue import plan_turn
from app.answer_display import clean_answer
from app.retrieval import load_knowledge, Retriever
from app.graph_knowledge import GraphKnowledgeAgent
from app import local_llm, feedback
from app import safety
from app.model_explanation import explain
from app.settings import database, browser_url
from typing import Literal
ROOT=Path(__file__).resolve().parents[1]
for line in (ROOT/'.env').read_text().splitlines() if (ROOT/'.env').exists() else []:
 if '=' in line:
  k,v=line.split('=',1);os.environ.setdefault(k,v)
kb=load_knowledge()
docs=kb['documents']
retriever=Retriever(docs)
schema=json.loads((ROOT/'models/schema.json').read_text())
models={k:joblib.load(ROOT/'models'/f'{v}.joblib') for k,v in [('classification','MLPClassifier'),('regression','MLPRegressor')]}
app=FastAPI(title='GlucoGuide • Giang KT')
app.mount('/assets',StaticFiles(directory=ROOT/'web'),name='assets')
class Turn(BaseModel):
 role:Literal["user","assistant"]
 content:str=Field(max_length=3000)

class Request(BaseModel):
 question:str=Field(default='',max_length=3000)
 task:str='knowledge'
 values:dict=Field(default_factory=dict)
 history:list[Turn]=Field(default_factory=list,max_length=64)
 preferred_format:Literal['auto','brief','steps','explain']='auto'
def graph_driver():
 uri=os.environ.get('NEO4J_URI','bolt://127.0.0.1:7687')
 if os.environ.get('GLUCOGUIDE_LOCAL_ONLY')=='1':
  from urllib.parse import urlparse
  if urlparse(uri).hostname not in {'localhost','127.0.0.1','::1'}:raise RuntimeError('Local mode requires a local graph')
 return GraphDatabase.driver(uri,auth=(os.environ.get('NEO4J_USER','neo4j'),os.environ.get('NEO4J_PASSWORD','')),connection_timeout=3,connection_acquisition_timeout=4,max_transaction_retry_time=0)
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
   rows=driver.execute_query('MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) RETURN a.name AS source,b.name AS target,r.label AS label,r.document AS document LIMIT 500', database_=database()).records
   edges=[dict(r) for r in rows]
   return {'storage':'Neo4j','nodes':sorted(set(e[k] for e in edges for k in ['source','target'])),'edges':edges}
 except Exception:raise HTTPException(503,'Chưa kết nối được đồ thị. Vui lòng thử lại sau.')
@app.post('/api/chat')
def chat(req:Request):
 bus=MessageBus();trace=bus.trace
 bus.register(Agent("Mô hình",lambda payload,b: models[payload["task"]].predict(payload["x"])[0]))
 bus.register(Agent("Truy xuất",lambda payload,b: retriever.search(payload)))
 bus.register(Agent("Đối chiếu",lambda payload,b: {"scope":payload.get("scope","Kiến thức có nguồn"),"allow_diagnosis":False}))
 def grounded_reply(payload,b):
  selected=payload[:2]
  if any(d['id']=='meal_example' for d in selected):selected=[d for d in selected if d['id']!='plate']
  return '\n\n'.join(d['text']+' ['+d['id']+']' for d in selected)
 bus.register(Agent('Phản hồi',grounded_reply))
 def msg(sender,receiver,kind,content):trace.append(dict(sender=sender,receiver=receiver,type=kind,content=content))
 msg('Người dùng','Điều phối','REQUEST',req.question or req.task)
 if req.task not in ['knowledge','classification','regression']:raise HTTPException(422,'Bài toán không hợp lệ')
 bus.register(Agent('An toàn',lambda payload,b: safety.classify(payload['question'],payload['history'])))
 assessment=bus.request('Điều phối','An toàn',{'question':req.question,'history':[h.model_dump() for h in req.history]})
 # Triage precedes model input checks, topic routing, Neo4j and language generation.
 if safety.protected(assessment):
  ids=['low','urgent'] if assessment.reason=='possible_hypoglycemia' else ['sick_day','urgent'] if assessment.reason in {'possible_dka','high_glucose_with_vomiting','high_glucose'} else ['medicine'] if assessment.medication_risk and assessment.level=='ROUTINE' else ['urgent'] if assessment.level=='EMERGENCY' else []
  selected=[d for i in ids for d in docs if d['id']==i]
  answer=safety.validate(assessment,clean_answer(safety.response(assessment)))
  msg('An toàn','Người dùng','INFORM',{'level':assessment.level,'reason':assessment.reason,'generation_bypassed':True,'validation':'protected-response'})
  return {'answer':answer,'safety':assessment.public(),'result':None,'trace':trace,'sources':[{'id':d['id'],'title':d['title'],'excerpt':d['text'],'source':kb['sources'].get(d['source'],{})} for d in selected],'graph_evidence':[],'feedback_supported':False,'response_id':None,'response_mode':'rules','generator':'Luật an toàn cục bộ','suggestions':[],'context_used':assessment.context_used,'topic':'low' if assessment.reason=='possible_hypoglycemia' else 'urgent' if assessment.level=='EMERGENCY' else 'medicine' if assessment.medication_risk else 'safety','tone':'urgent' if assessment.level!='ROUTINE' else 'normal'}
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
 plan=route(q,[h.model_dump() for h in req.history])
 plan=plan_turn(q,[h.model_dump() for h in req.history],plan)
 if result is not None:
  plan.update(topic=req.task,ids=['classification_scope'] if req.task=='classification' else ['model'],override=None,intro='',fixed_sources=True,skip_retrieval=False,suggestions=['HbA1c là gì?','Tôi cần kiểm tra đường huyết thế nào?'])
 msg('Hội thoại','Điều phối','INFORM',{'topic':plan['topic'],'context_used':plan['context_used']})
 selected=bus.request('Điều phối','Truy xuất',plan)
 graph_evidence=[]
 graph_state='not-requested'
 graph_agent=GraphKnowledgeAgent(kb,lambda:graph_driver(),database)
 bus.register(Agent('Đồ thị tri thức',graph_agent.receive))
 try:
  graph_result=bus.request('Điều phối','Đồ thị tri thức',{'document_ids':[d['id'] for d in selected]})
  graph_evidence=graph_result['facts'];graph_state=graph_result['storage']
 except Exception:
  graph_state='unavailable'
  msg('Điều phối','Truy xuất','INFORM','Đồ thị chưa sẵn sàng; tiếp tục bằng văn bản KB đã có nguồn.')
 # Learned workflow policy; rules constrain output when no evidence exists.
 policy=json.loads((ROOT/'models/workflow_policy.json').read_text(encoding='utf-8'))
 state=int(result is not None)*2+int(bool(selected)); action=int(np.argmax(policy['q'][state]))
 if not selected:action=0
 msg('Chính sách RL','Phản hồi','INFORM',{'state':state,'action':policy['actions'][action],'rule':'Thiếu bằng chứng thì yêu cầu làm rõ'})
 answer=bus.request('Điều phối','Phản hồi',selected) if action in (1,2) else 'Tôi chưa tìm thấy bằng chứng phù hợp trong kho tri thức. Bạn hãy nêu rõ chỉ số hoặc chủ đề cần tìm hiểu.'
 if plan['override'] is not None:answer=plan['override']
 elif plan['intro']:answer=plan['intro']+'\n\n'+answer
 if result:
  verdict=bus.request('Điều phối','Đối chiếu',result)
  answer=explain(req.task,result)
 msg('Đối chiếu','Phản hồi','INFORM','Giữ đúng phạm vi mô hình, dẫn nguồn tài liệu; không suy ra chẩn đoán từ nhãn tổng hợp.')
 response_mode="kb-rules"
 feedback_id=None;presentation=0
 if local_llm.enabled() and selected and not plan.get('guarded') and result is None:
  feedback_id,presentation=feedback.choose(plan['topic'],req.preferred_format)
  plan['format']=feedback.FORMATS[presentation]
  msg('Chính sách phản hồi','Điều phối','INFORM',{'strategy':plan['format'],'selected_by':'user' if req.preferred_format!='auto' else 'local-Q'})
 if local_llm.enabled() and result is None:
  bus.register(Agent('Kiểm chứng phản hồi',local_llm.verify))
  bus.register(Agent('Ngôn ngữ cục bộ',local_llm.respond))
  try:
   generated=bus.request('Điều phối','Ngôn ngữ cục bộ',{'question':q,'plan':plan,'documents':selected,'graph_evidence':graph_evidence,'fallback':answer,'history':[h.model_dump() for h in req.history]})
   answer=generated['answer'];response_mode=generated['mode']
   msg('Kiểm chứng phản hồi','Điều phối','INFORM',{'mode':generated['mode'],'reason':generated['reason']})
  except Exception as exc:
   msg('Ngôn ngữ cục bộ','Điều phối','FAILURE',type(exc).__name__+'; sử dụng phản hồi KB')
 msg('Phản hồi','Người dùng','INFORM','Hoàn thành')
 if response_mode.startswith('qwen'):
  cited=set(re.findall(r'\[([a-z0-9_]+)\]',answer))
  selected=[d for d in selected if d['id'] in cited]
  graph_evidence=[r for r in graph_evidence if r['document'] in cited]
 answer=clean_answer(answer)
 answer=safety.validate(assessment,answer)
 return {'answer':answer,'safety':assessment.public(),'result':result,'trace':trace,'sources':[{'id':d['id'],'title':d['title'],'excerpt':d['text'],'retrieval_score':d.get('retrieval_score'),'source':kb.get('sources',{}).get(d.get('source'),{})} for d in selected],'graph_evidence':graph_evidence,'graph_status':graph_state,'graph_context_supplied':bool(graph_evidence) and response_mode.startswith('qwen'),'feedback_supported':bool(feedback_id),'response_id':feedback_id,'response_mode':response_mode,'generator':('Qwen3 cục bộ + RAG và KG' if graph_evidence and response_mode.startswith('qwen') else 'Qwen3 cục bộ + RAG' if response_mode.startswith('qwen') else 'KB và luật có nguồn'),'suggestions':plan['suggestions'],'context_used':plan['context_used'],'topic':plan['topic'],'tone':plan['tone']}


@app.get('/api/knowledge')
def knowledge(q:str=''):
 from app.conversation import norm
 found=[d for d in docs if not q or norm(q) in norm(d['title']+' '+' '.join(d['terms'])+' '+d['text'])]
 return {'documents':[dict(d,source_info=kb['sources'].get(d['source'],{})) for d in found],'total':len(docs)}

@app.get('/api/status')
def status():
 model_name='Qwen3 4B · RAG local' if os.environ.get('GLUCOGUIDE_LLAMA_URL') else 'Qwen3 1.7B LoRA' if local_llm.enabled() else None
 try:
  g=graph();return {'neo4j':True,'nodes':len(g['nodes']),'edges':len(g['edges']),'documents':len(docs),'neo4j_browser':browser_url(),'local_llm':local_llm.enabled(),'model_name':model_name,'local_only':os.environ.get('GLUCOGUIDE_LOCAL_ONLY')=='1'}
 except HTTPException:return {'neo4j':False,'nodes':0,'edges':0,'documents':len(docs),'neo4j_browser':browser_url(),'local_llm':local_llm.enabled(),'model_name':model_name,'local_only':os.environ.get('GLUCOGUIDE_LOCAL_ONLY')=='1'}

class FeedbackRequest(BaseModel):
 response_id:str=Field(min_length=10,max_length=80)
 helpful:bool
@app.post('/api/feedback')
def rate(req:FeedbackRequest):
 if not local_llm.enabled():raise HTTPException(404,'Phản hồi chỉ có ở bản local.')
 result=feedback.record(req.response_id,req.helpful)
 if result is None:raise HTTPException(409,'Lượt này đã được đánh giá hoặc đã hết hạn.')
 return result
