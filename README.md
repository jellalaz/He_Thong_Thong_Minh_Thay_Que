# GlucoGuide - Hệ đa agent hỗ trợ tìm hiểu tiểu đường

Kiều Trường Giang, B23DCCN254, nhóm học phần 06, nhóm thực hiện 02.

## Phiên bản V2 và bộ nộp gọn

Mở http://localhost:8765/#v2 để chạy workflow mới và so sánh hai kiến trúc trên Pima/OpenML 37 và Early Stage/UCI 529. V2 có 6 tầng, 7 vai trò (Coordinator điều phối Data, Prediction, Rule, KG/RAG, Explanation, Monitoring), request ID, model version/hash và audit metadata tại `.runtime/audit-v2.jsonl`. Chat và các mô hình V1 gốc vẫn giữ nguyên.

V1 đối chứng có 3 tầng ẩn 64–32–16. V2 có 5 tầng ẩn 64–32–16–8–4 giữa đầu vào và đầu ra, tăng L2 và cân bằng trọng số lớp. Hai cấu hình dùng cùng cách chia trong từng dataset, 3 seed khởi tạo và chọn epoch bằng validation. Early Stage còn 251/520 mẫu sau khi loại trùng, Pima có 768 mẫu. Macro-F1 trung bình V1/V2 lần lượt là 0,837/0,903 trên Early Stage và 0,736/0,698 trên Pima. Kết quả và dự đoán nằm trong `results/v2/`, checkpoint trong `models/v2/`.

Tiểu luận Final V2 dùng toàn bộ bảy chương và phụ lục từ nguồn Final, rồi bổ sung bốn chương về dữ liệu, MLP năm tầng, tích hợp đa agent và kiểm chứng. Project 01 trình bày cách vận hành và demo.

| Tài liệu | V1 gốc | V2 |
| --- | --- | --- |
| Tiểu luận Final | [PDF](reports/tieuluan_final_06_02_giangkt.254.pdf) | [PDF](reports/v2/tieuluan_final_06_02_giangkt_v2.pdf) |
| Project 01 | [PDF](reports/project01_06_02_giangkt.254.pdf) | [PDF](reports/v2/project01_06_02_giangkt_v2.pdf) |

[Gợi ý ôn 51 câu](ON_VAN_DAP/goi_y_tra_loi_51_cau.pdf) để riêng trong thư mục ôn vấn đáp.

```bash
.venv/bin/python -m scripts.train_v2
.venv/bin/python -m scripts.test_v2
.venv/bin/python scripts/build_v2_reports.py
.venv/bin/python -m scripts.package_delivery
```

Hai nguồn nhỏ đã có trong `data/v2/sources/`, có thể train V2 offline. Tải lại nguồn và Tectonic bằng `scripts/setup_v2_assets.py` nếu cần. Biên dịch LaTeX cần Times New Roman/Courier New và Tectonic hoặc XeLaTeX. Tập tin `results/v2/report_quality.json` ghi QA của PDF hiện tại; đóng gói yêu cầu hash đúng bản đã rà render.

`BAN_GIAO_GLUCOGUIDE/` là bản sinh để nộp, chỉ có 5 tệp: hai PDF V2, `kb_diabet.cypher`, `code_data_kb_rag.zip`, `DOC_TRUOC.txt`. ZIP giữ code/data/checkpoint, KB/KG/RAG, kết quả và hai PDF V1 để đối chiếu. Không mang runtime, venv, mật khẩu hoặc trọng số Qwen. Các bộ nộp sinh trước được chuyển vào `.runtime/` để thư mục nộp không lẫn file cũ.

## Chạy trên macOS Apple Silicon

Đã khôi phục và kiểm tra trên MacBook Pro M3 Pro, macOS 27.0.1, Python 3.14.10 ngày 13/11/2026. Python chạy trong `.venv/` riêng của project, tạo từ Python Miniforge; không cài gói vào `base` hoặc môi trường `ai`. Neo4j, Node.js, Playwright và llama.cpp nằm trong `.runtime/`; Qwen nằm trong `.local-models/`. Các thư mục này được bỏ qua bởi Git.

Trên máy đã setup, chạy từ thư mục project:

```bash
bash run-macos.sh start
```

Mở http://localhost:8765. Lệnh tự bật Neo4j, nạp lại đồ thị bằng MERGE, bật Qwen3 4B Q4_K_M bằng **Metal trên GPU Apple**, rồi bật web. Không cần kích hoạt conda, Docker hoặc Homebrew. Các tiến trình chạy nền, tiếp tục hoạt động khi đóng Terminal; sau khi khởi động lại máy cần chạy lại lệnh. Có thể bấm đúp `START_CHATBOT_MAC.command` để bật và mở trang bằng trình duyệt mặc định.

```bash
bash run-macos.sh status
bash run-macos.sh stop
```

`stop` chỉ dừng các tiến trình được launcher này ghi nhận. Log nằm tại `.runtime/web.log`, `.runtime/qwen.log`, `.runtime/neo4j.log`. Neo4j Browser ở http://localhost:7474/browser/, user `neo4j`; mật khẩu tự tạo nằm trong `.env` local. Giao diện đồ thị trong web không yêu cầu nhập mật khẩu.

Setup lại trên một Mac Apple Silicon khác: cần Python 3.14 và Java 21 ARM64 đã cài; Edge cần có để chạy kiểm thử giao diện. Có thể kích hoạt môi trường Miniforge mong muốn trước khi tạo `.venv`:

```bash
conda activate ai
bash setup-macos.sh
bash run-macos.sh start
.venv/bin/python scripts/verify_macos.py
```

