"""Local-only LoRA response agent. Activated explicitly; never falls back to a cloud API."""
import os,re,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
_lock=threading.Lock();_model=None;_tokenizer=None
GUARDED={'bloodpressure','a1c','testing','low','urgent','medicine','model','classification','meanpressure','demographics','sick_day'}
def enabled():return os.environ.get('GLUCOGUIDE_LOCAL_LLM')=='1'
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
 if payload['plan']['tone']=='urgent' or payload['plan']['topic'] in GUARDED or re.search(r'\d',payload['question']):
  return {'answer':payload['fallback'],'mode':'rules','reason':'Thông số, thuốc và tình huống khẩn cấp được đối chiếu bằng luật có nguồn.'}
 if not payload['documents'] and payload['plan']['topic']!='social':return {'answer':payload['fallback'],'mode':'rules','reason':'Thiếu tài liệu; không sinh câu trả lời y tế.'}
 with _lock:
  load();import torch
  from app.local_prompt import SYSTEM
  context='\n'.join('['+d['id']+'] '+d['text'] for d in payload['documents'])
  messages=[{'role':'system','content':SYSTEM+'\nTÀI LIỆU:\n'+context}]+payload['history'][-8:]+[{'role':'user','content':payload['question']}]
  inputs=_tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False,return_tensors='pt').to(_model.device)
  if inputs.shape[1]>2048:return {'answer':payload['fallback'],'mode':'rules','reason':'Ngữ cảnh vượt giới hạn suy luận cục bộ.'}
  start=time.perf_counter()
  with torch.inference_mode():out=_model.generate(inputs,attention_mask=torch.ones_like(inputs),max_new_tokens=320,do_sample=False,pad_token_id=_tokenizer.eos_token_id,use_cache=True)
  draft=_tokenizer.decode(out[0,inputs.shape[1]:],skip_special_tokens=True).strip()
  # This is a conservative consistency filter, not a clinical fact checker.
  verdict=bus.request('Ngôn ngữ cục bộ','Kiểm chứng phản hồi',{'draft':draft,'documents':payload['documents'],'fallback':payload['fallback']})
  return dict(verdict,seconds=round(time.perf_counter()-start,3))
def verify(payload,bus):
 draft=payload['draft'];context=' '.join(d['text'] for d in payload['documents']);ids={d['id'] for d in payload['documents']}
 unknown=set(re.findall(r'\[([a-z0-9_]+)\]',draft))-ids
 numbers=set(re.findall(r'\d+(?:[.,]\d+)?',draft))-set(re.findall(r'\d+(?:[.,]\d+)?',context))
 unsafe=any(x in draft.lower() for x in ['chắc chắn mắc','chẩn đoán của tôi','tăng liều','ngừng thuốc ngay'])
 if not draft or unknown or numbers or unsafe or len(draft)<30 or (ids and not set(re.findall(r'\[([a-z0-9_]+)\]',draft))):
  return {'answer':payload['fallback'],'mode':'rules','reason':'Bản sinh không vượt kiểm tra nhất quán; dùng nội dung KB.'}
 return {'answer':draft,'mode':'qwen-lora','reason':'Đã kiểm tra mã nguồn và số liệu; chưa thay thế đánh giá chuyên gia.'}
