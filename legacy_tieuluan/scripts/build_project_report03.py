"""Xuất tài liệu project từ cùng nội dung phân tích đã dùng cho báo cáo Word."""
from pathlib import Path
import json
from report_details03 import add_details

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'artifacts_tl03/data';FIG=ROOT/'artifacts_tl03/figures'
parts=[]
def p(s,*args,**kwargs):parts.append(str(s))
def h(s,level=2,*args,**kwargs):parts.append('#'*min(level+1,5)+' '+s)
def table(headers,rows,caption,*args,**kwargs):
    p(caption)
    parts.append('| '+' | '.join(map(str,headers))+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rows))
def image(path,caption,*args,**kwargs):p('!['+caption+']('+str(Path(path).relative_to(ROOT))+')\n\n'+caption)
def eq(s,*args,**kwargs):p('$$\n'+s+'\n$$')
def link(label,url,*args,**kwargs):p('['+label+']('+url+')')
ctx={'DATA':DATA,'FIG':FIG,'TAB':json.loads((DATA/'tabular_results.json').read_text()),'RED':'FF0000',
     'para':p,'heading':h,'table':table,'picture':image,'equation':eq,'link_line':link}
p('# Phân tích và triển khai các bài toán trong project')
p('Kiều Trường Giang — B23DCCN254. Tài liệu này giải thích dữ liệu, cơ chế và giới hạn của các chức năng đang triển khai, đi kèm bằng chứng từ `main.ipynb`, CSV dự đoán và checkpoint. Báo cáo học phần đầy đủ nằm trong Word/PDF năm chương; các phần dưới tập trung vào đường đi của từng bài toán lên web.')
link('Web','https://rag-httm-chatbot.vercel.app/')
link('GitHub','https://github.com/jellalaz/HTTM_ThayQue')
p('## Chạy và tái lập')
p('Chọn Run All trong `main.ipynb`, chế độ full, seed 42. Notebook nhúng mã huấn luyện, phân tích và đóng gói, tự tải dữ liệu công khai khi thiếu. Cache được kiểm tra bằng hash. Lần kiểm chứng full CPU gồm ML, CNN 8 epoch và sáu mạng chuỗi 35 epoch/mạng. Phân tích bổ sung không train lại trọng số, không đổi lựa chọn theo test. Raw dữ liệu được tải lại từ URL/hash trong manifest; không đưa token vào repository.')
table(['Chức năng','Đầu vào → đầu ra','Đường xử lý'],[
 ['Giá nhà','11 thuộc tính → tỷ VND','API /api/predict; task=housing'],
 ['Nhãn nguy cơ tổng hợp','8 số → High/Moderate/Low','API; task=diabetes_classifier'],
 ['CNN','784 pixel → chữ số 0–9','API; task=cnn'],
 ['Chuỗi FPT/vàng','30 log-return + giá → giá bước tiếp theo','API; task=sequence'],
 ['Hồi quy y tế gốc','10 biến nghiên cứu → điểm tiến triển','JavaScript trong trình duyệt'],
 ['FPT/vàng gốc','Đặc trưng thị trường → dự báo một bước','JavaScript; cấu hình TL02'],
 ['Chatbot sức khỏe','Câu hỏi + ngữ cảnh → thông tin có căn cứ','BM25 + KG + state machine trong trình duyệt']], 'Các luồng triển khai không được đánh đồng với nhau')
