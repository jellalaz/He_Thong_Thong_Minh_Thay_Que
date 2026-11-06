# GlucoGuide - Hệ đa agent hỗ trợ tìm hiểu tiểu đường

Kiều Trường Giang, B23DCCN254, nhóm học phần 06, nhóm thực hiện 02.

## Chạy sản phẩm local

1. Khởi động Neo4j bằng start-neo4j.ps1 nếu dịch vụ chưa chạy.
2. Chạy START_CHATBOT_LOCAL.cmd hoặc run-chatbot-local.ps1.
3. Mở http://localhost:8765 và http://localhost:7474/browser/.

Xem đồ thị ngay trên http://localhost:8765/#graph: nút **Xem toàn bộ đồ thị** nằm cạnh bộ lọc chủ đề. Có thể phóng to, kéo và bấm khái niệm để đọc quan hệ, không cần dán lệnh hoặc đăng nhập Neo4j Browser riêng.

Web dùng FastAPI; Qwen3 4B Q4_K_M chạy bằng llama.cpp/Vulkan tại 127.0.0.1:11435; Neo4j local ở cổng 7687. Luồng hỏi đáp không gọi dịch vụ xử lý bên ngoài, không tự tải tài nguyên. Tệp cấu hình và khóa nội bộ nằm ngoài Git.

## Dữ liệu và các thành phần

- Phân loại: Diabetes Risk Prediction 50K, 40.000 dòng train và 10.000 dòng test; MLP học nhãn tổng hợp High/Moderate/Low.
- Hồi quy: diabetes/scikit-learn, 353 mẫu train và 89 mẫu test; dự đoán điểm tiến triển nghiên cứu.
- Tri thức: knowledge.json, knowledge_dialogue.json và knowledge_curated.json trong data/, tổng 58 đoạn từ 22 nguồn được tham chiếu.
- Đồ thị local: 169 khái niệm, 106 quan hệ, phủ đủ 58 tài liệu. Mỗi quan hệ lưu mã tài liệu, trích đoạn và URL nguồn.
- Hội thoại: định tuyến, truy xuất TF-IDF từ/ký tự, Qwen local và kiểm tra phản hồi. Trọng số 4B dùng nguyên bản; các thí nghiệm LoRA 1.7B được giữ riêng.
- Agent đồ thị: truy vấn Neo4j theo mã tài liệu qua MessageBus, đối chiếu bộ ba/trích đoạn/URL và cấp các quan hệ hợp lệ vào ngữ cảnh Qwen. Không tự sinh Cypher từ câu hỏi và không tự thêm quan hệ vào cơ sở dữ liệu.
- An toàn: phân loại trước RAG, không chờ đồ thị hoặc mô hình khi cần hành động ưu tiên.
- Phản hồi: bảng Q học ba cách trình bày theo chủ đề; không học liều thuốc hoặc điều trị.

## Nạp lại đồ thị và kiểm thử

Từ thư mục project, dùng Python của .venv:

    python scripts/ingest_graph.py
    python -m scripts.test_graph_coverage
    python -m scripts.test_safety_offline
    python -m scripts.test_local_feedback
    python -m scripts.test_knowledge_agents

Kiểm thử an toàn chặn DNS/kết nối ngoài; kết nối loopback được giữ cho các thành phần nội bộ. Kết quả nằm trong results/. Script evaluate_chat_local.py cần web cùng mô hình local đang chạy và lưu phản hồi để đọc lại.

Kiểm thử giao diện: `node scripts/test_graph_view.cjs`, cần Playwright và Edge đã có sẵn. Script không tải trình duyệt; chặn trang truy cập máy chủ ngoài và kiểm tra đủ 58 bộ lọc cùng các thao tác trên desktop/điện thoại. Ảnh desktop được lưu trực tiếp tại reports/demo-graph-current.png để báo cáo và kiểm thử dùng chung một bản.

## Bộ nộp KB, KG và RAG

[Bộ tệp đã xuất](exports/diabetes/) và [ZIP để nộp](exports/glucoguide_kb_kg_rag.zip) có KB JSON; KG dạng CSV, JSON và Cypher; chỉ mục RAG đã fit; cấu hình; 22 câu hỏi và kết quả; ví dụ chạy local cùng trace; code chạy lại và manifest SHA-256. Bộ nộp không chứa mật khẩu hoặc trọng số Qwen.

Xuất lại từ Neo4j và web local đang chạy:

    python -m scripts.export_knowledge --live-examples
    python -m scripts.test_knowledge_export

Để truy vấn bằng tệp, không cần web, Neo4j đang chạy hoặc Internet:

    python scripts/query_knowledge_export.py exports/diabetes --question "HbA1c là gì?"

Chế độ này trả văn bản và quan hệ từ bản chụp, có nhãn `exported-snapshot`; không chạy Qwen. Hướng dẫn chạy độc lập từ code đóng gói, nạp lại đồ thị và các giới hạn nằm trong [README của bộ nộp](exports/diabetes/README.md). Chỉ mở chỉ mục joblib từ bộ nộp tin cậy.

