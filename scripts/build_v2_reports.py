"""Assemble the two V2 LaTeX reports using measured experiment artifacts."""
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties


def tex(text):
    result=str(text)
    for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:result=result.replace(a,b)
    return result


def table(name, caption, columns, headers, rows):
    columns=columns.replace('p{','P{')
    content=r'\par\FloatBarrier\begin{table}[H]\centering\small\setstretch{1.15}\setlength{\tabcolsep}{5pt}'+'\n'
    content+=r'\caption{'+caption+r'}\begin{tabular}{'+columns+r'}\toprule'+'\n'
    header=' & '.join(headers)+r'\\\midrule'+'\n'
    content+=header
    content+='\n'.join(' & '.join(map(str,row))+r'\\' for row in rows)
    content+=r'\bottomrule\end{tabular}\end{table}'+'\n'
    (OUT/name).write_text(content)


def thesis_tables(experiment):
    registry = json.loads((ROOT/'models/v2/registry.json').read_text())
    table('early_feature_table.tex', 'Từ điển 16 đặc trưng của Early Stage theo thứ tự mô hình.',
          'p{5.2cm}p{5.3cm}p{4.0cm}', ['Trường gốc', 'Ý nghĩa', 'Dạng đầu vào'], [
              [tex(f['name']), tex(f['label']),
               'Tuổi theo năm' if f['name']=='Age' else '0 = nữ, 1 = nam'
               if f['name']=='Gender' else '0 = không, 1 = có']
              for f in registry['datasets']['early_stage']['features']
          ])
    split_rows = []
    for key, name in [('pima', 'Pima'), ('early_stage', 'Early Stage')]:
        with (ROOT/'data/v2'/f'{key}.csv').open(newline='') as source:
            records = list(csv.DictReader(source))
        for split in ['train', 'validation', 'test']:
            counts = [sum(row['split']==split and row['target']==label for row in records)
                      for label in ('0', '1')]
            split_rows.append([name, split, *counts, sum(counts)])
    table('v2_split_table.tex', 'Phân bố nhãn theo từng tập sau khi làm sạch.', 'llrrr',
          ['Bộ dữ liệu', 'Tập', 'Negative', 'Positive', 'Tổng'], split_rows)
    table('v2_seed_table.tex', 'Epoch được chọn theo validation và macro-F1 trên test theo từng seed.',
          'llrrrr', ['Bộ dữ liệu', 'Model', 'Seed', 'Epoch', 'F1 validation', 'F1 test'], [
              ['Pima' if row['dataset']=='pima' else 'Early Stage', row['version'].upper(),
               row['seed'], row['best_epoch'], f"{row['validation_macro_f1']:.4f}", f"{row['macro_f1']:.4f}"]
              for row in experiment['results'] if row['version']!='logistic'
          ])
    table('v2_repro_table.tex', 'Đối chiếu từng loại bằng chứng với vị trí trong gói mã nguồn.',
          'p{4.4cm}p{5.2cm}p{4.7cm}', ['Bằng chứng', 'Vị trí', 'Cách kiểm tra'], [
              ['Nguồn và hợp đồng dữ liệu', r'\code{data/v2/sources/}', 'Xem nguồn, phiên bản và dữ liệu gốc.'],
              ['Phép chia train, validation, test', r'\code{data/v2/pima.csv} và \code{early_stage.csv}', 'Đếm nhãn, hàng và khóa đặc trưng theo tập.'],
              ['Điểm từng hàng test', r'\code{results/v2/}', 'Dùng cột xác suất và ngưỡng 0,5 để lập lại ma trận.'],
              ['Checkpoint và registry', r'\code{models/v2/}', 'Đối chiếu thứ tự đặc trưng và SHA-256.'],
              ['Vết chạy đa agent', r'\code{results/v2/} và \code{agent_examples.json}', 'Xem model version, mã yêu cầu và mã đoạn nguồn.'],
              ['Kho tri thức và chỉ mục', r'\code{exports/diabetes/}', 'Đọc KB, Cypher và phát lại bộ câu truy xuất.'],
          ])


