"""Local Qwen response agent with bounded text and graph evidence; no cloud fallback."""
import os,re,threading,time
from contextlib import nullcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
_lock=threading.Lock();_model=None;_tokenizer=None
GUARDED={'bloodpressure','a1c','testing','low','urgent','medicine','model','classification','meanpressure','demographics','sick_day'}
def enabled():return os.environ.get('GLUCOGUIDE_LOCAL_LLM')=='1'

def llama_generate(payload):
 from urllib.parse import urlparse
 import httpx
 from app.local_prompt import build_messages
 url=os.environ['GLUCOGUIDE_LLAMA_URL']
 parsed=urlparse(url)
 if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.username or parsed.password:
  raise RuntimeError('Only a loopback model endpoint is allowed')
 headers={}
 if os.environ.get('GLUCOGUIDE_LLAMA_KEY_FILE'):
  headers['Authorization']='Bearer '+Path(os.environ['GLUCOGUIDE_LLAMA_KEY_FILE']).read_text().strip()
 with httpx.Client(timeout=httpx.Timeout(180,connect=3),trust_env=False) as client:
  r=client.post(url.rstrip('/')+'/v1/chat/completions',headers=headers,json={'model':'local-qwen','messages':build_messages(payload),'max_tokens':650,'temperature':.2,'top_p':.85,'repeat_penalty':1.08,'seed':254,'chat_template_kwargs':{'enable_thinking':False}})
  r.raise_for_status()
  data=r.json()
  text=data['choices'][0]['message'].get('content') or ''
  text=re.sub(r'<think>[\s\S]*?</think>','',text).strip()
  return text
def load():
 global _model,_tokenizer
 if _model is not None:return
 os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
 import torch
 from transformers import AutoModelForCausalLM,AutoTokenizer
 from peft import PeftModel
 base=ROOT/'.local-models/Qwen3-1.7B';adapter=ROOT/'models/qwen_adapter'
 if not (adapter/'adapter_config.json').exists():raise RuntimeError('Chưa có checkpoint LoRA cục bộ')
 _tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True)
 m=AutoModelForCausalLM.from_pretrained(base,local_files_only=True,torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,attn_implementation='sdpa')
 _model=PeftModel.from_pretrained(m,adapter,local_files_only=True).to('cuda' if torch.cuda.is_available() else 'cpu').eval()
 torch.set_num_threads(6)
def respond(payload,bus):
 if payload['plan']['topic']=='social':
  return {'answer':payload['fallback'],'mode':'rules','reason':'Câu giao tiếp dùng nhánh đã kiểm tra; checkpoint hội thoại thử nghiệm không được triển khai.'}
 guarded=payload['plan'].get('guarded')
 if guarded is None:guarded=payload['plan']['topic'] in GUARDED or bool(re.search(r'\d',payload['question']))
 if payload['plan']['tone']=='urgent' or guarded:
  return {'answer':payload['fallback'],'mode':'rules','reason':'Thông số, thuốc và tình huống khẩn cấp được đối chiếu bằng luật có nguồn.'}
 if not payload['documents'] and payload['plan']['topic']!='social':return {'answer':payload['fallback'],'mode':'rules','reason':'Thiếu tài liệu; không sinh câu trả lời y tế.'}
 with _lock:
  if os.environ.get('GLUCOGUIDE_LLAMA_URL'):
   start=time.perf_counter();draft=llama_generate(payload)
   verdict=bus.request('Ngôn ngữ cục bộ','Kiểm chứng phản hồi',{'draft':draft,'documents':payload['documents'],'graph_evidence':payload.get('graph_evidence',[]),'fallback':payload['fallback']})
   if verdict['mode']=='rules':
    revised=llama_generate(dict(payload,repair=draft,repair_reason=verdict['reason']))
    verdict=bus.request('Ngôn ngữ cục bộ','Kiểm chứng phản hồi',{'draft':revised,'documents':payload['documents'],'graph_evidence':payload.get('graph_evidence',[]),'fallback':payload['fallback']})
   if verdict['mode']=='qwen-lora':verdict['mode']='qwen4-rag'
   return dict(verdict,seconds=round(time.perf_counter()-start,3))
  load();import torch
  from app.local_prompt import build_messages
  messages=build_messages(payload)
  inputs=_tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False,return_tensors='pt').to(_model.device)
  if inputs.shape[1]>4096:return {'answer':payload['fallback'],'mode':'rules','reason':'Ngữ cảnh vượt giới hạn suy luận cục bộ.'}
  start=time.perf_counter()
  use_adapter=os.environ.get('GLUCOGUIDE_QWEN_ADAPTER','1')=='1'
  with torch.inference_mode(), (nullcontext() if use_adapter else _model.disable_adapter()):
   out=_model.generate(inputs,attention_mask=torch.ones_like(inputs),max_new_tokens=480,do_sample=False,repetition_penalty=1.08,pad_token_id=_tokenizer.eos_token_id,use_cache=True)
  draft=_tokenizer.decode(out[0,inputs.shape[1]:],skip_special_tokens=True).strip()
  # This is a conservative consistency filter, not a clinical fact checker.
  verdict=bus.request('Ngôn ngữ cục bộ','Kiểm chứng phản hồi',{'draft':draft,'documents':payload['documents'],'graph_evidence':payload.get('graph_evidence',[]),'fallback':payload['fallback']})
  if verdict['mode']=='qwen-lora' and not use_adapter:verdict['mode']='qwen-rag'
  return dict(verdict,seconds=round(time.perf_counter()-start,3))