p('<a id="gia-nha"></a>\n<a id="phan-loai-nguy-co"></a>\n## 1. Hai bài toán Machine Learning')
d=ctx['TAB']['diabetes_classifier'];house=ctx['TAB']['housing']
p('Classifier học từ Diabetes Risk Prediction 50.000 dòng tổng hợp, chia 32.000/8.000/10.000; Random Forest 80 cây, depth 10, class_weight balanced được chọn bằng StratifiedKFold 3 phần. Giá nhà dùng 30.229 tin đăng Vietnam Housing 2024, chia 19.377/4.491/6.361; Log Random Forest 80 cây, depth 14, leaf tối thiểu 3 được chọn bằng GroupKFold 3 phần. Các biến tiền xử lý luôn fit trong train của fold.')
table(['Bài toán','CV','Test','Checkpoint'],[
 ['Nguy cơ tổng hợp',f"macro-F1 {d['CV_F1_macro']:.6f}",f"Accuracy {d['metrics']['Accuracy']:.6f}; macro-F1 {d['metrics']['F1_macro']:.6f}",'artifacts_tl03/models/diabetes_classifier.joblib'],
 ['Giá nhà',f"MAE {house['CV_MAE']:.6f}",f"MAE {house['metrics']['MAE']:.6f}; R² {house['metrics']['R2']:.6f}",'artifacts_tl03/models/housing.joblib']], 'Kết quả chọn mô hình và đánh giá giữ riêng')
