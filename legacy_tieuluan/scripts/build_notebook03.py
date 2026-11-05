"""Đóng gói mọi mã thực nghiệm và web vào một notebook tự chứa."""
from pathlib import Path
import hashlib
import json
import textwrap
ROOT=Path(__file__).resolve().parents[1]
legacy=json.loads((ROOT/'Tieuluan02_06_02_Giangkt.ipynb').read_text())
cells=[]


def md(text):cells.append({'cell_type':'markdown','metadata':{},'source':text.splitlines(keepends=True)})
def code(text):cells.append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':text.splitlines(keepends=True)})
def source(name):return (ROOT/name).read_text()


md('''# Tiểu luận 03 — AI, ML, CNN, RNN, Knowledge Graph và RAG

**Kiều Trường Giang — B23DCCN254**
Học phần: Phát triển các hệ thống thông minh — Giảng viên: Thầy Trần Đình Quế.

Chọn **Run All**. Đây là notebook chính duy nhất; không cần mở notebook cũ hoặc chạy thủ công script phụ.
Mặc định `MODE="full"`, CPU, seed 42. Lần kiểm thử trong workspace chạy đầy đủ, CNN 8 epoch,
RNN/LSTM/GRU mỗi mạng 35 epoch. Thời gian phụ thuộc máy; dữ liệu tải một lần và có cache kiểm tra hash.
`MODE="quick"` ghi vào `tmp/quick03`, không thay checkpoint, web hay số liệu full.

Các thử nghiệm từ Tiểu luận 01 được xây lại độc lập. Không sử dụng checkpoint/kết quả của tác giả cũ.
Hai PDF gốc được giữ để đối chiếu lý thuyết; dữ liệu tổng hợp nguy cơ tiểu đường không phải hồ sơ bệnh nhân lâm sàng.
''')
code('''# 1. Môi trường: tự cài các gói còn thiếu, không cần torchvision.
import sys, os, importlib.util, subprocess
from pathlib import Path
if sys.version_info < (3, 10):
    raise RuntimeError("Cần Python 3.10 trở lên, khuyến nghị Python 3.12+.")
required = {"numpy":"numpy", "pandas":"pandas", "sklearn":"scikit-learn", "torch":"torch",
            "matplotlib":"matplotlib", "requests":"requests", "networkx":"networkx",
            "joblib":"joblib", "IPython":"ipython", "reportlab":"reportlab", "pypdf":"pypdf", "PIL":"Pillow"}
missing = [pkg for mod,pkg in required.items() if importlib.util.find_spec(mod) is None]
if missing:
    subprocess.check_call([sys.executable,"-m","pip","install",*missing])
MODE = "full"             # đổi thành "quick" để kiểm tra nhanh
REUSE_CACHE = True         # False để huấn luyện lại từ đầu
REFRESH_MARKET = False     # True chỉ khi muốn lấy dữ liệu Yahoo mới; cần mạng
ROOT = Path.cwd().resolve()
if not (ROOT/"artifacts_giangkt").exists() and (ROOT.parent/"artifacts_giangkt").exists():
    ROOT=ROOT.parent
RUN_ROOT = ROOT if MODE=="full" else ROOT/"tmp/quick03"
RUN_ROOT.mkdir(parents=True,exist_ok=True)
print("Python",sys.version.split()[0],"mode",MODE,"root",ROOT)
''')
md('''## 2. Cấu hình, phép chia và các hàm thực nghiệm

ML: classification dùng stratified train/validation/test; CV chỉ chạy trên train.
Giá nhà chia theo nhóm địa chỉ, preprocessing được fit trong từng fold.
CNN giữ nguyên 10.000 ảnh test MNIST. RNN chia theo ngày **nhãn**, scaling chỉ fit trên train.
Không dùng test để chọn checkpoint hoặc mô hình triển khai.
''')
experiment=source('src/experiments03.py').split('\nif __name__=="__main__":')[0]
code(experiment)
code('''# Cache kiểm tra cấu hình và từng artifact đầu ra.
import shutil, hashlib, json
from IPython.display import display
SOURCE_SHA = '''+repr(hashlib.sha256(experiment.encode()).hexdigest())+'''
BASE_URL = "https://raw.githubusercontent.com/jellalaz/HTTM_ThayQue/main/"
for folder in [RUN_ROOT/"artifacts_tl03/data/raw",RUN_ROOT/"artifacts_tl03/models",RUN_ROOT/"artifacts_tl03/figures",ROOT/"artifacts_giangkt/data"]:
    folder.mkdir(parents=True,exist_ok=True)
for name in ["fpt_stock_processed.csv","gold_futures_processed.csv"]:
    path=ROOT/"artifacts_giangkt/data"/name
    if not path.exists(): download(BASE_URL+"artifacts_giangkt/data/"+name,path)
    if RUN_ROOT!=ROOT:
        dest=RUN_ROOT/"artifacts_giangkt/data"/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
if RUN_ROOT!=ROOT and (ROOT/"artifacts_tl03/data/raw").exists():
    shutil.copytree(ROOT/"artifacts_tl03/data/raw",RUN_ROOT/"artifacts_tl03/data/raw",dirs_exist_ok=True)
reset_seed()
print("Torch",torch.__version__,"GPU available",torch.cuda.is_available(),"training device CPU")

def run_stage(name,function,paths):
    directory=RUN_ROOT/"artifacts_tl03"
    manifest=directory/"data"/(name+"_cache.json")
    key={"source":SOURCE_SHA,"mode":MODE,"seed":SEED,"torch":torch.__version__,
         "sklearn":__import__('sklearn').__version__,
         "inputs":{f:sha256(ROOT/"artifacts_giangkt/data"/f) for f in ["fpt_stock_processed.csv","gold_futures_processed.csv"]}}
    if REUSE_CACHE and manifest.exists():
        old=json.loads(manifest.read_text())
        if old.get("key")==key and old.get("outputs") and all((directory/f).exists() and sha256(directory/f)==h for f,h in old["outputs"].items()):
            print("Cache đã xác minh:",name);return
    function()
    outputs={str(p.relative_to(directory)):sha256(p) for pattern in paths for p in directory.glob(pattern) if p.is_file()}
    if not outputs:raise RuntimeError("Không có artifact "+name)
    save_json(manifest,{"key":key,"outputs":outputs})
''')
md('''## 3. Machine Learning — hai bài toán của Tiểu luận 01 được xây lại

Dataset tải tự động bằng Kaggle public API, có kiểm tra schema. Tệp zip được cache cùng SHA-256.
Diabetes Risk Score, recommendation và consultation không được dùng làm đầu vào.
Diabetes Risk Prediction chứa **50.000 dòng tổng hợp**, 41 cột gồm cả nhãn và định danh.
''')
code('''run_stage("tabular",lambda:train_tabular(RUN_ROOT,MODE),["data/tabular_results.json","data/*_cv.csv","data/*_split.csv","data/*_predictions.csv","models/*.joblib","figures/diabetes_confusion.png","figures/housing*.png"])
tabular_results=json.loads((RUN_ROOT/"artifacts_tl03/data/tabular_results.json").read_text())
display(pd.DataFrame([{ "task":k,**v["metrics"]} for k,v in tabular_results.items()]))
''')
md('''## 4. CNN — nhận dạng chữ số MNIST

Tải IDX gzip trực tiếp, kiểm tra magic number. 48.000 train, 12.000 validation, 10.000 test.
Mạng Conv(1→8)→Pool→Conv(8→16)→Pool→Dense(784→64→10), huấn luyện từ đầu, không pretrained.
Augmentation chỉ trên train; checkpoint theo validation loss.
''')
code('''run_stage("cnn",lambda:train_cnn(RUN_ROOT,MODE),["data/cnn*.json","data/cnn*.csv","models/mnist_cnn.*","figures/cnn*.png"])
cnn_results=json.loads((RUN_ROOT/"artifacts_tl03/data/cnn_results.json").read_text())
print(cnn_results["metrics"])
display(__import__('IPython').display.Image(filename=str(RUN_ROOT/"artifacts_tl03/figures/cnn_learning.png")))
''')
md('''## 5. RNN, LSTM và GRU — dự báo giá theo chuỗi

30 log-return dự báo log-return kế tiếp, biến đổi ngược ra đơn vị gốc.
Ngày nhãn test kết thúc 14/10/2026; không đánh đồng chỉ số ngày nhãn với chỉ số ngày đặc trưng
của pipeline thị trường Tiểu luận 02. Persistence tham gia lựa chọn trên validation.
''')
code('''run_stage("sequences",lambda:train_sequences(RUN_ROOT,MODE),["data/sequence*.json","data/sequence*.csv","data/*_sequence_split.csv","data/*_history.csv","data/*_predictions.csv","models/*_rnn.pt","models/*_lstm.pt","models/*_gru.pt","models/sequences.json","figures/*_sequences.png"])
sequence_results=json.loads((RUN_ROOT/"artifacts_tl03/data/sequence_results.json").read_text())
display(pd.DataFrame(sequence_results["rows"])[["domain","model","validation_MAE","MAE","RMSE","R2","baseline_MAE"]])
''')
md('''## 6. Tái lập pipeline Tiểu luận 02 và Knowledge Graph

Giữ cơ chế CV, calibration và historical test của bản gốc. Mặc định dùng snapshot để
đối chiếu đúng số liệu đã báo cáo; bật REFRESH_MARKET nếu muốn cập nhật dữ liệu.
Các số đo ở đây là hồi quy tiến triển bệnh trên 442 người đã mắc bệnh, khác với classifier
nhãn nguy cơ tổng hợp ở phần ML.
''')
old1=''.join(legacy['cells'][1]['source'])
old1=old1.replace('ROOT / "artifacts_giangkt"','ROOT / "artifacts_tl03" / "legacy"')
old1=old1.replace('ROOT / "vercel_app"','ROOT / "tmp" / "tl03" / "legacy_web"')
old1=old1.replace('"https://github.com/jellalaz/RAG_HTTM"','"https://github.com/jellalaz/HTTM_ThayQue"')
code(old1+'\nfrom IPython.display import display\n')
old3=''.join(legacy['cells'][3]['source'])
old3=old3.replace('raw,meta=yahoo_chart(symbol)','''if not REFRESH_MARKET: raise RuntimeError("Snapshot đã khóa để tái lập")
        raw,meta=yahoo_chart(symbol)''')
