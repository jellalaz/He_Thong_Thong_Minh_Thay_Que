import requests,concurrent.futures,time,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
url='https://huggingface.co/Qwen/Qwen3-1.7B/resolve/main/model-00001-of-00002.safetensors'
sha='169ad53ec313c3a34b06c0809216e4fc072cce444a5d4ff2b59690d064130ed5'
base=ROOT/'.local-models/hf-cache/hub/models--Qwen--Qwen3-1.7B/blobs'
base.mkdir(parents=True,exist_ok=True)
parts=ROOT/'.local-models/download-parts';parts.mkdir(exist_ok=True)
r=requests.get(url+'?part=probe',headers={'Range':'bytes=0-0'},timeout=30)
r.raise_for_status();total=int(r.headers['Content-Range'].split('/')[-1]);print('TOTAL',total,flush=True)
chunk=16*1024*1024
jobs=[(i,start,min(start+chunk,total)-1) for i,start in enumerate(range(0,total,chunk))]
def get(job):
 i,a,b=job;p=parts/str(i)
 if p.exists() and p.stat().st_size==b-a+1:return i
 for trial in range(4):
  try:
   r=requests.get(url+'?part='+str(i),headers={'Range':f'bytes={a}-{b}'},timeout=(20,90))
   r.raise_for_status()
   assert r.headers.get('Content-Range','').startswith(f'bytes {a}-{b}/')
   assert len(r.content)==b-a+1
   p.write_bytes(r.content);return i
  except Exception:
   if trial==3:raise
   time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for n,i in enumerate(pool.map(get,jobs),1):print('PART',n,'/',len(jobs),flush=True)
h=hashlib.sha256();tmp=base/(sha+'.manual')
with tmp.open('wb') as f:
 for i,a,b in jobs:
  data=(parts/str(i)).read_bytes();h.update(data);f.write(data)
assert h.hexdigest()==sha,'SHA256 mismatch'
os.replace(tmp,base/sha)
print('VERIFIED SHA256',sha,flush=True)
