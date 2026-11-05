from pathlib import Path
import re
r=Path(__file__).resolve().parents[1];p=r/'reports'
old=(p/'tieuluan_final_06_02_giangkt.254.tex').read_text(encoding='utf-8')
if not (p/'thesis_core.tex').exists():
 core=old[old.index(r'\clearpage\section*{CHƯƠNG 1'):old.index(r'\chapter{Giới thiệu}')]
 core=re.sub(r'\\clearpage\\section\*\{CHƯƠNG \d+\. ([^}]+)\}',lambda m:r'\chapter{'+m[1].replace('\n',' ')+'}',core)
 (p/'thesis_core.tex').write_text(core,encoding='utf-8')
pre=old[:old.index(r'\begin{document}')].replace(r'\setcounter{secnumdepth}{-1}',r'\setcounter{secnumdepth}{0}')
pre+=r'\usepackage{xurl}\hypersetup{hypertexnames=false}\renewcommand{\bibname}{Tài liệu tham khảo}\renewcommand{\appendixname}{Phụ lục}\renewcommand{\partname}{Phần}\makeatletter\patchcmd{\@makechapterhead}{50\p@}{15\p@}{}{}\patchcmd{\@makechapterhead}{40\p@}{20\p@}{}{}\makeatother'+'\n'
body=(p/'project_body.tex').read_text(encoding='utf-8')
body=body.replace('các vai trò chưa chạy như những dịch vụ tự chủ độc lập.','các agent được gọi qua MessageBus với handler và bộ nhớ trong lượt, chưa chạy như những dịch vụ tự chủ độc lập.')
body=body.replace('Bản hiện tại cần được mở rộng bằng trạng thái riêng, giao thức yêu cầu và phản hồi thực giữa các agent, cơ chế chất vấn khi có bất đồng và kiểm tra lỗi riêng từng thành phần.','Bản hiện tại đã có handler và bộ nhớ theo lượt; hướng mở rộng là bộ nhớ hội thoại bền vững, cơ chế chất vấn khi có bất đồng và triển khai dịch vụ độc lập.')
body=body.replace('Hướng ưu tiên là triển khai giao thức agent thực,','Hướng ưu tiên là mở rộng giao thức agent và bộ nhớ hội thoại,')
body=body.replace('điểm lớn hơn 0,04','điểm lớn hơn giá trị lớn nhất giữa 0,04 và 65\\% điểm của đoạn đứng đầu')
body=body.replace(r'\section{Nhánh dữ liệu}',r'\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{figures/architecture.png}\caption{Hai nhánh hội tụ về điều phối và trợ giúp, dựng lại từ sơ đồ trên bảng.}\end{figure}'+'\n'+r'\section{Nhánh dữ liệu}')
body=body.replace(r'\chapter{Code và demo}',r'\input{project_details.tex}'+'\n'+r'\chapter{Code và demo}')
body=body.replace('Địa chỉ localhost chỉ hoạt động',r'Demo công khai tại thời điểm hoàn thiện: \url{https://bear-parental-pair-mercury.trycloudflare.com}. Đây là đường hầm tạm thời, phụ thuộc máy và tiến trình đang chạy; không phải hosting thường trực. Địa chỉ localhost chỉ hoạt động')
body+=r'''\begin{figure}[htbp]\centering\includegraphics[width=\linewidth,height=.65\textheight,keepaspectratio]{demo-classification.png}\caption{Suy luận phân loại từ mẫu của bộ dữ liệu.}\end{figure}
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth,height=.65\textheight,keepaspectratio]{demo-regression.png}\caption{Đầu ra hồi quy là điểm tiến triển nghiên cứu.}\end{figure}
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{demo-neo4j.png}\caption{Neo4j Browser đã kết nối và trả về các quan hệ Concept.}\end{figure}

\section{Ảnh chụp sản phẩm đang chạy}
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth,height=.72\textheight,keepaspectratio]{demo-chat.png}\caption{Chatbot trả lời HbA1c kèm mã tài liệu và liên kết nguồn.}\end{figure}
\begin{figure}[htbp]\centering\includegraphics[width=\linewidth,height=.72\textheight,keepaspectratio]{demo-graph.png}\caption{Lọc quan hệ theo tài liệu a1c, dữ liệu đọc trực tiếp từ Neo4j.}\end{figure}
\clearpage
'''
(p/'project_content.tex').write_text(body,encoding='utf-8')
intro=r'''\chapter*{Mở đầu}\addcontentsline{toc}{chapter}{Mở đầu}
Báo cáo tổng hợp nền tảng trí tuệ nhân tạo, học máy, mạng nơ-ron, đồ thị tri thức và cơ chế phối hợp đa agent. Phần thứ nhất kế thừa nội dung của tiểu luận 02 và 03 của Kiều Trường Giang, đồng thời bổ sung học sâu trên đồ thị và hệ đa agent. Tiểu luận 01 của Phạm Mai Linh được dùng làm tài liệu tham khảo nền tảng theo lựa chọn của sinh viên; các số liệu không được nhận là kết quả mới nếu chỉ xuất hiện trong tài liệu tham khảo.

Phần thứ hai triển khai một sản phẩm mới theo sơ đồ trên lớp: dữ liệu có sẵn đi qua mô hình Deep Learning để tạo kết quả phân loại và dự đoán; nguồn tri thức đi qua KB và RAG; các thành phần được điều phối bằng agent, chính sách học và luật để đưa ra phản hồi. Báo cáo project riêng trình bày chi tiết kiến trúc, thực nghiệm, API và kịch bản demo. Các số liệu mới đều có tệp kết quả trong thư mục results.

Bố cục tham khảo hai báo cáo của Nguyễn Tự Kiên do sinh viên cung cấp. Bản hiện thực không nhận các bộ dữ liệu, số agent hoặc kết quả của bài tham khảo là thành phần đã được triển khai. Cơ chế sinh phản hồi hiện là tổng hợp trích đoạn có nguồn; GNN trong phần lý thuyết chưa được huấn luyện trong demo.
'''
bib=r'''\begin{thebibliography}{99}
\bibitem{tl02} Kiều Trường Giang, Tiểu luận 02, nhóm 06--02, tài liệu học phần do sinh viên cung cấp.
\bibitem{tl03} Kiều Trường Giang, Tiểu luận 03, B23DCCN254, tài liệu và thực nghiệm học phần do sinh viên cung cấp.
\bibitem{linh} Phạm Mai Linh, Tiểu luận 01, nhóm 06--03, tài liệu tham khảo do sinh viên chỉ định.
\bibitem{kien} Nguyễn Tự Kiên, Tiểu luận final CT\_07 và Project01 CT\_07, hai PDF tham khảo về bố cục do sinh viên cung cấp.
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
for fn,title,content in [('tieuluan_final_06_02_giangkt.254','TIỂU LUẬN FINAL',intro+r'\part{Nền tảng và tổng hợp}\input{thesis_core.tex}\input{theory_extension.tex}\part{Project tích hợp}\setcounter{chapter}{0}\setcounter{secnumdepth}{1}\input{project_content.tex}'),('project01_06_02_giangkt.254','PROJECT 01',r'\setcounter{secnumdepth}{1}\input{project_content.tex}')]:
 cover=r'''\begin{document}\begin{titlepage}\centering
{\large HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG\\KHOA CÔNG NGHỆ THÔNG TIN 1}\vfill
{\LARGE\bfseries '''+title+r'''}\par\vspace{1cm}
{\Large\bfseries '''+('AI, HỌC MÁY VÀ HỆ ĐA AGENT' if 'final' in fn else 'HỆ ĐA AGENT CHO BỆNH TIỂU ĐƯỜNG')+r'''}\par\vspace{1cm}
{\large PHÁT TRIỂN CÁC HỆ THỐNG THÔNG MINH}\vfill
\begin{tabular}{ll}Giảng viên:&PGS. TS. Trần Đình Quế\\Sinh viên:&Kiều Trường Giang\\Mã sinh viên:&B23DCCN254\\Nhóm học phần:&06\\Nhóm thực hiện:&02\end{tabular}\vfill
Hà Nội, tháng 11 năm 2026\end{titlepage}\pagenumbering{roman}\tableofcontents\clearpage\pagenumbering{arabic}
'''
 appendix=r'\input{bibliography.tex}\appendix\chapter{Mã nguồn tái lập}'+'\n'
 for f in ['scripts/ingest_graph.py','scripts/train_models.py','scripts/train_policy.py','app/agents.py','app/main.py','scripts/test_scenarios.py']:
  appendix+=r'\section{'+f.replace('_',r'\_')+'}\n'+r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{../'+f+'}\n'
 (p/(fn+'.tex')).write_text(pre+cover+content+appendix+r'\end{document}',encoding='utf-8')
print('Report sources assembled')