code('''for file in ["fpt_stock_processed.csv","gold_futures_processed.csv"]:
    shutil.copy2(ROOT/"artifacts_giangkt/data"/file,DATA_DIR/file)
'''+old3)
code(''.join(legacy['cells'][4]['source']))
code(''.join(legacy['cells'][6]['source']))
md('''## 7. Vector RAG và GraphRAG có thể kiểm tra

TF-IDF là biểu diễn vector thưa, chưa phải dense embedding. NetworkX giữ KG trong bộ nhớ.
Generator ghép đoạn có căn cứ, không train hoặc gọi một LLM mới. Sáu câu hỏi là smoke test;
điểm hybrid tự định nghĩa không được coi là độ chính xác hay faithfulness.
''')
code(''.join(legacy['cells'][8]['source']))
code(''.join(legacy['cells'][9]['source']))
md('''## 8. Xuất kết quả, checkpoint và hình ảnh

CSV predictions, CV, training history và JSON metrics được tạo từ lần chạy thật.
Các mô hình truyền thống của bản gốc được xuất dưới dạng tham số inference trong JSON;
các mô hình mới có checkpoint joblib/PyTorch và trọng số JSON.
''')
code(''.join(legacy['cells'][11]['source']))
code(''.join(legacy['cells'][13]['source']))
code('''legacy_summary={"diabetes":diabetes_metrics,"stock":stock_model_info,"gold":gold_model_info,"retrieval":evaluation_df.to_dict("records")}
save_json(ROOT/"artifacts_tl03/data/legacy_results.json",legacy_summary)
# Không ghi đè snapshot gốc hoặc metrics đang dùng trên web chỉ vì refresh dữ liệu.
print("Đã tái lập và lưu riêng kết quả TL02.")
''')
md('''## 9. Đóng gói API và giao diện web

Mã HTML/CSS/JS, exporter và API được nhúng ở đây; notebook tự tạo nếu thiếu, không cần chạy
file phụ. Giao diện cũ và chatbot được giữ. API dùng standard library với trọng số đã train,
không cài PyTorch trên serverless. Quick không thay ứng dụng full.
''')
md('''### Phân tích sâu từ dự đoán và checkpoint

Phân phối lớp, missingness, sai số theo phân khúc giá, feature map CNN và phép tích chập
được tính lại từ dữ liệu gốc và trọng số đã học. Block bootstrap chỉ mô tả độ bất định
của test, không dùng đổi mô hình triển khai. Các sơ đồ cơ chế được ghi rõ là minh họa.
''')
analysis=source('src/analysis03.py').split('\nif __name__')[0].replace('    from experiments03 import DigitCNN,read_mnist','    # DigitCNN và read_mnist đã được định nghĩa ở phần 2.')
code(analysis+'\nif MODE=="full":\n    run_analysis03(RUN_ROOT, documents=documents, retriever=retriever, kg=kg)\nelse:\n    print("Chẩn đoán đầy đủ dùng artifact full; quick không thay các hình và bảng này.")\n')
# Nhúng nguyên các nguồn bảo trì dưới dạng payload; không phụ thuộc notebook hay file Python khác.
asset_names=['src/web.html','src/styles.css','src/clinical.js','src/engine.js','src/app.js',
             'src/experiments03.html','src/experiments03.js','src/inference03.py','scripts/export_web03.py']
