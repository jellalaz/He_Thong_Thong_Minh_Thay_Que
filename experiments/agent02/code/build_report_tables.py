from pathlib import Path
import csv,numpy as np
root=Path(__file__).resolve().parents[1]
out=root/'tables';out.mkdir(exist_ok=True)
def read(f):return list(csv.DictReader((root/'data'/f).open()))
def table(filename,caption,label,headers,rows,align=None,note=''):
 s='\\begin{table}[H]\\centering\\small\n\\caption{'+caption+'}\\label{'+label+'}\n'
 s+='\\begin{tabular}{'+(align or ('l'+'r'*(len(headers)-1)))+'}\\toprule\n'
 s+=' & '.join(headers)+'\\\\\\midrule\n'
 s+='\n'.join(' & '.join(map(str,row))+'\\\\' for row in rows)
 s+='\n\\bottomrule\\end{tabular}\n'
 if note:s+='\\par\\vspace{4pt}{\\footnotesize '+note+'}\n'
 s+='\\end{table}\n'
 (out/filename).write_text(s)
base=read('original_baseline_evaluation.csv')
table('baseline.tex','Kết quả đánh giá baseline: 500 episode, 10.000 bước','tab:baseline',['Agent','Tổng reward',r'$\bar R$',r'Không giảm','Giảm'],[[r['agent'],f"{float(r['total_reward']):.0f}",f"{float(r['mean_reward_per_step']):.4f}",r['no_discount_actions'],r['discount_actions']] for r in base],note=r'\sourceoriginal\ Tỷ lệ giảm giá của cả hai agent bằng 0\%.')
q=[['(0,0)','228.302398','178.849438','0'],['(0,1)','177.992001','207.205116','1'],['(1,0)','246.879938','235.233833','0'],['(1,1)','211.419819','242.962865','1']]
table('qtable.tex','Bảng Q và policy sau huấn luyện baseline seed 42','tab:qtable',['Trạng thái',r'$Q(s,0)$',r'$Q(s,1)$','Greedy'],q,align='lrrc',note=r'\sourceoriginal\ Giá trị Q là ước lượng return chiết khấu, không phải lợi nhuận trung bình mỗi bước.')
seed=read('original_multi_seed_summary.csv');rows=[]
for s in ['11','22','33','44','55']:
 pair={r['agent']:float(r['mean_reward_per_step']) for r in seed if r['seed']==s}
 rows.append([s,f"{pair['RL']:.4f}",f"{pair['Rule-based']:.4f}",f"{pair['RL']-pair['Rule-based']:+.4f}"])
rows.append(['Trung bình','34.8919','34.9321','-0.0402'])
rows.append(['SD mẫu','0.3132','0.2496','0.0754'])
table('seeds.tex','Reward đánh giá qua năm seed và chênh lệch theo cặp','tab:seeds_results',['Seed','RL','Theo luật','RL - luật'],rows,note=r'\sourceoriginal\ Mỗi seed gồm một lần huấn luyện và một lần đánh giá mới; cả hai agent đều không giảm giá trên các lượt đánh giá này.')
training=read('training_summary.csv')
for kind,filename,label,caption in [('alpha_','alpha.tex','tab:alpha','Learning rate: hiệu năng huấn luyện và đánh giá'),('exploration_','exploration.tex','tab:exploration','Exploration: hiệu năng huấn luyện và đánh giá')]:
 rows=[]
 for r in training:
  if not r['experiment'].startswith(kind):continue
  name=r['experiment'].replace(kind,'')
  names={'low':'Low','baseline':'Baseline','high':'High','fixed005':'Fixed 0.05','fixed030':'Fixed 0.30'}
  rows.append([names.get(name,name)]+[f'{float(r[k]):.4f}' for k in ['training_mean','first100','last100','evaluation_mean']]+[f"{float(r['discount_rate'])*100:.2f}\\%"])
 table(filename,caption,label,['Cấu hình',r'\shortstack{Train\\toàn bộ}',r'\shortstack{100 ep.\\đầu}',r'\shortstack{100 ep.\\cuối}',r'Eval',r'$\rho$ eval'],rows,note=r'\sourcesupp\ Mỗi dòng là một seed huấn luyện của nhóm; không dùng các dòng này để ước lượng SD giữa seed.')
rob=read('robustness_summary.csv');rows=[]
for r in rob:
 condition={'robust_base_':r'20\%, gốc','robust_frozen_':r'5\%, đóng băng','robust_retrained_':r'5\%, học lại'}[r['condition']]
 rows.append([condition, r['agent'],f"{float(r['mean']):.4f}",f"{float(r['std']):.4f}",f"{float(r['discount_rate'])*100:.2f}\\%"])
table('robustness.tex','Thay đổi chiết khấu: trung bình và SD mẫu qua năm seed','tab:robustness',['Điều kiện','Agent','Mean','SD',r'$\rho$'],rows,align='llrrr',note=r'\sourcesupp\ Pha đánh giá luôn giữ policy cố định. “Học lại” nghĩa là huấn luyện mới trước khi đánh giá.')
rows=[]
for d in [0,1]:
 for b in [0,1]:
  vals=[]
  for delta in [.20,.05]:
   for a in [0,1]:
    p=np.clip(.30+.25*d+.15*a-.10*b,.05,.95)
    vals.append(f'{(10 if d==0 else 20)*p*(10*(1-delta*a)-5):.2f}')
  rows.append([str(d),str(b)]+vals)
table('expected_reward.tex','Lợi nhuận kỳ vọng một bước, có điều kiện theo hành động hiện tại của đối thủ','tab:expected',['$d$','$a_{-i}$',r'\shortstack{$\delta=20\%$\\$a_i=0$}',r'\shortstack{$\delta=20\%$\\$a_i=1$}',r'\shortstack{$\delta=5\%$\\$a_i=0$}',r'\shortstack{$\delta=5\%$\\$a_i=1$}'],rows,align='ccrrrr',note='Nguồn: tính giải tích từ công thức mô hình; đây không phải số liệu lấy mẫu.')
if (root/'data/planning_benchmark.csv').exists():
 data=read('planning_benchmark.csv');rows=[]
 for delta in [.2,.05]:
  rr=[r for r in data if float(r['delta'])==delta and r['policy']=='Planning']
  v=[float(r['mean_reward_per_step']) for r in rr]
  rows.append([f'{delta*100:.0f}\\%',f"{float(rr[0]['expected_planning_mean']):.4f}",f'{np.mean(v):.4f}',f'{np.std(v,ddof=1):.4f}',f"{np.mean([float(r['discount_action_rate']) for r in rr])*100:.0f}\\%"])
 table('planning.tex','Mốc lập kế hoạch biết mô hình và kết quả đánh giá qua năm seed','tab:planning',[r'$\delta$','Kỳ vọng chính xác','Mean đo','SD đo',r'$\rho$'],rows,note='Mốc này biết đúng môi trường và luật đối thủ, không phải agent học từ dữ liệu. Kỳ vọng được tính cho cùng horizon 20 bước và trạng thái reset của thí nghiệm.')