def verify(payload,bus):
 from app.retrieval import normalize
 from app.graph_knowledge import ground_facts
 _,bad_graph=ground_facts(payload.get('graph_evidence',[]),payload['documents'])
 if bad_graph:return {'answer':payload['fallback'],'mode':'rules','reason':'Quan hệ đồ thị không khớp tài liệu; dùng nội dung KB đã kiểm tra.'}
 draft=re.sub(r'^\s*\d+[.)]\s+', '- ', payload['draft'], flags=re.M).strip()
 draft=re.sub(r'^Dưới đây là (?:bản nháp|câu trả lời) (?:được |đã )?(?:chỉnh sửa|sửa lại)[^:\n]*:\s*','',draft,flags=re.I)
 context=' '.join(d['text'] for d in payload['documents']);ids={d['id'] for d in payload['documents']}
 unknown=set(re.findall(r'\[([a-z0-9_]+)\]',draft))-ids
 denied_evidence=bool(re.search(r'(?:không (?:được )?(?:đề cập|nêu|có)|chưa (?:đề cập|có))[^.!?\n]*\[[a-zA-Z][a-zA-Z0-9_-]*\]',draft,re.I))
 numbers=set(re.findall(r'\d+(?:[.,]\d+)?',draft))-set(re.findall(r'\d+(?:[.,]\d+)?',context))
 spelled=set(re.findall(r'\b(?:mot|hai|ba|bon|nam|sau|bay|tam|chin|muoi)(?:\s+(?:den|hoac|hai|ba|bon|nam|muoi))?\s+(?:qua|gam|phut|vien|don vi|lan moi ngay)\b',normalize(draft)))
 if any(value not in normalize(context) for value in spelled):numbers.add('lượng không có trong nguồn')
 food_error=False
 if ids & {'meal_example','plate','carb','rice_portion','fruit_whole','fruit'}:
  evidence=normalize(context+' '+' '.join(' '.join(d.get('terms',[])) for d in payload['documents']))
  food_names=['dua hau','ca rot','ca chua','cai xanh','rau bina','bong cai','xa lach','ca hoi','thit ga','thit heo','thit bo','thit cuu','ca ngu','khoai lang','gao lut','sua','xoai','chuoi','qua oi','qua tao','nho','qua le','pho','bun','banh mi']
  normalized=normalize(draft)
  food_error=any(re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',normalized) and name not in evidence for name in food_names)
  food_error=food_error or bool(re.search(r'(?:rau|salad)[^\n.]{0,90}(?:dua hau|xoai|chuoi)|thit nac (?:xa lach|salad)',normalized))
 unsafe=any(x in draft.lower() for x in ['chắc chắn mắc','chẩn đoán của tôi','ngừng thuốc ngay','bạn nên tăng liều','bạn hãy tăng liều','bạn nên giảm liều','bạn hãy giảm liều','system prompt','cách trả lời lượt này','tài liệu cung cấp sau đây'])
 mixed_language=bool(re.search(r'\b(?:enough|however|because|therefore|you should|your blood|i understand)\b',draft,re.I))
 if not draft or unknown or denied_evidence or numbers or unsafe or food_error or mixed_language or len(draft)<30 or (ids and not set(re.findall(r'\[([a-z0-9_]+)\]',draft))):
  reason='nguồn không hỗ trợ nội dung đang nói; không đưa thêm kiến thức ngoài tài liệu' if denied_evidence else 'nguồn không hợp lệ' if unknown else 'số liệu ngoài tài liệu' if numbers else 'phạm vi điều trị' if unsafe else 'tự thêm món hoặc phân nhóm thực phẩm không có trong nguồn; chỉ dùng đúng ví dụ nguồn' if food_error else 'xen tiếng Anh, cần viết lại bằng tiếng Việt' if mixed_language else 'thiếu nội dung hoặc dẫn nguồn'
  return {'answer':payload['fallback'],'mode':'rules','reason':'Dùng KB vì bản sinh có '+reason+'.'}
 return {'answer':draft,'mode':'qwen-lora','reason':'Đã kiểm tra mã nguồn và số liệu; chưa thay thế đánh giá chuyên gia.'}
