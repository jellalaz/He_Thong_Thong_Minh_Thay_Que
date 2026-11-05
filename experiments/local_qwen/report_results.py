import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
R=Path(__file__).resolve().parents[2];out=R/'results/local_qwen'
s=json.loads((out/'training_summary.json').read_text());logs=json.loads((out/'learning.json').read_text());ev=json.loads((out/'generation_checks.json').read_text())
f=FontProperties(fname='C:/Windows/Fonts/times.ttf',size=11)
fig,ax=plt.subplots(figsize=(8,3.7))
ax.plot([x['step'] for x in logs],[x['train_loss'] for x in logs],color='black',lw=1,label='Training loss (4 mẫu/bước)')
v=[x for x in logs if 'validation_loss' in x]
ax.plot([0]+[x['step'] for x in v],[s['baseline_validation_loss']]+[x['validation_loss'] for x in v],color='black',linestyle='--',marker='o',label='Validation loss')
ax.set_xlabel('Bước cập nhật',fontproperties=f);ax.set_ylabel('Cross-entropy',fontproperties=f);ax.legend(prop=f);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(R/'reports/figures/qwen_learning.png',dpi=220);plt.close(fig)
rows=[]
for model,label in [('base','Qwen nền'),('lora','Qwen LoRA')]:
 for group,gl in [('knowledge','Kiến thức'),('dialogue','Hội thoại')]:
  x=ev[model][group];rows.append(f"{label} & {gl} & {x['citation_present']}/{x['n']} & {x['unknown_citation_cases']} & {x['token_limit_cases']} & {x['mean_seconds']:.2f}"+r"\\")
tex=r"""\subsection{Kết quả đo trên máy thực nghiệm}
Số tham số được tối ưu là PARAMS, trên tổng TOTAL tham số. Checkpoint được chọn ở epoch EPOCH. Loss validation của mô hình nền là BASELOSS; giá trị tốt nhất sau tinh chỉnh là BESTLOSS. Thời gian ba epoch, gồm đánh giá validation và lưu checkpoint, là MINUTES phút. Bộ nhớ GPU cấp phát đỉnh do PyTorch ghi nhận là MEMORY GiB; số này không bao gồm toàn bộ bộ nhớ các ứng dụng khác.
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{figures/qwen_learning.png}\caption{Loss huấn luyện theo bước và validation theo epoch. Điểm đầu validation thuộc mô hình nền.}\end{figure}
\begin{table}[H]\centering\small
\begin{tabular}{llrrrr}\toprule
Mô hình & Nhóm & Có dẫn mã & Mã lạ & Chạm giới hạn & Giây/câu\\\midrule
ROWS
\bottomrule\end{tabular}
\caption{Kiểm tra hình thức đầu ra trên hai nhóm test, mỗi nhóm 8 câu.}\end{table}
Có dẫn mã chỉ kiểm tra sự xuất hiện của mã tài liệu, không chứng minh trích dẫn hỗ trợ đầy đủ câu trả lời. Mã lạ là mã không nằm trong ngữ cảnh đã cấp. Chạm giới hạn nghĩa là sinh đủ 320 token, có nguy cơ câu bị cắt. Độ trễ được đo sau khi mô hình đã nạp, không gồm thời gian khởi động hoặc truy xuất Neo4j. Hai mô hình dùng cùng ngữ cảnh được chỉ định trước để tách ảnh hưởng của bộ sinh; kết quả này chưa đo toàn bộ pipeline truy xuất.

Tệp \path{results/local_qwen/base_answers.json} và \path{results/local_qwen/lora_answers.json} lưu nguyên văn từng phản hồi. Tệp \path{results/local_qwen/training_summary.json} lưu cấu hình, mã băm dữ liệu và tài nguyên đo được. Các tệp này cho phép kiểm tra lại kết luận mà không cần dựa vào ảnh minh họa.
"""
for key,value in {'PARAMS':f"{s['trainable_parameters']:,}",'TOTAL':f"{s['total_parameters']:,}",'EPOCH':s['best_epoch'],'BASELOSS':f"{s['baseline_validation_loss']:.4f}",'BESTLOSS':f"{s['best_validation_loss']:.4f}",'MINUTES':f"{s['training_seconds']/60:.2f}",'MEMORY':f"{s['peak_gpu_gib']:.2f}",'ROWS':'\n'.join(rows)}.items():tex=tex.replace(key,str(value))
(R/'reports/local_qwen_results.tex').write_text(tex,encoding='utf-8')
print('Wrote training figure and result section')
