from pathlib import Path
import re
r=Path(__file__).resolve().parents[1];p=r/'reports'
old=(p/'tieuluan_final_06_02_giangkt.254.tex').read_text(encoding='utf-8')
if not (p/'thesis_core.tex').exists():
 core=old[old.index(r'\clearpage\section*{CHƯƠNG 1'):old.index(r'\chapter{Giới thiệu}')]
 core=re.sub(r'\\clearpage\\section\*\{CHƯƠNG \d+\. ([^}]+)\}',lambda m:r'\chapter{'+m[1].replace('\n',' ')+'}',core)
 (p/'thesis_core.tex').write_text(core,encoding='utf-8')
pre=(p/'preamble.tex').read_text(encoding='utf-8')
body=(p/'project_body.tex').read_text(encoding='utf-8')
body=body.replace('các vai trò chưa chạy như những dịch vụ tự chủ độc lập.','các agent được gọi qua MessageBus với handler và bộ nhớ trong lượt, chưa chạy như những dịch vụ tự chủ độc lập.')
body=body.replace('Bản hiện tại cần được mở rộng bằng trạng thái riêng, giao thức yêu cầu và phản hồi thực giữa các agent, cơ chế chất vấn khi có bất đồng và kiểm tra lỗi riêng từng thành phần.','Bản hiện tại đã có handler và bộ nhớ theo lượt; hướng mở rộng là bộ nhớ hội thoại bền vững, cơ chế chất vấn khi có bất đồng và triển khai dịch vụ độc lập.')
body=body.replace('Hướng ưu tiên là triển khai giao thức agent thực,','Hướng ưu tiên là mở rộng giao thức agent và bộ nhớ hội thoại,')
body=body.replace('điểm lớn hơn 0,04','điểm lớn hơn giá trị lớn nhất giữa 0,04 và 65\\% điểm của đoạn đứng đầu')
body=body.replace(r'\section{Nhánh dữ liệu}',r'\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{figures/architecture.png}\caption{Hai nhánh hội tụ về điều phối và trợ giúp, dựng lại từ sơ đồ trên bảng.}\end{figure}'+'\n'+r'\section{Nhánh dữ liệu}')
body=body.replace(r'\chapter{Code và demo}',r'\input{project_details.tex}'+'\n'+r'\chapter{Code và demo}')
body+=r'\input{web_walkthrough.tex}'+'\n'
body=body.replace(r'\chapter{Các thành phần và thực nghiệm}',r'\input{data_methodology.tex}\chapter{Các thành phần và thực nghiệm}')
(p/'project_content.tex').write_text(body,encoding='utf-8')
intro=r'''\chapter*{Mở đầu}\addcontentsline{toc}{chapter}{Mở đầu}
Báo cáo nghiên cứu cách kết hợp học máy, học sâu và biểu diễn tri thức trong một hệ thống hỗ trợ người dùng. Các chương đầu trình bày nền tảng, dữ liệu và thực nghiệm trên dữ liệu bảng, ảnh, chuỗi thời gian và đồ thị. Chương 6 và chương 7 mở rộng sang học sâu trên đồ thị, cơ chế phối hợp đa agent và học tăng cường.

Phần II nghiên cứu biểu diễn tri thức, học sâu trên đồ thị và hệ đa agent. Thực nghiệm Cora đối chiếu GCN với MLP trên cùng phép chia dữ liệu; mô phỏng Agent02 khảo sát chính sách học tăng cường và chính sách theo luật. Kết quả được phân tích cùng giới hạn dữ liệu, cách đánh giá và điều kiện tái lập.

Báo cáo kế thừa các tiểu luận học phần, bổ sung thực nghiệm và tổng hợp mối liên hệ giữa các phương pháp. Sản phẩm ứng dụng được trình bày trong báo cáo Project 01 độc lập.
'''
bib=r'''\begin{thebibliography}{99}
\bibitem{tl02} Kiều Trường Giang, Tiểu luận 02, nhóm 06--02, báo cáo học phần.
\bibitem{tl03} Kiều Trường Giang, Tiểu luận 03, B23DCCN254, báo cáo và thực nghiệm học phần.
\bibitem{linh} Phạm Mai Linh, Tiểu luận 01, nhóm 06--03, báo cáo học phần.
\bibitem{kien} Nguyễn Tự Kiên, Tiểu luận final CT\_07 và Project01 CT\_07, báo cáo học phần.
\bibitem{lam} Bùi Văn Lâm, Tiểu luận final CT\_03 và Project01 CT\_03, mã 477, báo cáo học phần.
\bibitem{gcn} T. Kipf và M. Welling, Semi-Supervised Classification with Graph Convolutional Networks, ICLR 2017. \url{https://arxiv.org/abs/1609.02907}.
\bibitem{sage} W. Hamilton, R. Ying và J. Leskovec, Inductive Representation Learning on Large Graphs, 2017. \url{https://arxiv.org/abs/1706.02216}.
\bibitem{gat} P. Velickovic và cộng sự, Graph Attention Networks, ICLR 2018. \url{https://arxiv.org/abs/1710.10903}.
\bibitem{rgcn} M. Schlichtkrull và cộng sự, Modeling Relational Data with Graph Convolutional Networks, 2017. \url{https://arxiv.org/abs/1703.06103}.
\bibitem{diabetes} Scikit-learn, tài liệu load\_diabetes. \url{https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_diabetes.html}.
\bibitem{risk} Mobeen Fatimah, Diabetes Risk Prediction Dataset 50K Patients. \url{https://www.kaggle.com/datasets/mobeenfatimah/diabetes-risk-prediction-dataset-50k-patients}.
\bibitem{niddk} NIDDK, Diabetes Tests and Diagnosis. \url{https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis}.
\bibitem{kb} Danh mục nguồn tri thức của project được lưu tại data/knowledge.json; mỗi đoạn văn có mã tài liệu, mã nguồn và các bộ ba có căn cứ.
\end{thebibliography}
'''
(p/'bibliography.tex').write_text(bib,encoding='utf-8')
(p/'bibliography_thesis.tex').write_text('\n'.join(line for line in bib.splitlines() if not any(key in line for key in [r'\bibitem{diabetes}',r'\bibitem{niddk}',r'\bibitem{kb}'])),encoding='utf-8')
for fn,title,content in [('tieuluan_final_06_02_giangkt.254','TIỂU LUẬN FINAL',intro+r'\input{abbreviations.tex}\input{data_overview.tex}\part{Nền tảng và tổng hợp}\input{thesis_core.tex}\input{theory_extension.tex}\input{thesis_conclusion.tex}'),('project01_06_02_giangkt.254','PROJECT 01',r'\setcounter{secnumdepth}{2}\input{project_content.tex}')]:
 cover=r'''\begin{document}\begin{titlepage}\centering
{\large HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG\\KHOA CÔNG NGHỆ THÔNG TIN 1}\vfill
{\LARGE\bfseries '''+title+r'''}\par\vspace{1cm}
{\Large\bfseries '''+('HỌC MÁY, BIỂU DIỄN TRI THỨC VÀ HỆ ĐA AGENT' if 'final' in fn else 'HỆ ĐA AGENT CHO BỆNH TIỂU ĐƯỜNG')+r'''}\par\vspace{1cm}
{\large PHÁT TRIỂN CÁC HỆ THỐNG THÔNG MINH}\vfill
\begin{tabular}{ll}Giảng viên:&PGS. TS. Trần Đình Quế\\Sinh viên:&Kiều Trường Giang\\Mã sinh viên:&B23DCCN254\\Nhóm học phần:&06\\Nhóm thực hiện:&02\end{tabular}\vfill
Hà Nội, tháng 11 năm 2026\end{titlepage}\pagenumbering{roman}\tableofcontents\clearpage\listoffigures\clearpage\listoftables\clearpage\pagenumbering{arabic}
'''
 appendix=r'\input{bibliography.tex}\appendix\chapter{Mã nguồn tái lập}'+'\n'
 for f in (['scripts/train_cora.py'] if 'final' in fn else ['scripts/ingest_graph.py','scripts/train_models.py','scripts/train_policy.py','app/agents.py','app/conversation.py','app/main.py','scripts/test_scenarios.py','scripts/test_chatbot.py']):
  appendix+=r'\section{'+f.replace('_',r'\_')+'}\n'+r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{../'+f+'}\n'
 if 'final' in fn:
  appendix=appendix.replace(r'\input{bibliography.tex}',r'\input{bibliography_thesis.tex}')
 (p/(fn+'.tex')).write_text(pre+cover+content+appendix+r'\end{document}',encoding='utf-8')
print('Report sources assembled')
