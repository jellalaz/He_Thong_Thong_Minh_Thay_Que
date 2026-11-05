GLUCOGUIDE — TIỂU LUẬN FINAL VÀ PROJECT 01
Kiều Trường Giang · B23DCCN254 · Nhóm 06–02

1. MỞ SẢN PHẨM TRÊN MÁY NÀY
- Web: http://localhost:8765
- Neo4j Browser: http://localhost:7474/browser/
- Địa chỉ kết nối Neo4j: neo4j://127.0.0.1:7687; tài khoản neo4j.
- Mật khẩu nằm trong tệp .env trên máy, dòng NEO4J_PASSWORD. Tệp này không đưa lên GitHub.
- Browser đã được đăng nhập và mở truy vấn đồ thị ở phiên hoàn thiện.
- Demo công khai: https://glucoguide-giang254.vercel.app
  Vercel Hobby + Neo4j AuraDB Free. Không cần bật máy cá nhân; chỉ dùng gói miễn phí.

2. CHẠY LẠI
Mở PowerShell trong thư mục này:
  .\start-neo4j.ps1
  .\run.ps1
Để chạy trên máy khác, cài Python 3.14, tạo venv, cài requirements.txt.
Sao chép .env.example thành .env và điền mật khẩu Neo4j của máy đó.
Có thể dùng Docker Compose (docker compose up -d neo4j) hoặc Neo4j cài riêng.
Sau khi Neo4j sẵn sàng:
  .\.venv\Scripts\python.exe scripts/ingest_graph.py
  .\run.ps1
Checkpoint đã kèm trong models, không cần train lại để demo.

3. KỊCH BẢN BẢO VỆ (KHOẢNG 8–10 PHÚT)
- Giới thiệu sơ đồ hai nhánh trong báo cáo.
- Trợ lý kiến thức: chọn “HbA1c là gì?”, mở liên kết nguồn và xem trace.
- Phòng thực nghiệm: chọn phân loại, bấm điền mẫu rồi chạy MLP; giải thích nhãn tổng hợp.
- Chọn hồi quy, bấm điền mẫu rồi chạy; giải thích điểm tiến triển, không phải % mắc bệnh.
- Đồ thị: chọn tài liệu a1c, đối chiếu hai quan hệ và mã nguồn.
- Neo4j Browser chạy:
  MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) RETURN a,r,b LIMIT 100;
- Trình bày ma trận nhầm lẫn: lớp Low hiếm, recall thấp; Ridge tốt hơn MLP ở hồi quy.
- Nêu RL là chính sách điều phối mô phỏng một bước, không tối ưu điều trị.

4. BÁO CÁO VÀ TÁI LẬP
Hai PDF và mã LaTeX ở reports/.
- tieuluan_final_06_02_giangkt.254.pdf: tiểu luận độc lập, 7 chương nền tảng và thực nghiệm; không ghép project.
- project01_06_02_giangkt.254.pdf: kiến trúc, mô hình, KB, agent, kiểm thử và demo.
Chạy scripts/assemble_reports.py để ghép nguồn; biên dịch từng tệp chính bằng XeLaTeX hoặc Tectonic, từ reports/.
Dùng Times New Roman và Consolas; máy build cần có hai font này.
Ảnh demo là chụp sản phẩm thật. Biểu đồ mới được tính từ CSV predictions.

Huấn luyện lại:
- Tải ZIP Diabetes Risk Prediction 50K từ trang Kaggle trong DATASET_ATTRIBUTION.txt,
  lưu data/raw/diabetes.zip (raw không đẩy Git); sau đó chạy scripts/train_models.py.
- scripts/train_policy.py: học Q-table điều phối.
- scripts/build_figures.py: vẽ biểu đồ từ kết quả thật.
- scripts/test_scenarios.py: tám kịch bản API, cần Neo4j đang chạy.
  Trong PowerShell đặt $env:PYTHONPATH=(Get-Location).Path trước khi chạy.
- legacy_tieuluan/ lưu notebook, mã và dữ liệu kết quả kế thừa của tiểu luận 02/03.
  Môi trường của phần cũ được ghi riêng; không nhận là đã chạy lại toàn bộ trong lần build project.

5. PHẠM VI ĐÃ LÀM
FastAPI + web, hai MLP có checkpoint, TF-IDF retrieval, Neo4j thật,
MessageBus định tuyến handler của các agent, Q-table mô phỏng và luật thiếu bằng chứng.
Câu trả lời tổng hợp trích đoạn xác định, không gọi LLM. Chưa có bộ nhớ hội thoại lâu dài,
chưa có hội đồng tranh biện. Thực nghiệm GCN Cora nằm riêng trong tiểu luận, chưa tích hợp vào chatbot. Dữ liệu phân loại là tổng hợp.
Không dùng đầu ra demo làm chẩn đoán hoặc quyết định điều trị.
Không công khai cổng Neo4j, .env hoặc dữ liệu người dùng.

CẬP NHẬT ĐỐI CHIẾU THAM KHẢO CT_03
- Nguồn dữ liệu và xử lý: reports/data_methodology.tex; kiểm kê: results/data_audit.json.
- Trang web: mục 04 · Dữ liệu & nguồn, có URL gốc và danh mục nguồn KB.
- Tái kiểm kê: python scripts/audit_data.py (cần ZIP dữ liệu gốc ở data/raw).
- Chỉ số dòng chia tập: results/classification_split.csv và regression_split.csv.
- Báo cáo bổ sung bản đồ dữ liệu kế thừa, danh mục hình/bảng, thuyết minh từng màn hình.

BẢN CHATBOT VÀ GIAO DIỆN MỚI
- Trợ lý kiến thức: HbA1c, xét nghiệm có đơn vị, ăn uống, vận động, theo dõi; hỏi tiếp theo chủ đề.
- Chat dùng KB + luật hội thoại, không gọi LLM. Lịch sử chỉ trong tab, gửi tối đa 12 thông điệp mỗi yêu cầu.
- Bằng chứng cạnh câu trả lời; mở trực tiếp quan hệ tài liệu trên Neo4j.
- Thực nghiệm dữ liệu: so sánh lần chạy trước và đưa kết quả sang chat. Không diễn giải thay đổi mô hình thành hiệu quả điều trị.
- Nguồn & tài liệu: tìm kiếm không dấu, xem đoạn nguồn và hỏi tiếp.
- Kiểm thử: python -m scripts.test_chatbot (20 kiểm tra), python -m scripts.test_scenarios (8 kịch bản).
- Hướng dẫn Neo4j: HUONG_DAN_NEO4J.md. Không phải cài lại trên máy đã thiết lập này.

TÁCH HAI BÁO CÁO
- Chương 6: GCN so với MLP trên Cora, 3 seed, mã scripts/train_cora.py; kết quả results/cora/.
- Chương 7: mô phỏng đa agent, kết quả AGENT02 lưu trong experiments/agent02/.
- Huấn luyện: cài requirements-training.txt. Chạy sản phẩm: requirements.txt.
- Kiểm tra demo công khai: python scripts/check_deployment.py.
