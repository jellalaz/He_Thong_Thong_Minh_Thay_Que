"""Create the flat five-file V2 hand-in, preserving the previous generated copy."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.query_knowledge_export import verify_bundle,query_bundle


def main():
    now=datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'));stamp=now.strftime('%Y%m%d-%H%M%S')
    stage=ROOT/'.runtime'/('delivery-v2-'+stamp);stage.mkdir(parents=True)
    quality=json.loads((ROOT/'results/v2/report_quality.json').read_text())
    assert quality['passed'] and quality.get('visual_reviewed'),'Complete final PDF review before packaging'
    for name in ['tieuluan_final_06_02_giangkt_v2.pdf','project01_06_02_giangkt_v2.pdf']:
        p=ROOT/'reports'/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==quality['files'][name]['sha256']
        shutil.copy2(p,stage/name)
    source=ROOT/'exports/diabetes';manifest=verify_bundle(source)
    cases=json.loads((source/'rag/evaluation.json').read_text())['cases']
    for c in cases:assert query_bundle(source,c['question'],c.get('history'))['sources']==c['selected']
    shutil.copy2(source/'kg/import.cypher',stage/'kb_diabet.cypher')
    checks=json.loads((ROOT/'results/v2/integration_checks.json').read_text())
    ui=json.loads((ROOT/'results/v2/ui_checks.json').read_text())
    old=json.loads((ROOT/'results/macos_setup_checks.json').read_text())
    assert checks['passed']>=11 and ui['passed']>=7 and old['passed']
    listed=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    files=sorted({n for n in listed if n and (ROOT/n).is_file()
                  and not n.startswith('ON_VAN_DAP/')})
    hashes={}
    archive=stage/'code_data_kb_rag.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in files:
            p=Path(n)
            assert not any(x in {'.git','.venv','.venv-llm','.runtime','.local-models','.local-training','__pycache__','BAN_GIAO_GLUCOGUIDE'} for x in p.parts)
            assert not(p.name.startswith('.env') and p.name!='.env.example')
            assert p.name!='.DS_Store'
            z.write(ROOT/n,'He_Thong_Thong_Minh_Thay_Que/'+n)
            hashes[n]=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
        for relative in ['live_qwen/results/dialogue_live_checks.json','graph_ui/results/graph_ui_checks.json','support_ui/results/support_ui_tests.json','graph_ui/reports/demo-graph-current.png','support_ui/reports/demo-pdf-sources.png']:
            evidence=ROOT/'.runtime/macos-verification'
            p=evidence/relative.replace('/reports/', '/report_sources/')
            if not p.exists():p=evidence/relative
            if p.exists():z.write(p,'minh_chung_mac/'+relative)
        summary={'created_at':now.isoformat(),'export':{k:manifest[k] for k in ['sources','documents','nodes','relationships']},'retrieval_cases_replayed':len(cases),'integration':checks,'ui':ui,'old_regression_passed':old['passed'],'report_quality':quality,'source_sha256':hashes}
        z.writestr('KIEM_TRA_DONG_GOI.json',json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        z.writestr('NOI_DUNG_ZIP.txt','Code đầy đủ: He_Thong_Thong_Minh_Thay_Que/\nPDF V1 và V2: reports/. Mã LaTeX và hình: report_sources/.\nData/nguồn: data/v2/. Checkpoint: models/v2/. Kết quả: results/v2/.\nKB/KG/RAG và code truy vấn độc lập: exports/diabetes/.\n')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    guide=f'''GLUCOGUIDE V2 — BỘ NỘP CHỈ 5 TỆP
Đóng gói: {now.strftime('%d/%m/%Y %H:%M')} (Việt Nam)

1. tieuluan_final_06_02_giangkt_v2.pdf
   Tiểu luận Final phát triển toàn văn, gồm bảy chương kế thừa và bốn chương V2.
2. project01_06_02_giangkt_v2.pdf
   Kiến trúc 6 tầng, 7 vai trò, hai dataset, đối chiếu V1/V2 theo từng mẫu test.
   Chương minh chứng có ảnh Pima V1/V2, đồ thị Neo4j và lượt chat Qwen có nguồn.
   Các chương kỹ thuật và phụ lục code chỉ rõ cách huấn luyện, điều phối, kiểm lỗi
   và truy lại tài liệu. Tiểu luận cũng có phụ lục code V2 với số dòng gốc.
3. kb_diabet.cypher
   FILE CYPHER THẦY YÊU CẦU: 169 Concept, 106 RELATED_TO, có document/evidence/URL.
   Tài liệu thầy gọi DB_diabet.cypher; ở đây đặt tên theo ảnh bảng kb_diabet.cypher.
4. code_data_kb_rag.zip
   Code, nguồn dữ liệu nhỏ, checkpoint, LaTeX, kết quả, KB/KG/RAG và hai PDF V1.
5. DOC_TRUOC.txt
   Chính tệp hướng dẫn này.

V2 KHÁC V1
- Giữ chat Qwen/KB/KG của V1; thêm workflow /api/v2/predict có schema theo dataset,
  request ID, model version/hash và audit metadata. Audit không lưu raw input.
- Train thật Pima: 768 mẫu, 8 feature; Early Stage: 520 dòng gốc, loại 269 dòng trùng,
  còn 251 mẫu, 16 feature. Cùng split gần 60/20/20 trong từng dataset cho các model.
- V1 đối chứng có 3 tầng ẩn (64-32-16). V2 có 5 tầng ẩn (64-32-16-8-4),
  đếm riêng phần giữa đầu vào và đầu ra. V2 tăng L2 và cân bằng trọng số lớp.
  V1 đối chứng là kiến trúc cũ tái train trên data mới, không phải checkpoint 50K cũ.
  Epoch chọn theo validation, với ngưỡng 0,5 và seed demo 254 cố định.
  Macro-F1 trung bình tăng trên Early Stage và giảm trên Pima. Xem bảng kết quả
  và ma trận nhầm lẫn trong Project 01 để trình bày đánh đổi của hai model.
- Qwen4B dùng nguyên trọng số. Train MLP không phải fine-tune Qwen.
- Tiểu luận V2 phát triển từ nguồn LaTeX của bản Final. Phần III bổ sung giao thức
  dữ liệu, MLP năm tầng, tích hợp agent và kiểm chứng. PDF V1 trong ZIP để đối chiếu.

DEMO TRÊN MAC HIỆN TẠI
Từ thư mục project gốc: bash run-macos.sh start
Mở http://localhost:8765/#v2
Chọn dataset -> Điền mẫu công khai -> Chạy -> đọc nguồn, trace, model version, request ID.
Đổi V1 đối chứng/V2 để chạy cùng schema; đổi dataset thì form/schema cũng đổi.
Sang Trò chuyện hỏi bữa trưa và hỏi tiếp; sang Đồ thị lọc a1c rồi mở nguồn.
Trong Dữ liệu & tài liệu tìm PDF để mở bản nguồn local và đúng trang.
Audit: .runtime/audit-v2.jsonl của project (metadata, không đưa dữ liệu audit vào gói nộp).
Tắt: bash run-macos.sh stop. Đọc tình trạng: bash run-macos.sh status.

CYPHER, KB VÀ RAG NẰM ĐÂU?
Neo4j Browser: http://localhost:7474/browser/
Copy kb_diabet.cypher vào Browser để chạy; MERGE không xóa graph khác.
  MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) RETURN a,r,b LIMIT 100;
  MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) WHERE r.document='a1c' RETURN a,r,b;
Giải nén code_data_kb_rag.zip, đi vào He_Thong_Thong_Minh_Thay_Que/:
  exports/diabetes/kb/knowledge.json: 58 đoạn, 22 nguồn, nội dung và triple.
  exports/diabetes/kg/: CSV, JSON và Cypher (bản chụp Neo4j).
  exports/diabetes/rag/: index.joblib, settings, queries, evaluation.
  exports/diabetes/sources/: PDF NIDDK, văn bản nguồn và trích dẫn ngắn Vinmec.
Code retrieval/graph có trong exports/diabetes/code/app/ và app/ của project.
RAG dùng TF-IDF word/char, không dùng neural embedding hoặc multi-hop GraphRAG.
Truy vấn file offline từ project có .venv:
  .venv/bin/python scripts/query_knowledge_export.py exports/diabetes --question "HbA1c là gì?"
Chế độ file trả căn cứ snapshot, không chạy Qwen và không giả kết nối Neo4j.

CHẠY LẠI SAU KHI GIẢI NÉN
Đi vào He_Thong_Thong_Minh_Thay_Que/ trong gói.
Mac cần Python 3.14 + Java 21 ARM64; Edge để test UI.
  bash setup-macos.sh
  bash run-macos.sh start
Checkpoint đã đóng gói: không cần train lại chỉ để demo.
Muốn train V2 offline: .venv/bin/python -m scripts.train_v2
Nguồn nhỏ có sẵn ở data/v2/sources/. Kết quả và CSV predictions: results/v2/.
Test: .venv/bin/python -m scripts.test_v2
LaTeX và ảnh ở report_sources/, có thể biên dịch bằng XeLaTeX/Tectonic.
Qwen khoảng 2,5 GB, runtime, .venv và mật khẩu không đóng gói; setup tải trên máy mới.
Không cần cài thêm vào Miniforge base. ZIP Diabetes 50K để train model cũ vẫn thiếu;
không chặn hai dataset V2 hoặc inference checkpoint đã có.

KIỂM TRA
{len(cases)} câu truy xuất replay đúng; {checks['passed']} kiểm tra tích hợp V2;
{ui['passed']} kiểm tra UI V2; các nhóm hồi quy chức năng cũ đều qua.
SHA-256 ZIP code/data: {digest}
Manifest chi tiết nằm trong ZIP để không thêm file rời ở cấp ngoài.
'''
    (stage/'DOC_TRUOC.txt').write_text(guide,encoding='utf-8')
    assert len(list(stage.iterdir()))==5 and all(p.is_file() for p in stage.iterdir())
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    dest=ROOT/'BAN_GIAO_GLUCOGUIDE'
    if dest.exists():dest.rename(ROOT/'.runtime'/('delivery-previous-'+stamp))
    oldzip=ROOT/'BAN_GIAO_GLUCOGUIDE.zip'
    if oldzip.exists():oldzip.rename(ROOT/'.runtime'/('delivery-previous-'+stamp+'.zip'))
    stage.rename(dest)
    print(json.dumps({'folder':str(dest),'files':[p.name for p in sorted(dest.iterdir())],'source_files':len(files),'zip_sha256':digest},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
