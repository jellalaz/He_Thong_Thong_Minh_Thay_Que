GLUCOGUIDE — TIỂU LUẬN FINAL VÀ PROJECT 01
Kiều Trường Giang · B23DCCN254 · Nhóm 06–02

1. MỞ SẢN PHẨM TRÊN MÁY NÀY
- Web: http://localhost:8765
- Neo4j Browser: http://localhost:7474/browser/
- Địa chỉ kết nối Neo4j: neo4j://127.0.0.1:7687; tài khoản neo4j.
- Mật khẩu nằm trong tệp .env trên máy, dòng NEO4J_PASSWORD. Tệp này không đưa lên GitHub.
- Browser đã được đăng nhập và mở truy vấn đồ thị ở phiên hoàn thiện.
- Demo công khai tạm thời: https://bear-parental-pair-mercury.trycloudflare.com
  Link chỉ hoạt động khi máy và tiến trình tunnel còn chạy. Không phải hosting cố định.

2. CHẠY LẠI
Mở PowerShell trong thư mục này:
  .\start-neo4j.ps1
  .\run.ps1
Để chạy trên máy khác, cài Python 3.12, tạo venv, cài requirements.txt.
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
- tieuluan_final_06_02_giangkt.254.pdf: tổng hợp nền tảng + project.
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
chưa có hội đồng tranh biện, chưa huấn luyện GNN. Dữ liệu phân loại là tổng hợp.
Không dùng đầu ra demo làm chẩn đoán hoặc quyết định điều trị.
Không công khai cổng Neo4j, .env hoặc dữ liệu người dùng.