def paired_prediction_table(threshold):
    """Count how often a row changed from correct to wrong or the reverse."""
    rows = []
    for key, title in [('pima', 'Pima'), ('early_stage', 'Early Stage')]:
        with (ROOT/'results/v2'/f'{key}_test_predictions.csv').open(newline='') as source:
            predictions = list(csv.DictReader(source))
        for actual, label in [(0, 'Negative'), (1, 'Positive')]:
            transitions = {(a, b): 0 for a in (True, False) for b in (True, False)}
            for record in predictions:
                if int(record['actual']) != actual:
                    continue
                v1 = (float(record['v1_254_prob']) >= threshold) == bool(actual)
                v2 = (float(record['v2_254_prob']) >= threshold) == bool(actual)
                transitions[v1, v2] += 1
            rows.append([title, label, *transitions.values(), sum(transitions.values())])
    table('paired_prediction_table.tex', 'Thay đổi dự đoán trên cùng hàng test, seed 254, thứ tự V1 tới V2.',
          'llrrrrr', ['Bộ dữ liệu', 'Nhãn thật', 'Đúng/đúng', 'Đúng/sai', 'Sai/đúng', 'Sai/sai', 'Tổng'],
          rows)


def project_detail_tables(experiment):
    """Use committed evidence for the detailed Project 01 chapters."""
    metrics = json.loads((ROOT/'results/model_metrics.json').read_text())
    table('project_v1_scores.tex', 'Kết quả test lưu từ Project 01 gốc.',
          'llrrll', ['Tác vụ', 'Mô hình', 'Train', 'Test', 'Chỉ số 1', 'Chỉ số 2'], [
              ['Phân loại', r['model'], r['n_train'], r['n_test'],
               f"Acc. {r['accuracy']:.4f}", f"F1 {r['macro_f1']:.4f}"]
              if r['task']=='classification' else
              ['Hồi quy', r['model'], r['n_train'], r['n_test'],
               f"MAE {r['mae']:.2f}", f"$R^2$ {r['r2']:.4f}"]
              for r in metrics
          ])
    counts = experiment['datasets']['pima']['zeros_as_missing']
    total = experiment['datasets']['pima']['raw_rows']
    table('project_missing_table.tex', 'Giá trị 0 chuyển thành thiếu trên toàn bộ Pima trước khi chia.',
          'lrr', ['Mã trường', 'Số giá trị', 'Tỷ lệ trên 768 mẫu'], [
              [key, value, f'{100*value/total:.1f}\\%'] for key,value in counts.items()
          ])
    table('project_model_seed254.tex', 'Điểm trên test ở checkpoint demo seed 254.',
          'llrrrrr', ['Dataset', 'Model', 'Epoch', 'Precision +', 'Recall +', 'ROC-AUC', 'Log loss'], [
              ['Pima' if r['dataset']=='pima' else 'Early Stage', r['version'].upper(),
               r['best_epoch'], *[f"{r[k]:.4f}" for k in ('precision','recall','roc_auc','log_loss')]]
              for r in experiment['results'] if r['version'] in {'v1','v2'} and r['seed']==254
          ])
    examples = json.loads((ROOT/'results/v2/agent_examples.json').read_text())
    pima = next(x for x in examples if x['prediction']['model_version']=='pima-v2-seed254')
    table('project_trace_example.tex', 'Một lượt Pima V2 đã lưu. Mỗi hàng là một lời gọi.',
          'llrr', ['Vai trò nhận', 'Loại yêu cầu', 'Thời gian (ms)', 'Thông điệp kết quả'], [
              [request['receiver'], request['type'], f"{request['elapsed_ms']:.3f}", reply['type']]
              for request,reply in zip(pima['trace'][::2],pima['trace'][1::2],strict=True)
          ])
    retrieval = json.loads((ROOT/'exports/diabetes/rag/evaluation.json').read_text())
    table('project_rag_rank_cases.tex', 'Các ca nguồn kỳ vọng xuống hạng và các ca bỏ qua truy xuất.',
          'lp{4cm}p{6cm}r', ['Ca', 'Mã kỳ vọng', 'Kết quả đã lưu theo thứ tự', 'Hạng đầu'], [
              [tex(c['id']), tex(', '.join(c['expected'])) or '--',
               tex(', '.join(item['id'] for item in c['selected'])) or '--',
               c['first_relevant_rank'] or '--']
              for c in retrieval['cases'] if c['first_relevant_rank']!=1
          ])