Tập truy xuất có 20 câu cần tìm tài liệu và 2 câu cần từ chối: Hit@1 85%, Hit@4 100%, MRR@4 0,917. Đây là tập chức năng tự biên soạn, không phải độ chính xác tư vấn hoặc chẩn đoán. Agent KG hiện lấy cạnh theo tài liệu, chưa có tìm đường nhiều bước hoặc thuật toán cộng đồng Microsoft GraphRAG.

## Hai báo cáo

Hai PDF và mã LaTeX được giữ riêng trong reports/:

- tieuluan_final_06_02_giangkt.254: nền tảng và các thực nghiệm học phần.
- project01_06_02_giangkt.254: kiến trúc sản phẩm, dữ liệu, mô hình, đồ thị, hội thoại và kiểm thử.

Dùng scripts/assemble_reports.py để ghép nguồn; biên dịch từng tệp chính từ reports/ bằng Tectonic hoặc XeLaTeX. Font cần có: Times New Roman và Consolas. Các hình demo là ảnh chụp ứng dụng; số liệu mô hình được giữ trong results/.

## Cấu trúc thư mục

app/: backend; web/: giao diện; data/: KB và ví dụ; models/: checkpoint; scripts/: xử lý và kiểm thử; results/: bằng chứng thực nghiệm; experiments/: thí nghiệm bổ sung; legacy_tieuluan/: tài liệu thực nghiệm kế thừa; reports/: hai báo cáo.

.runtime/ chứa bộ chạy local và dữ liệu Neo4j; .local-models/ chứa trọng số; .local-training/ chứa checkpoint và bảng Q trên máy. Những thư mục này được bỏ qua khi đưa lên Git, nhưng một số tệp cần để vận hành trên máy hiện tại.

`scripts/clean_generated.ps1` mặc định chỉ liệt kê tệp có thể dọn; thêm `-Apply` để xóa danh sách đã kiểm tra. Script giữ tài nguyên đang chạy, kiểm tra đường dẫn và ghi lịch sử tại results/cleanup_manifest.json. Không xóa models/, experiments/ hoặc legacy_tieuluan/: các thư mục này chứa checkpoint và bằng chứng thực nghiệm được báo cáo sử dụng.

Bản Vercel/Aura là triển khai trước đây, không chạy Qwen4B. Các số liệu và ảnh của bản hoàn thiện được kiểm tra trên local. Dữ liệu tổng hợp, tập hội thoại tự biên soạn và kiểm thử chức năng chưa thay thế đánh giá chuyên môn y tế.

## Nguồn web/PDF và hỗ trợ sau mô hình

12 đoạn bổ sung được dựng từ web NIDDK, hai bài Vinmec và PDF NIDDK Guiding Principles. PDF nguồn và văn bản web NIDDK lưu tại data/source_documents/; Vinmec chỉ lưu trích dẫn ngắn cùng URL và mã băm. data/source_curation.json ghi nội dung biên soạn và vị trí đối chiếu; chạy `python scripts/build_sourced_kb.py` để kiểm tra và dựng lại hoàn toàn offline. PDF là tài liệu lưu trữ: chỉ dùng các nguyên tắc tự chăm sóc đã chọn, không lấy ngưỡng chẩn đoán hoặc liều điều trị từ đó. Thu thập nguồn ban đầu có truy cập web theo yêu cầu; lúc hỏi đáp không tự tải nguồn hoặc gửi dữ liệu người dùng ra ngoài.

Nguồn Vimec Accessibility là thiết bị nâng, còn vimec.net.vn là công ty thiết bị y tế; các trang đã kiểm tra không được đưa vào KB tư vấn bệnh. Vinmec là nguồn y khoa tiếng Việt đã được người dùng xác nhận.

Sau khi chạy phân loại/hồi quy, bấm **Nhận xét và hỗ trợ**. Agent Nhận xét mô hình giải thích phạm vi; agent Hỗ trợ người dùng trả ba mục có nguồn: ăn uống, theo dõi và chuẩn bị đi khám. Những mục này là gợi ý chung, không được cá nhân hóa bằng nhãn tổng hợp. Mẫu được chuyển sang các lượt chat tiếp theo khi người dùng bấm nút; có thể bấm Bỏ ngữ cảnh mẫu hoặc Cuộc trò chuyện mới để xóa. Backend tự tính lại kết quả từ trường đầu vào, không nhận kết luận chẩn đoán do trình duyệt gửi.

Kiểm thử mới: `python -m scripts.test_sources_support` và `node scripts/test_support_view.cjs`. Tập 8 truy vấn kiểm tra nguồn PDF/Vinmec nằm trong data/rag_source_evaluation.json; kết quả được lưu riêng với tập 22 truy vấn hồi quy. Để xem PDF offline trên web, tìm PDF trong Dữ liệu & tài liệu, bấm Đọc tài liệu gốc; liên kết đi tới /api/source/{id} kèm số trang.
