"""Export the current local KB, exact Neo4j snapshot, fitted RAG and reproducible code."""
import argparse
import csv
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib
from neo4j import GraphDatabase
from app.settings import database
from app.retrieval import load_knowledge, Retriever, RETRIEVAL_CONFIG
from app.conversation import route
from app.dialogue import plan_turn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/diabetes'
SNAPSHOT_QUERY='''MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept)
RETURN a.name AS source,r.label AS relation,b.name AS target,
r.document AS document,r.evidence AS evidence,r.source_url AS source_url
ORDER BY document,source,relation,target'''


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def snapshot(kb):
    uri=os.environ.get('NEO4J_URI','bolt://127.0.0.1:7687')
    if urlparse(uri).hostname not in {'127.0.0.1','localhost','::1'}:
        raise ValueError('Export requires a local Neo4j; remote targets are disabled')
    with GraphDatabase.driver(uri,auth=(os.environ.get('NEO4J_USER','neo4j'),os.environ['NEO4J_PASSWORD']),connection_timeout=5,max_transaction_retry_time=0) as driver:
        rows=[dict(r) for r in driver.execute_query(SNAPSHOT_QUERY,database_=database()).records]
        names=[r['name'] for r in driver.execute_query('MATCH (n:Concept) RETURN n.name AS name ORDER BY name',database_=database()).records]
    expected={(d['id'],*t) for d in kb['documents'] for t in d['triples']}
    actual={(r['document'],r['source'],r['relation'],r['target']) for r in rows}
    assert actual==expected and len(rows)==len(expected),'Neo4j and KB differ; export aborted'
    by_id={d['id']:d for d in kb['documents']}
    for r in rows:
        d=by_id[r['document']]
        assert r['evidence']==d['text'] and r['source_url']==kb['sources'][d['source']]['url']
    assert set(names)=={n for r in rows for n in (r['source'],r['target'])}
    nodes=[{'id':f'n{i:04d}','name':name,'label':'Concept'} for i,name in enumerate(sorted(names),1)]
    return {'storage':'Neo4j local snapshot','nodes':nodes,'relationships':rows}


def evaluate(retriever,cases):
    rows=[]
    for case in cases:
        plan=plan_turn(case['question'],case.get('history',[]),route(case['question'],case.get('history',[])))
        selected=retriever.search(plan)
        ids=[d['id'] for d in selected]
        rank=next((i+1 for i,x in enumerate(ids) if x in case['expected']),None)
        rows.append(dict(case,selected=[{'id':d['id'],'score':d.get('retrieval_score')} for d in selected],
                         first_relevant_rank=rank,passed=bool(rank) if case['expected'] else not ids))
    positives=[r for r in rows if r['expected']]
    return {'scope':'Functional author-created retrieval set; not a clinical or independent benchmark.',
            'cases':rows,'positive_queries':len(positives),
            'hit_at_1':sum(r['first_relevant_rank']==1 for r in positives)/len(positives),
            'hit_at_4':sum(r['first_relevant_rank'] is not None for r in positives)/len(positives),
            'mrr_at_4':sum(1/r['first_relevant_rank'] if r['first_relevant_rank'] else 0 for r in positives)/len(positives),
            'abstention_checks':sum(not r['selected'] for r in rows if not r['expected']),
            'passed_cases':sum(r['passed'] for r in rows),'total_cases':len(rows)}