for key in ['ml_data','ml_errors']:add_details(key,ctx)
p('<a id="cnn-chu-so"></a>\n## 2. CNN nhận dạng chữ số')
p('MNIST giữ 10.000 ảnh test chính thức, chia 60.000 ảnh train gốc thành 48.000 train và 12.000 validation. Pixel chia 255; chỉ train dịch ảnh ±1 pixel. CNN 52.138 tham số train từ đầu bằng Adam 0,001, weight decay 0,0001, batch 128, clip norm 1, tám epoch. Checkpoint chọn validation loss thấp nhất tại epoch 8; Accuracy test 0,9866, macro-F1 0,986487. Không dùng pretrained.')
for key in ['cnn_mechanism','cnn_errors']:add_details(key,ctx)
p('<a id="chuoi-thoi-gian"></a>\n## 3. RNN/LSTM/GRU dự báo FPT và vàng')
p('Snapshot FPT.VN và GC=F từ 15/10/2021 đến 14/10/2026. Mỗi mạng có một recurrent layer, hidden 16 và head tuyến tính; train 35 epoch, batch 128, Adam 0,001, clip norm 1. Scaling chỉ fit train. Chọn checkpoint bằng validation MSE; chọn kiến trúc web bằng validation MAE với Persistence cùng tham gia. FPT chọn GRU, vàng chọn Persistence. Các ngày test là ngày nhãn, không phải ngày đặc trưng của pipeline TL02.')
p('GRU inference dùng đúng quy ước PyTorch: reset gate nhân sau phép biến đổi tuyến tính của hidden state trong nhánh ứng viên; update gate z đặt trọng số lên hidden cũ, h=(1−z)·n+z·h_cũ. Một số cách trình bày lý thuyết đặt reset trước ma trận và dùng z cho ứng viên. Không trộn hai quy ước khi xuất checkpoint; bộ test so sánh cả sáu mạng kiểm tra điều này bằng đầu ra số thực.')
rows=json.loads((DATA/'sequence_results.json').read_text())['rows']
table(['Miền/mạng','Val MAE','Test MAE','Test RMSE'],[[r['domain']+'/'+r['model'],f"{r['validation_MAE']:.3f}",f"{r['MAE']:.3f}",f"{r['RMSE']:.3f}"] for r in rows],'Đơn vị VND đối với FPT và USD/oz đối với GC=F')
for key in ['sequence_mechanism','sequence_errors']:add_details(key,ctx)
p('## 4. Ba miền dự đoán gốc: dữ liệu và cách phân tích')
p('### Hồi quy tiến triển bệnh')
p('Bộ diabetes có 442 người đã mắc bệnh, 10 biến đầu vào nghiên cứu và nhãn định lượng tiến triển sau một năm. Train/calibration/test là 282/71/89. Ridge được chọn theo CV MAE 44,442606; test MAE 42,936402, RMSE 53,861835, R² 0,452432. Baseline trung vị có MAE 62,275281 trên cùng test. Sai số được tính trên thang điểm nghiên cứu, không phải mg/dL, HbA1c hoặc phần trăm mắc bệnh.')
p('Chuẩn hóa dùng thống kê train. Calibration 71 mẫu tạo bán kính sai số danh nghĩa 90%, khoảng 85,446193 điểm. Coverage quan sát test là 0,865169, không đạt đúng 90% trong mẫu hữu hạn. Khoảng rộng phản ánh giới hạn dự đoán cá nhân. Form phân biệt bp là huyết áp trung bình với cặp tâm thu/tâm trương; s5 là đặc trưng nghiên cứu, không tự đổi thành xét nghiệm triglyceride. Trung vị điền thiếu chỉ phục vụ mô hình, không được chuyển thành số đo đã quan sát của người dùng trong chatbot.')
p('### FPT và vàng của pipeline gốc')
p('Lịch sử giá được sắp theo thời gian, tạo đặc trưng từ các quan sát đã có như lợi suất, trung bình động, RSI và biến động; nhãn là giá của bước tiếp theo. Phép chia calibration/test theo thời gian và TimeSeriesSplit trong train tránh dùng tương lai để chọn cấu hình. FPT chọn Persistence với CV MAE 1.215,9737 VND và test MAE 728,1284 VND; GC=F chọn SVR return với CV MAE 38,7920 USD/oz và test MAE 49,4405 USD/oz. Test R² lần lượt khoảng 0,8714 và 0,8803.')
p('R² cao của mức giá không đồng nghĩa dự báo được xu hướng giao dịch, vì giá liên tiếp thường rất gần nhau. Việc FPT chọn Persistence là kết quả hợp lệ của quy tắc chọn, không phải một mô hình neural bị thay tên. Vàng futures GC=F không phải spot XAU/USD hoặc giá SJC. Chỉ số ở đây không được so trực tiếp với Chương 4 như cùng test vì cách gắn ngày nhãn/đặc trưng khác nhau. Tham số, khoảng calibration và đối chiếu test/refit được lưu trong `web_model_config.json` và kết quả legacy.')
link('Demo ba miền gốc','https://rag-httm-chatbot.vercel.app/#predict')
p('## 5. Knowledge Graph, truy xuất và chatbot')
add_details('rag_trace',ctx)
p('## 6. Tệp bằng chứng và cách kiểm tra')
table(['Loại','Tệp / thư mục'],[
 ['Mã thực nghiệm','src/experiments03.py; nhúng trong main.ipynb'],['Phân tích bổ sung','src/analysis03.py; nhúng trong main.ipynb'],
 ['Chia dữ liệu','artifacts_tl03/data/*_split.csv'],['Dự đoán','artifacts_tl03/data/*_predictions.csv'],
 ['Đường học','artifacts_tl03/data/*_history.csv'],['Nguồn từng hình mới','artifacts_tl03/data/figure_lineage.json'],
 ['Phân tích tổng hợp','artifacts_tl03/data/extended_analysis.json'],['Đối chiếu export','tests/test_inference03.py'],
 ['Chức năng cũ','tests/engine.test.cjs; tests/clinical.test.cjs'],['Production HTTP','tests/check_production03.py; production_verified.json']], 'Điểm bắt đầu để tái lập hoặc kiểm tra một kết luận')
p('Chạy `python tests/test_inference03.py`, `node tests/engine.test.cjs`, `node tests/clinical.test.cjs` sau khi build. Kiểm tra production dùng mẫu công khai/tổng hợp, không dùng dữ liệu riêng của người dùng. Độ đúng phần mềm, hiệu năng thống kê và tính phù hợp cho y tế/tài chính là ba phạm vi khác nhau; test phần mềm không phải chứng nhận chuyên môn. Chưa có kiểm chứng GPU, nhiều seed, dữ liệu lâm sàng bên ngoài hoặc benchmark độc lập chất lượng câu trả lời.')
(ROOT/'PROJECT_REPORT.md').write_text('\n\n'.join(parts)+'\n',encoding='utf-8')
print('PROJECT_REPORT.md:',len(parts),'blocks')