Installer dùng phiên bản đã kiểm tra trong `requirements-macos-lock.txt`, tải Qwen khoảng 2,5 GB và runtime chính thức, kiểm tra checksum, tạo `.env` cùng khóa API local. Chỉ giai đoạn setup cần Internet; launcher không tải tài nguyên. Không dùng lock CUDA của Windows để cài trên Mac. Không cần PyTorch/LoRA 1.7B cho luồng sản phẩm Qwen4B hiện tại.

`results/macos_setup_checks.json` ghi kiểm thử trên máy mới. Chi tiết và ảnh giao diện được giữ tại `.runtime/macos-verification/`, tách khỏi bằng chứng thực nghiệm Windows cũ. Có thể chạy lại một nhóm, ví dụ `.venv/bin/python scripts/verify_macos.py --only graph_ui`.

**Dữ liệu để train lại:** các checkpoint sản phẩm, KB/PDF, bộ nộp và kết quả đã có đầy đủ trong Git. Hai tệp Cora gốc đã khôi phục và khớp SHA-256 cũ trong `data/raw/cora/`. Tệp `data/raw/diabetes.zip` chưa có: endpoint Kaggle cũ trả HTTP 404 khi setup máy mới. Điều này không ảnh hưởng inference, chatbot, KG hoặc bộ nộp; `scripts/train_models.py` và `scripts/audit_data.py` cần tệp ZIP gốc. Có thể chép lại từ máy Windows hoặc thử `.venv/bin/python scripts/setup_macos.py --data-only` khi nguồn tải hoạt động lại. Installer đối chiếu SHA-256 đã ghi trong `results/data_audit.json`, không thay bằng một dataset khác. Các thí nghiệm LoRA và notebook legacy chưa được huấn luyện lại trên Mac.

## Chạy sản phẩm local trên Windows

1. Khởi động Neo4j bằng start-neo4j.ps1 nếu dịch vụ chưa chạy.
2. Chạy START_CHATBOT_LOCAL.cmd hoặc run-chatbot-local.ps1.
3. Mở http://localhost:8765 và http://localhost:7474/browser/.

Xem đồ thị ngay trên http://localhost:8765/#graph: nút **Xem toàn bộ đồ thị** nằm cạnh bộ lọc chủ đề. Có thể phóng to, kéo và bấm khái niệm để đọc quan hệ, không cần dán lệnh hoặc đăng nhập Neo4j Browser riêng.

Web dùng FastAPI; Qwen3 4B Q4_K_M chạy bằng llama.cpp tại 127.0.0.1:11435 (Vulkan trên Windows, Metal trên Mac); Neo4j local ở cổng 7687. Luồng hỏi đáp không gọi dịch vụ xử lý bên ngoài, không tự tải tài nguyên. Tệp cấu hình và khóa nội bộ nằm ngoài Git.

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

## Demo trên Vercel

[Mở demo GlucoGuide](https://glucoguide-giang254.vercel.app/#v2) để so sánh mô hình V1 và V2. Web chạy FastAPI và các checkpoint MLP đã huấn luyện. Chat trả lời bằng KB và luật có nguồn. Nếu Aura không kết nối, giao diện và agent KG đọc bản chụp tại `exports/diabetes/kg/graph.json` và ghi rõ nguồn lưu trữ. Bản chạy Mac dùng Qwen 4B, Neo4j trực tiếp và lưu audit metadata. Kết quả thực nghiệm phục vụ học phần và cần được đọc trong phạm vi nghiên cứu của từng dataset.

## Nguồn web/PDF và hỗ trợ sau mô hình

12 đoạn bổ sung được dựng từ web NIDDK, hai bài Vinmec và PDF NIDDK Guiding Principles. PDF nguồn và văn bản web NIDDK lưu tại data/source_documents/; Vinmec chỉ lưu trích dẫn ngắn cùng URL và mã băm. data/source_curation.json ghi nội dung biên soạn và vị trí đối chiếu; chạy `python scripts/build_sourced_kb.py` để kiểm tra và dựng lại hoàn toàn offline. PDF là tài liệu lưu trữ: chỉ dùng các nguyên tắc tự chăm sóc đã chọn, không lấy ngưỡng chẩn đoán hoặc liều điều trị từ đó. Thu thập nguồn ban đầu có truy cập web theo yêu cầu; lúc hỏi đáp không tự tải nguồn hoặc gửi dữ liệu người dùng ra ngoài.

Nguồn Vimec Accessibility là thiết bị nâng, còn vimec.net.vn là công ty thiết bị y tế; các trang đã kiểm tra không được đưa vào KB tư vấn bệnh. Vinmec là nguồn y khoa tiếng Việt đã được người dùng xác nhận.

Sau khi chạy phân loại/hồi quy, bấm **Nhận xét và hỗ trợ**. Agent Nhận xét mô hình giải thích phạm vi; agent Hỗ trợ người dùng trả ba mục có nguồn: ăn uống, theo dõi và chuẩn bị đi khám. Những mục này là gợi ý chung, không được cá nhân hóa bằng nhãn tổng hợp. Mẫu được chuyển sang các lượt chat tiếp theo khi người dùng bấm nút; có thể bấm Bỏ ngữ cảnh mẫu hoặc Cuộc trò chuyện mới để xóa. Backend tự tính lại kết quả từ trường đầu vào, không nhận kết luận chẩn đoán do trình duyệt gửi.

Kiểm thử mới: `python -m scripts.test_sources_support` và `node scripts/test_support_view.cjs`. Tập 8 truy vấn kiểm tra nguồn PDF/Vinmec nằm trong data/rag_source_evaluation.json; kết quả được lưu riêng với tập 22 truy vấn hồi quy. Để xem PDF offline trên web, tìm PDF trong Dữ liệu & tài liệu, bấm Đọc tài liệu gốc; liên kết đi tới /api/source/{id} kèm số trang.