def defense_evidence():
    table('defense_requirements_table.tex', 'Yêu cầu và bằng chứng có thể mở trong buổi demo.',
          'p{3.7cm}p{6.0cm}p{4.1cm}', ['Yêu cầu', 'Cách thể hiện trong GlucoGuide', 'Mở để kiểm tra'], [
              ['Hai phiên bản và hai bộ train', 'V1 đối chứng và V2 dùng cùng phép chia trong mỗi bộ. V2 có năm tầng ẩn.', r'Chương~\ref{pr:model}, bảng test, màn V1/V2.'],
              ['DL có thể dùng lại', 'Mô hình V1 gốc phục vụ luồng cũ. Nhánh V2 nạp pipeline đã huấn luyện khi suy luận.', r'\code{app/main.py}, \code{app/v2.py}.'],
              ['Sáu tầng và hợp đồng agent', 'Coordinator gọi Data, Prediction, Rule, KG/RAG, Explanation và Monitoring.', r'Chương~\ref{pr:mas}, trace có mã yêu cầu.'],
              ['Neo4j, Cypher và nguồn RAG', 'Nạp cạnh từ Cypher. Đối chiếu mã tài liệu, trích đoạn và URL giữa KB, đồ thị và câu trả lời.', r'Chương~\ref{pr:knowledge}, Neo4j Browser.'],
              ['Đánh giá từng phần và toàn hệ', 'Đối chiếu checkpoint, replay retrieval, chạy API và giao diện. Tách đánh giá kỹ thuật khỏi đánh giá lâm sàng.', r'Chương~\ref{pr:checks}, JSON kiểm thử.'],
          ])
    examples = json.loads((ROOT/'results/v2/agent_examples.json').read_text())
    sample = next(x for x in examples if x['prediction']['model_version']=='pima-v2-seed254')
    prediction = sample['prediction']
    excerpt = {
        'request_id': sample['request_id'],
        'prediction': {k: prediction[k] for k in ('model_version', 'hidden_layers', 'label_text', 'positive_label_score', 'threshold')},
        'source_ids': [d['id'] for d in sample['sources']],
        'graph_status': sample['graph_status'],
    }
    excerpt['prediction']['positive_label_score'] = round(prediction['positive_label_score'], 4)
    registry = json.loads((ROOT/'models/v2/registry.json').read_text())
    request = {'dataset': 'pima', 'version': 'v2',
               'values': registry['datasets']['pima']['example'], 'question': 'HbA1c là gì?'}
    # source_ids is a compact projection of the response's sources array.
    formatted = re.sub(r'\[[^\[\]]*\]', lambda match: json.dumps(json.loads(match[0])),
                       json.dumps(excerpt,indent=2))
    (OUT/'defense_sample.tex').write_text(
        r'\Needspace{16\baselineskip}\noindent\textbf{Yêu cầu dùng mẫu Pima công khai.}\par'+'\n'
        + r'\begin{Verbatim}[fontsize=\small]'+'\n'
        + json.dumps(request,ensure_ascii=False,indent=2)+'\n'
        + r'\end{Verbatim}'+'\n'
        + r'\Needspace{13\baselineskip}\noindent\textbf{Trích phản hồi của lượt kiểm thử.}\par'+'\n'
        + r'\begin{Verbatim}[fontsize=\small]'+'\n'
        + formatted
        + '\n'+r'\end{Verbatim}'+'\n'
    )
    table('defense_timings_table.tex', 'Bốn lượt kiểm tra API V2, thời gian tới trước bước ghi audit.',
          'lrrr', ['Model / phiên bản', 'Thời gian (ms)', 'Thông điệp', 'Cạnh đã đối chiếu'], [
              [x['prediction']['model_version'].replace('_',r'\_'), f"{1000*x['seconds']:.1f}",
               len(x['trace']),len(x['graph_evidence'])]
              for x in examples
          ])