payload={name:source(name) for name in asset_names}
code('''embedded_sources = '''+repr(payload)+'''
if MODE=="full":
    # Các file này do notebook quản lý; sửa mã trong notebook/builder khi cần thay đổi.
    for relative,content in embedded_sources.items():
        target=ROOT/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding="utf-8")
    # Tệp cấu hình cũ được tái lập nếu không có trong một thư mục sạch.
    original=ROOT/"artifacts_giangkt/data/web_model_config.json"
    if not original.exists():shutil.copy2(DATA_DIR/"web_model_config.json",original)
    sys.path.insert(0,str(ROOT/"src"))
    import importlib.util
    spec=importlib.util.spec_from_file_location("export_web03",ROOT/"scripts/export_web03.py")
    exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
    bundle03=exporter.export(ROOT)
    print("Web đã được build trong vercel_app/. Chưa tự deploy khi Run All.")
else:
    print("Quick hoàn tất trong",RUN_ROOT,"; không ghi đè bản full/web.")
''')
md('''## 10. Kiểm tra cuối cùng và bảng đối chiếu

Notebook tính lại metrics từ CSV, kiểm tra train/test, checkpoint và vector đối chiếu xuất mô hình.
Deploy/push cần xác thực hợp lệ; Run All không tự publish.
Word/PDF đã bàn giao được tạo từ các bảng và hình của chế độ full; khi thay cấu hình hoặc dữ liệu,
cần xuất lại báo cáo bằng builder đi kèm để tránh dùng số liệu cũ.
''')
code('''a=RUN_ROOT/"artifacts_tl03"
p=pd.read_csv(a/"data/cnn_predictions.csv")
assert abs(accuracy_score(p.actual,p.prediction)-cnn_results["metrics"]["Accuracy"])<1e-12
p=pd.read_csv(a/"data/housing_predictions.csv")
assert abs(mean_absolute_error(p.actual,p.prediction)-tabular_results["housing"]["metrics"]["MAE"])<1e-9
assert (a/"models/mnist_cnn.pt").exists() and (a/"models/housing.joblib").exists()
if MODE=="full":
    sys.path.insert(0,str(ROOT/"src"))
    from inference03 import predict as api_predict
    for s in json.loads((a/"data/cnn_parity.json").read_text()):
        r=api_predict(bundle03,{"task":"cnn","pixels":s["pixels"]})
        assert max(abs(x-y) for x,y in zip(r["logits"],s["logits"]))<3e-5
    assert "__MODEL_CONFIG__" not in (ROOT/"vercel_app/index.html").read_text()
alignment=pd.DataFrame([
 {"Chương":2,"Bài toán":"Diabetes classifier","Dataset":"50k synthetic","Model":tabular_results["diabetes_classifier"]["model"],"Metric":tabular_results["diabetes_classifier"]["metrics"]["F1_macro"],"Website":"/api/predict task=diabetes_classifier"},
 {"Chương":2,"Bài toán":"Giá nhà","Dataset":"Vietnam Housing 2024","Model":tabular_results["housing"]["model"],"Metric":tabular_results["housing"]["metrics"]["MAE"],"Website":"/api/predict task=housing"},
 {"Chương":3,"Bài toán":"Chữ số","Dataset":"MNIST","Model":"CNN from scratch","Metric":cnn_results["metrics"]["Accuracy"],"Website":"/api/predict task=cnn"},
 {"Chương":4,"Bài toán":"Chuỗi giá","Dataset":"FPT.VN / GC=F snapshot","Model":"RNN / LSTM / GRU / Persistence","Metric":"Xem sequence_comparison.csv","Website":"/api/predict task=sequence"},
 {"Chương":5,"Bài toán":"KG/RAG","Dataset":"11 docs, 25 nodes, 22 edges","Model":"TF-IDF + NetworkX + deterministic generator","Metric":evaluation_df["vector_precision@3"].mean(),"Website":"Chatbot sức khỏe BM25+KG"}])
alignment.to_csv(a/"data/alignment.csv",index=False)
display(alignment)
save_json(a/"data/notebook_verified.json",{"mode":MODE,"seed":SEED,"verified_at":datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),"code_sha256":SOURCE_SHA,"status":"Run All completed; metrics verified from predictions"})
print("RUN ALL THÀNH CÔNG — tất cả metrics lấy từ kết quả thật.")
''')
notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},'nbformat':4,'nbformat_minor':5}
for i,c in enumerate(cells):c['id']=f'tl03-{i:02d}'
(ROOT/'main.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print('main.ipynb:',len(cells),'cells')