def build(live=False):
    kb=load_knowledge()
    kb['sources']={k:v for k,v in kb['sources'].items() if k in {d['source'] for d in kb['documents']}}
    graph=snapshot(kb)
    for directory in ['kb','kg','rag','examples','code/app','code/models','code/scripts']:
        (OUT/directory).mkdir(parents=True,exist_ok=True)
    write_json(OUT/'kb/knowledge.json',kb)
    write_json(OUT/'kg/graph.json',graph)
    ids={n['name']:n['id'] for n in graph['nodes']}
    with (OUT/'kg/nodes.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','name','label']);writer.writeheader();writer.writerows(graph['nodes'])
    with (OUT/'kg/relationships.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['source_id','target_id','relation','document','evidence','source_url']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in graph['relationships']:
            writer.writerow(dict(source_id=ids[r['source']],target_id=ids[r['target']],**{k:r[k] for k in fields[2:]}))
    literal='[\n'+',\n'.join('{'+','.join(k+':'+json.dumps(v,ensure_ascii=False) for k,v in r.items())+'}' for r in graph['relationships'])+'\n]'
    cypher='UNWIND '+literal+''' AS row
MERGE (a:Concept {name:row.source}) MERGE (b:Concept {name:row.target})
MERGE (a)-[r:RELATED_TO {label:row.relation,document:row.document}]->(b)
SET r.evidence=row.evidence,r.source_url=row.source_url;
'''
    (OUT/'kg/import.cypher').write_text(cypher,encoding='utf-8')
    retriever=Retriever(kb['documents'])
    joblib.dump(retriever,OUT/'rag/index.joblib',compress=3)
    write_json(OUT/'rag/settings.json',RETRIEVAL_CONFIG)
    questions=json.loads((ROOT/'data/rag_evaluation.json').read_text(encoding='utf-8'))
    write_json(OUT/'rag/queries.json',questions)
    evaluation=evaluate(retriever,questions['cases'])
    write_json(OUT/'rag/evaluation.json',evaluation)
    write_json(ROOT/'results/rag_retrieval_evaluation.json',evaluation)
    modules=['agents','answer_display','conversation','dialogue','graph_knowledge','intent','local_prompt','retrieval','safety']
    (OUT/'code/app/__init__.py').write_text('',encoding='utf-8')
    for module in modules:shutil.copyfile(ROOT/f'app/{module}.py',OUT/f'code/app/{module}.py')
    shutil.copyfile(ROOT/'models/chat_intent.joblib',OUT/'code/models/chat_intent.joblib')
    for script in ['query_knowledge_export.py','restore_knowledge_export.py']:
        shutil.copyfile(ROOT/'scripts'/script,OUT/'code/scripts'/script)
    dependencies={name:version(name) for name in ['numpy','scikit-learn','joblib','neo4j']}
    (OUT/'requirements.txt').write_text('\n'.join(k+'=='+v for k,v in dependencies.items())+'\n',encoding='utf-8')
    examples=[]
    if live:
        import httpx
        with httpx.Client(base_url='http://127.0.0.1:8765',trust_env=False,timeout=180) as client:
            status=client.get('/api/status');status.raise_for_status()
            assert status.json()['local_only'] and status.json()['local_llm']
            for question in ['Type 1 khác type 2 thế nào?','Gợi ý một bữa trưa dễ nấu cho người tiểu đường','Metformin dùng để làm gì?','Đường huyết 350 mg/dL, nôn và đau bụng, có cần đi viện không?']:
                response=client.post('/api/chat',json={'question':question});response.raise_for_status()
                examples.append({'question':question,**response.json()})
        write_json(OUT/'examples/agent_runs.json',examples)
        write_json(ROOT/'results/knowledge_agent_examples.json',examples)
    else:
        write_json(OUT/'examples/agent_runs.json',{'scope':'No live generation requested; run export_knowledge with --live-examples to capture local model responses.'})
    readme='''# Bộ nộp KB, KG và RAG tiểu đường

Thư mục này chứa dữ liệu và code có thể kiểm tra, không chỉ ảnh demo. KB gồm 46 đoạn từ 19 nguồn; KG được đọc và đối chiếu trực tiếp từ Neo4j local, có 143 khái niệm và 86 quan hệ.

## Các tệp

- kb/knowledge.json: nội dung, từ khóa, mã tài liệu, nguồn và bộ ba.
- kg/nodes.csv, kg/relationships.csv: nút và cạnh UTF-8, có mã tài liệu, trích đoạn và URL.
- kg/graph.json, kg/import.cypher: bản chụp đồ thị và lệnh MERGE để nạp lại.
- rag/index.joblib, rag/settings.json: chỉ mục TF-IDF đã fit và cấu hình đầy đủ.
- rag/queries.json, rag/evaluation.json: câu hỏi, tài liệu kỳ vọng, kết quả từng câu và chỉ số truy xuất.
- examples/agent_runs.json: phản hồi và trace từ ứng dụng local nếu xuất với --live-examples.
- code/: các module điều phối, truy xuất, agent đồ thị, luật, prompt và script chạy lại.
- manifest.json: số lượng và SHA-256 của từng tệp. Không có mật khẩu, API key, hồ sơ bệnh nhân hoặc trọng số Qwen trong bộ nộp.

## Truy vấn bộ nộp hoàn toàn offline

Từ thư mục này, dùng Python đã có các thư viện theo requirements.txt:

    python code/scripts/query_knowledge_export.py . --question "HbA1c là gì?"

Lệnh kiểm tra checksum, đọc chỉ mục đã lưu, chạy các agent qua MessageBus và trả văn bản cùng quan hệ của bản chụp. Chế độ này không chạy Qwen, không giả lập kết nối Neo4j và không gọi Internet. Chỉ nạp index.joblib từ bộ nộp tin cậy; checksum kiểm tra tính toàn vẹn, không xác thực người phát hành.

## Nạp lại Neo4j local

    python code/scripts/restore_knowledge_export.py .

Script hỏi mật khẩu hoặc đọc NEO4J_PASSWORD từ môi trường. MERGE không xóa dữ liệu khác. Có thể dùng kg/import.cypher để kiểm tra bằng công cụ Neo4j. Không dùng địa chỉ máy chủ ngoài.

## Chạy sản phẩm đầy đủ

Mã nguồn gốc: https://github.com/jellalaz/He_Thong_Thong_Minh_Thay_Que

Trên máy đã có Qwen3 4B và Neo4j, chạy START_CHATBOT_LOCAL.cmd trong project gốc rồi mở http://localhost:8765. Agent đồ thị lấy quan hệ theo tài liệu đã truy xuất; quan hệ phải khớp bộ ba, văn bản và nguồn trước khi cấp cho Qwen. Nhánh cấp cứu trả bằng luật trước RAG/KG.

Đồ thị còn 57 cụm rời nhau; chưa phải ontology y khoa đầy đủ hay Microsoft GraphRAG. Tập câu hỏi do project biên soạn, chưa thay thế đánh giá độc lập hoặc thẩm định lâm sàng. Kết quả truy xuất không phải độ chính xác chẩn đoán.
'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')
    files={p.relative_to(OUT).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'}
    manifest={'schema_version':1,'documents':len(kb['documents']),'sources':len(kb['sources']),'nodes':len(graph['nodes']),'relationships':len(graph['relationships']),'graph_origin':'exact local Neo4j snapshot, checked against KB','dependencies':dependencies,'files':files}
    write_json(OUT/'manifest.json',manifest)
    archive=OUT.parent/'glucoguide_kb_kg_rag.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,'diabetes/'+p.relative_to(OUT).as_posix())
    result={'documents':manifest['documents'],'sources':manifest['sources'],'nodes':manifest['nodes'],'relationships':manifest['relationships'],'files':len(files)+1,'archive_bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'retrieval_hit_at_4':evaluation['hit_at_4'],'retrieval_passed_cases':evaluation['passed_cases'],'retrieval_total_cases':evaluation['total_cases'],'live_examples':len(examples)}
    write_json(ROOT/'results/knowledge_export.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-examples',action='store_true')
    build(parser.parse_args().live_examples)