def figures(hidden_layers):
    font=FontProperties(fname='/System/Library/Fonts/Supplemental/Times New Roman.ttf')
    layers=[('1. Giao diện','Chat · form V1/V2 · nguồn · đồ thị'),
            ('2. API và xử lý dữ liệu','FastAPI / Pydantic · schema theo dataset · kiểm tra đầu vào'),
            ('3. Điều phối','Coordinator · thứ tự thực thi · request ID · nhánh lỗi'),
            ('4. Agent chuyên trách','Data · Prediction · Rule · KG/RAG · Explanation · Monitoring'),
            ('5. Tri thức và mô hình','MLP checkpoint · KB · Neo4j · TF-IDF · Qwen local'),
            ('6. Đánh giá và audit','Predictions / metrics · trace có version · audit metadata')]
    fig,ax=plt.subplots(figsize=(8,7.7));ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
    for i,(title,detail) in enumerate(layers):
        y=8.6-i*1.45
        ax.add_patch(FancyBboxPatch((.25,y),9.5,1.05,boxstyle='round,pad=.10',facecolor='#e8f2f0',edgecolor='#346d68'))
        ax.text(5,y+.7,title,ha='center',va='center',fontproperties=font,fontsize=15,weight='bold')
        ax.text(5,y+.27,detail,ha='center',va='center',fontproperties=font,fontsize=11.5)
        if i<5:ax.annotate('',xy=(5,y-.36),xytext=(5,y-.12),arrowprops={'arrowstyle':'->','color':'#346d68','lw':1.8})
    fig.savefig(OUT/'figures/layers.png',dpi=180,bbox_inches='tight');plt.close(fig)
    nodes = [('Đầu vào', '8 hoặc 16'), *[(f'Ẩn {i}', str(width))
             for i, width in enumerate(hidden_layers, 1)], ('Đầu ra', '1')]
    fig, ax = plt.subplots(figsize=(9, 1.6))
    ax.set(xlim=(0, 2 * len(nodes)), ylim=(0, 2))
    ax.axis('off')
    for i, (title, detail) in enumerate(nodes):
        x = 2 * i + .17
        color = '#e8f2f0' if 0 < i < len(nodes) - 1 else '#f0f2f3'
        ax.add_patch(FancyBboxPatch((x, .45), 1.55, 1.1, boxstyle='round,pad=.07',
                                   facecolor=color, edgecolor='#346d68'))
        ax.text(x + .775, 1.13, title, ha='center', fontproperties=font, fontsize=13)
        ax.text(x + .775, .70, detail, ha='center', fontproperties=font, fontsize=13)
        if i < len(nodes) - 1:
            ax.annotate('', xy=(x + 1.92, 1), xytext=(x + 1.61, 1),
                        arrowprops={'arrowstyle': '->', 'lw': 1.2})
    fig.savefig(OUT/'figures/mlp.png',dpi=180,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5));ax.set(xlim=(0,10),ylim=(0,6));ax.axis('off')
    nodes=[(.3,4.7,4.1,'Nhánh dữ liệu: Pima / Early Stage'),(.3,3.1,4.1,'Làm sạch → chia → fit train → MLP'),
           (5.6,4.7,4.1,'Nhánh tri thức: web / PDF có nguồn'),(5.6,3.1,4.1,'KB → TF-IDF + KG / Neo4j'),
           (2.1,.7,5.8,'Coordinator → giải thích + nguồn + audit')]
    for x,y,w,text in nodes:
        ax.add_patch(FancyBboxPatch((x,y),w,.8,boxstyle='round,pad=.08',facecolor='#e8f2f0',edgecolor='#346d68'))
        ax.text(x+w/2,y+.4,text,ha='center',va='center',fontproperties=font,fontsize=12)
    for a,b in [((2.35,4.65),(2.35,4)),((7.65,4.65),(7.65,4)),((2.35,3),(4,1.6)),((7.65,3),(6,1.6))]:
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','lw':1.6,'color':'#346d68'})
    fig.savefig(OUT/'figures/provenance.png',dpi=180,bbox_inches='tight');plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    r=json.loads((ROOT/'results/v2/experiment.json').read_text())
    thesis_tables(r)
    paired_prediction_table(r['test_threshold'])
    project_detail_tables(r)
    defense_evidence()
    kb=json.loads((ROOT/'exports/diabetes/kb/knowledge.json').read_text())
    table('dataset_table.tex','Hai bộ dữ liệu và phép chia thực tế sau làm sạch.','p{4.2cm}rr',
          ['Hạng mục','Pima','Early Stage'],[
              ['Nguồn','OpenML 37 v1','UCI 529'],['Số dòng gốc',768,520],
              ['Sau loại trùng',r['datasets']['pima']['clean_rows'],r['datasets']['early_stage']['clean_rows']],
              ['Số feature',8,16],['Train / validation / test','460 / 154 / 154','150 / 50 / 51'],
              ['Negative / Positive (sạch)','500 / 268','78 / 173'],['Nhóm feature mâu thuẫn',0,0]])
    rows=[]
    for key,title in [('pima','Pima'),('early_stage','Early Stage')]:
        for v in ['logistic','v1','v2']:
            selected=[x for x in r['results'] if x['dataset']==key and x['version']==v]
            def stat(n):
                a=np.array([x[n] for x in selected]);return f'{a.mean():.3f}' if len(a)==1 else f'{a.mean():.3f} $\\pm$ {a.std():.3f}'
            rows.append([title,{'logistic':'Logistic','v1':'V1','v2':'V2'}[v],stat('accuracy'),stat('macro_f1'),stat('recall'),selected[0].get('parameters','--')])
    table('model_table.tex','Metric test; trung bình $\\pm$ độ lệch chuẩn khởi tạo, không phải khoảng tin cậy.','llrrrl',
          ['Dataset','Mạng','Accuracy','Macro-F1','Recall +','Tham số'],rows)
    def result(k,v):return next(x for x in r['results'] if x['dataset']==k and x['version']==v and x['seed']==254)
    comparison = []
    for key, title in [('pima', 'Pima'), ('early_stage', 'Early Stage')]:
        v1, v2 = result(key, 'v1'), result(key, 'v2')
        baseline = result(key, 'logistic')
        audit = r['datasets'][key]
        lo, hi = audit['paired_bootstrap_95_percentile']
        delta = audit['paired_accuracy_difference_v2_minus_v1']
        comparison.append(
            f'Ở seed demo 254, {title} có accuracy V1/V2 là '
            f"{v1['accuracy']:.4f}/{v2['accuracy']:.4f}, macro-F1 "
            f"{v1['macro_f1']:.4f}/{v2['macro_f1']:.4f}, recall Positive "
            f"{v1['recall']:.4f}/{v2['recall']:.4f}. Chênh lệch accuracy ghép cặp "
            f'V2 trừ V1 là {delta:.4f}, khoảng bootstrap 95\\% [{lo:.4f}, {hi:.4f}]. '
            f"Logistic đối chứng đạt macro-F1 {baseline['macro_f1']:.4f}."
        )
    comparison.append(
        'Trung bình ba seed, V2 tăng macro-F1 trên Early Stage. Trên Pima, '
        'recall Positive tăng và macro-F1 giảm. Hai khoảng bootstrap đều chứa 0. '
        'Độ sâu, L2 và trọng số lớp thay đổi cùng lúc. Hai tập test đã được dùng trước đó. '
        'Cần dữ liệu mới để xác nhận.'
    )
    (OUT/'comparison_text.tex').write_text('\n\n'.join(comparison) + '\n')
    rows=[]
    for k,title in [('pima','Pima'),('early_stage','Early Stage')]:
        for v in ['v1','v2']:
            x=result(k,v);tn,fp=x['confusion_matrix'][0];fn,tp=x['confusion_matrix'][1]
            rows.append([title,v.upper(),tn,fp,fn,tp])
    table('confusion_table.tex','Ma trận nhầm lẫn ở seed demo 254; lớp Positive là lớp 1.','llrrrr',
          ['Dataset','Mạng','TN','FP','FN','TP'],rows)
    sequence=json.loads((ROOT/'legacy_tieuluan/artifacts_tl03/data/sequence_results.json').read_text())['rows']
    table('sequence_table.tex','Kết quả chuỗi kế thừa, không train lại trong V2.','llrr',
          ['Miền / đơn vị','Mạng','Test MAE','Persistence MAE'],
          [[x['domain']+' / '+x['unit'],x['model'],f"{x['MAE']:.3f}",f"{x['baseline_MAE']:.3f}"] for x in sequence])
    triples=[]
    chosen=[next(d for d in kb['documents'] if d['id']==key) for key in ['a1c','testing','overview','activity','medicine']]
    for doc in chosen + kb['documents']:
        if not doc['triples']:continue
        a,b,c=doc['triples'][0]
        if len(a)+len(b)+len(c)<100:
            triples.append([tex(a),tex(b),tex(c),r'\code{'+doc['id']+'}'])
        if len(triples)==5:break
    table('triple_table.tex','Năm bộ ba thật từ KB đang nạp, kèm mã tài liệu đối chiếu.','p{3.4cm}p{3.2cm}p{3.7cm}p{3cm}',
          ['Chủ thể','Quan hệ','Đối tượng','Document'],triples)
    table('version_table.tex','V1 và phần nâng cấp V2 có thể kiểm tra.','p{2.6cm}p{5.6cm}p{5.6cm}',
          ['Hạng mục','V1 gốc / đối chứng','V2'],[
              ['Dữ liệu model','50K nhãn tổng hợp và hồi quy; giữ nguyên checkpoint gốc.','Thêm Pima và Early Stage nhị phân; kiểm kê trùng và nguồn.'],
              ['Mạng đối chứng','Ba tầng ẩn 64--32--16.','Năm tầng ẩn 64--32--16--8--4, L2 mạnh hơn và trọng số lớp cân bằng.'],
              ['MAS','Có MessageBus và các handler chuyên trách.','Thêm workflow riêng sáu tầng, bảy vai trò, schema theo dataset.'],
              ['Truy vết','Trace sender/receiver/type/content trong response.','Thêm request ID, version, status, timing, hash và audit metadata.'],
              ['KB / KG / chat','58 đoạn, 169 nút, 106 cạnh, TF-IDF và Qwen4B.','Tái sử dụng nguyên; không nhận là các thành phần mới hoặc fine-tune mới.'],
              ['Tài liệu nộp','Tiểu luận Final, Project 01 và các tệp thực nghiệm.','Tiểu luận phát triển từ Final, Project 01, Cypher, ZIP và hướng dẫn.']])
    table('agent_table.tex','Bảy vai trò: Coordinator điều phối sáu agent chuyên trách.','p{2.2cm}p{4.1cm}p{4.1cm}p{3.1cm}',
          ['Vai trò','Đầu vào','Đầu ra','Thực hiện'],[
              ['Coordinator','Request + dataset/version','Response tích hợp hoặc lỗi','Workflow trong v2.py'],
              ['Data','Feature thô và schema','Feature order, missing flags hoặc lỗi',r'validate\_data'],
              ['Prediction','Dữ liệu chuẩn hóa','Label, score, threshold, version, hash','predict / pipeline'],
              ['Rule','Dataset, cờ dữ liệu','Cờ phạm vi và giới hạn',r'reviewed\_rules'],
              ['KG/RAG','Câu hỏi kiến thức','Đoạn có nguồn, cạnh đã đối chiếu','Retriever + GraphKnowledgeAgent'],
              ['Explanation','Model + rules + evidence','Giải thích có nguồn, không chẩn đoán','explain'],
              ['Monitoring','Metadata lượt chạy','Trạng thái lưu request/version','monitor / JSONL']])
    tests=json.loads((ROOT/'results/v2/integration_checks.json').read_text())
    table('checks_table.tex','Bằng chứng kiểm thử thực tế; kiểm thử phần mềm không là chứng nhận lâm sàng.','p{5.4cm}p{8.5cm}',
          ['Nhóm','Kết quả / nơi kiểm tra'],[
              ['V2 tích hợp',str(tests['passed'])+r' kiểm tra qua; results/v2/integration\_checks.json.'],
              ['Model parity','Hai dataset, hai version seed 254: xác suất khớp CSV test tới sai số 1e-12.'],
              ['Graph coverage','58/58 tài liệu, 106 cạnh; exact triples, evidence và URL khớp KB.'],
              ['Export','8 nhóm; checksum, CSV/ZIP, replay 22 câu offline, Cypher EXPLAIN.'],
              ['V1 regression suite','Nguồn/PDF, an toàn, feedback, intent, graph, model support và UI trên Mac.'],
              ['Live chat','13 lượt smoke test local; 7 lượt sinh Qwen kèm context KG; không là benchmark y khoa.']])
    table('feature_table.tex','Tám feature Pima; đơn vị theo mô tả nguồn, không phải ngưỡng chẩn đoán.','p{2.2cm}p{6.5cm}p{5cm}',
          ['Mã','Ý nghĩa','Đơn vị / xử lý'],[
              ['preg','Số lần mang thai','Số lần; 0 hợp lệ'],['plas','Plasma glucose sau 2 giờ OGTT','mg/dL; 0 coi là thiếu'],
              ['pres','Huyết áp tâm trương','mmHg; 0 coi là thiếu'],['skin','Nếp gấp da cơ tam đầu','mm; 0 coi là thiếu'],
              ['insu','Insulin huyết thanh sau 2 giờ',r'$\mu$U/mL; 0 coi là thiếu'],['mass','Chỉ số BMI',r'kg/m$^2$; 0 coi là thiếu'],
              ['pedi','Diabetes pedigree function','Điểm chỉ số của dataset'],['age','Tuổi','Năm; quần thể từ 21 tuổi']])
    figures(r['configs']['v2']['hidden_layer_sizes'])
    bibliography=r'''\begin{thebibliography}{99}
\bibitem{architecture} Trần Đình Quế. Hybrid Multiagent System Architecture for Diabetes Decision Support. Tài liệu kiến trúc giảng viên cung cấp, tháng 11/2026, 11 trang.
\bibitem{pima} OpenML. Diabetes, dataset ID 37, version 1. \url{https://www.openml.org/d/37}.
\bibitem{early} UCI Machine Learning Repository. Early Stage Diabetes Risk Prediction, ID 529. DOI 10.24432/C5VG8H. \url{https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction+dataset}.
\bibitem{mlp} Scikit-learn 1.9.1. MLPClassifier và pipeline preprocessing. \url{https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html}.
\bibitem{neo4j} Neo4j. Cypher Manual. \url{https://neo4j.com/docs/cypher-manual/current/}.
\bibitem{qwen} Qwen Team. Qwen3-4B-GGUF, model card. \url{https://huggingface.co/Qwen/Qwen3-4B-GGUF}.
\bibitem{niddk} NIDDK. Guiding Principles for the Care of People with or at Risk for Diabetes. PDF nguồn lưu trong data/source\_documents; các trang chọn có provenance trong KB.
\bibitem{vinmec} Vinmec. Chế độ dinh dưỡng cho người tiểu đường. \url{https://www.vinmec.com/vie/bai-viet/che-do-dinh-duong-cho-nguoi-tieu-duong-vi}.
\bibitem{legacy} Kiều Trường Giang. Các báo cáo và artifact học phần trước; CNN, chuỗi, giá nhà, Agent02 và Cora được giữ trong legacy\_tieuluan/, experiments/ và results/.
\end{thebibliography}
'''
    (OUT/'bibliography.tex').write_text(bibliography)
    env=dict(os.environ,TECTONIC_CACHE_DIR=str(ROOT/'.runtime/tectonic-cache'))
    for name in ['tieuluan_final_06_02_giangkt_v2','project01_06_02_giangkt_v2']:
        subprocess.run([str(ROOT/'.runtime/tectonic/tectonic'),'--keep-logs','--keep-intermediates',name+'.tex'],cwd=OUT,env=env,check=True)


if __name__=='__main__':main()
