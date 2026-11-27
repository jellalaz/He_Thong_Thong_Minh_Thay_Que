# GlucoGuide - Hệ đa agent hỗ trợ tìm hiểu tiểu đường

Kiều Trường Giang, B23DCCN254, nhóm học phần 06, nhóm thực hiện 02.

## Project 01 V3 · hình minh họa và demo

[Báo cáo Project 01 V3](reports/project01_06_02_giangkt_v3.pdf) trình bày học tăng cường và demo phiếu đánh giá trong chương **Triển khai và trình diễn V3**. Chương **Đối chiếu mô hình với mã nguồn** chỉ tới từng tệp và dòng code. Khởi động trên Mac bằng `bash run-macos.sh start`.

- [Minh chứng mô hình](http://localhost:8765/#minhchung) hiển thị ROC và Precision–Recall của hai mạng ở seed 254. Chọn Pima hoặc Early Stage rồi kéo ngưỡng để đếm lại ma trận trên tập test. [Hàm evaluate_dataset](scripts/build_study_evidence.py) lấy dữ liệu từ CSV, [confusionAt và rankingChart](web/study-evidence.js) tính ma trận và vẽ trên web.
- [Đồ thị tri thức](http://localhost:8765/#graph) có nút **Cụm lớn nhất**. Bấm vào nút khái niệm để xem quan hệ có hướng, mở **Danh sách quan hệ** để xem mã tài liệu. [selectGraphEdges](web/app.js) dùng [layout](web/graph-layout.js) để xác định thành phần liên thông.
- Dựng lại dữ liệu web bằng `.venv/bin/python scripts/build_study_evidence.py`. Khi dịch vụ đang chạy, kiểm thử hai dataset, ba ngưỡng và chuyển bộ lọc bằng `NODE_PATH=.runtime/ui-tests/node_modules .runtime/node/bin/node scripts/test_study_evidence_view.cjs`.

## Demo và báo cáo V3

Mở [Sàng lọc tiểu đường · V3](https://glucoguide-giang254.vercel.app/#v3) hoặc chạy `bash run-macos.sh start` để xem trên Mac.

- **Sàng lọc trên Pima.** Nhập glucose sau 2 giờ, BMI, tuổi và các chỉ số còn lại để phân loại nhãn dương/âm. API `POST /api/v2/screening-predict` dùng một checkpoint CNN 1D đã chọn trên validation (Macro-F1 trung bình 0,775), `models/v3/pima_cnn_seed255.npz`. Dữ liệu nghiên cứu gồm phụ nữ Pima từ 21 tuổi.
- **[Phân loại type](https://glucoguide-giang254.vercel.app/#type) cho mẫu đã được chẩn đoán.** So sánh tám biến trên NHIS, Macro-F1 validation trung bình là MLP (0,635), Transformer (0,630) và CNN 1D (0,616). MLP đạt Macro-F1 test 0,641 ở ngưỡng 0,5.
- **Luồng agent.** `POST /api/v2/type-predict` chuyển qua Data, Prediction và Rule. `app/type_study.py` nạp tệp `models/v3/nhis_type1_vs_type2_8f_mlp_seed255.npz`.
- **Minh chứng.** [Notebook](notebooks/tieuluan_final_06_02_giangkt_v3.ipynb) mở đầu bằng so sánh các mô hình trên Pima và Early Stage, sau đó trình bày bài toán phân loại type trên NHIS. Tab V2 tái hiện demo trước đó.
- **Báo cáo.** [Project 01 V3](reports/project01_06_02_giangkt_v3.pdf) và [Tiểu luận Final V3](reports/tieuluan_final_06_02_giangkt_v3.pdf).


## Phiên bản V2 và bộ nộp gọn

Mở http://localhost:8765/#v2 để chạy workflow mới và so sánh hai kiến trúc trên Pima/OpenML 37 và Early Stage/UCI 529. V2 có 6 tầng, 7 vai trò (Coordinator điều phối Data, Prediction, Rule, KG/RAG, Explanation, Monitoring), request ID, model version/hash và audit metadata tại `.runtime/audit-v2.jsonl`. Chat và các mô hình V1 gốc vẫn giữ nguyên.

V1 đối chứng có 3 tầng ẩn 64–32–16. V2 có 5 tầng ẩn 64–32–16–8–4 giữa đầu vào và đầu ra, tăng L2 và cân bằng trọng số lớp. Hai cấu hình dùng cùng cách chia trong từng dataset, 3 seed khởi tạo và chọn epoch bằng validation. Early Stage còn 251/520 mẫu sau khi loại trùng, Pima có 768 mẫu. Macro-F1 trung bình V1/V2 lần lượt là 0,837/0,903 trên Early Stage và 0,736/0,698 trên Pima. Kết quả và dự đoán nằm trong `results/v2/`, checkpoint trong `models/v2/`.

Tiểu luận Final V2 dùng toàn bộ bảy chương và phụ lục từ nguồn Final, rồi bổ sung bốn chương về dữ liệu, MLP năm tầng, tích hợp đa agent và kiểm chứng. Project 01 trình bày cách vận hành và demo.

| Tài liệu | V1 gốc | V2 |
| --- | --- | --- |
| Tiểu luận Final | [PDF](reports/tieuluan_final_06_02_giangkt.254.pdf) | [PDF](reports/tieuluan_final_06_02_giangkt_v2.pdf) |
| Project 01 | [PDF](reports/project01_06_02_giangkt.254.pdf) | [PDF](reports/project01_06_02_giangkt_v2.pdf) |

```bash
.venv/bin/python -m scripts.train_v2
.venv/bin/python -m scripts.test_v2
.venv/bin/python scripts/build_v2_reports.py
.venv/bin/python -m scripts.package_delivery
```

Hai nguồn nhỏ đã có trong `data/v2/sources/`, có thể train V2 offline. Tải lại nguồn và Tectonic bằng `scripts/setup_v2_assets.py` nếu cần. Biên dịch LaTeX cần Times New Roman/Courier New và Tectonic hoặc XeLaTeX. Tập tin `results/v2/report_quality.json` ghi QA của PDF hiện tại; đóng gói yêu cầu hash đúng bản đã rà render.

`BAN_GIAO_GLUCOGUIDE/` chứa hai PDF V2 và `DOC_TRUOC.txt`. Mở `KB_KG_RAG/` để xem trực tiếp cả 10 tệp KB, KG, RAG và Cypher. `MA_NGUON/` chứa project có thể mở trực tiếp, kèm dữ liệu, checkpoint, kết quả và hai PDF V1. Runtime, môi trường Python, mật khẩu và trọng số Qwen nằm ngoài bộ nộp.

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

Installer dùng [lock macOS](scripts/requirements/requirements-macos-lock.txt), tải Qwen khoảng 2,5 GB và runtime chính thức, kiểm tra checksum, tạo `.env` cùng khóa API local. Chỉ giai đoạn setup cần Internet. Luồng Qwen 4B dùng llama.cpp trên Mac.

`results/macos_setup_checks.json` ghi kiểm thử trên máy mới. Chi tiết và ảnh giao diện được giữ tại `.runtime/macos-verification/`, tách khỏi bằng chứng thực nghiệm Windows cũ. Có thể chạy lại một nhóm, ví dụ `.venv/bin/python scripts/verify_macos.py --only graph_ui`.

**Dữ liệu để train lại:** các checkpoint sản phẩm, KB/PDF, bộ nộp và kết quả đã có đầy đủ trong Git. Hai tệp Cora gốc đã khôi phục và khớp SHA-256 cũ trong `data/raw/cora/`. Tệp `data/raw/diabetes.zip` chưa có: endpoint Kaggle cũ trả HTTP 404 khi setup máy mới. Điều này không ảnh hưởng inference, chatbot, KG hoặc bộ nộp; `scripts/train_models.py` và `scripts/audit_data.py` cần tệp ZIP gốc. Có thể chép lại từ máy Windows hoặc thử `.venv/bin/python scripts/setup_macos.py --data-only` khi nguồn tải hoạt động lại. Installer đối chiếu SHA-256 đã ghi trong `results/data_audit.json`, không thay bằng một dataset khác. Các thí nghiệm LoRA và notebook legacy chưa được huấn luyện lại trên Mac.

## Chạy sản phẩm local trên Windows

1. Nếu Neo4j chưa chạy, mở PowerShell tại thư mục gốc và chạy `./scripts/windows/start-neo4j.ps1`. Với Docker, chạy `docker compose --project-directory . -f scripts/windows/compose.yaml up -d neo4j`.
2. Mở [START_CHATBOT_LOCAL.cmd](scripts/windows/START_CHATBOT_LOCAL.cmd) hoặc chạy `./scripts/windows/run-chatbot-local.ps1`.
3. Mở http://localhost:8765 và http://localhost:7474/browser/.

Các đường dẫn Windows trong PDF cũ theo bố cục tại các tag `v1` và `v2`. Các tệp cùng tên hiện nằm trong `scripts/windows/`.

Xem đồ thị ngay trên http://localhost:8765/#graph: nút **Xem toàn bộ đồ thị** nằm cạnh bộ lọc chủ đề. Có thể phóng to, kéo và bấm khái niệm để đọc quan hệ, không cần dán lệnh hoặc đăng nhập Neo4j Browser riêng.

Web dùng FastAPI; Qwen3 4B Q4_K_M chạy bằng llama.cpp tại 127.0.0.1:11435 (Vulkan trên Windows, Metal trên Mac); Neo4j local ở cổng 7687. Luồng hỏi đáp không gọi dịch vụ xử lý bên ngoài, không tự tải tài nguyên. Tệp cấu hình và khóa nội bộ nằm ngoài Git.

## Dữ liệu và các thành phần

[Thông tin nguồn dữ liệu](data/DATASET_ATTRIBUTION.txt), [hướng dẫn Neo4j](docs/HUONG_DAN_NEO4J.md) và [huấn luyện nhận diện ý định](docs/TRAINING_CHATBOT.md).

- Phân loại: Diabetes Risk Prediction 50K, 40.000 dòng train và 10.000 dòng test; MLP học nhãn tổng hợp High/Moderate/Low.
- Hồi quy: diabetes/scikit-learn, 353 mẫu train và 89 mẫu test; dự đoán điểm tiến triển nghiên cứu.
- Tri thức: `knowledge.json`, `knowledge_dialogue.json` và `knowledge_curated.json` trong `data/`, tổng 61 đoạn tham chiếu 25 nguồn duy nhất, gồm 24 link web và 1 PDF. Mục Tri thức trên web và `GET /api/knowledge` đọc bản đang chạy.
- Đồ thị local: 175 khái niệm, 109 quan hệ, phủ đủ 61 tài liệu. Bản xuất lưu trước đợt bổ sung có 169 khái niệm và 106 quan hệ. Mỗi quan hệ lưu mã tài liệu, trích đoạn và URL nguồn.
- Hội thoại: định tuyến, truy xuất TF-IDF từ/ký tự, Qwen local và kiểm tra phản hồi. Trọng số 4B dùng nguyên bản; các thí nghiệm LoRA 1.7B được giữ riêng.
- Agent đồ thị: truy vấn Neo4j theo mã tài liệu qua MessageBus, đối chiếu bộ ba/trích đoạn/URL và cấp các quan hệ hợp lệ vào ngữ cảnh Qwen. Không tự sinh Cypher từ câu hỏi và không tự thêm quan hệ vào cơ sở dữ liệu.
- An toàn: phân loại trước RAG, không chờ đồ thị hoặc mô hình khi cần hành động ưu tiên.
- Phản hồi: bảng Q học ba cách trình bày theo chủ đề; không học liều thuốc hoặc điều trị.

### Tệp mô hình đang dùng

| Tác vụ | Tệp |
|---|---|
| Phân loại nhãn tổng hợp trên dữ liệu 50K | `models/synthetic_diabetes_risk_mlp_classifier.joblib` |
| Hồi quy điểm tiến triển nghiên cứu | `models/diabetes_progression_mlp_regressor.joblib` |
| Phân loại mẫu Pima | `models/v2/pima_mlp_classifier_3_hidden_layers.joblib` và `models/v2/pima_mlp_classifier_5_hidden_layers.joblib` |
| Phân loại mẫu Early Stage | `models/v2/early_stage_mlp_classifier_3_hidden_layers.joblib` và `models/v2/early_stage_mlp_classifier_5_hidden_layers.joblib` |

Các lựa chọn V1 và V2 trên màn hình đối chiếu tương ứng với mạng 3 và 5 tầng ẩn. Hồi quy logistic và Ridge vẫn có số liệu đối chứng trong `results/model_metrics.json`.

## Nạp lại đồ thị và kiểm thử

Từ thư mục project, dùng Python của .venv:

    python scripts/ingest_graph.py
    python -m scripts.test_graph_coverage
    python -m scripts.test_safety_offline
    python -m scripts.test_local_feedback
    python -m scripts.test_knowledge_agents

Kiểm thử an toàn chặn DNS/kết nối ngoài; kết nối loopback được giữ cho các thành phần nội bộ. Kết quả nằm trong results/. Script evaluate_chat_local.py cần web cùng mô hình local đang chạy và lưu phản hồi để đọc lại.

Kiểm thử giao diện bằng `node scripts/test_graph_view.cjs` với Playwright và Edge. Script chặn truy cập máy chủ ngoài và kiểm tra các bộ lọc tài liệu cùng các thao tác trên desktop và điện thoại. Ảnh desktop được lưu tại `report_sources/demo-graph-current.png`.

## Bộ nộp KB, KG và RAG

Mở [KB_KG_RAG](exports/KB_KG_RAG/) để xem trực tiếp cả 10 tệp, gồm `kb_diabet.cypher`, KB JSON, đồ thị CSV/JSON và chỉ mục RAG. [Bộ chạy offline](exports/diabetes/) có thêm trace mẫu, tài liệu nguồn, mã truy vấn và manifest SHA-256. Lệnh đóng gói đưa cùng 10 tệp vào `BAN_GIAO_GLUCOGUIDE/KB_KG_RAG/`.

Xuất lại từ Neo4j và web local đang chạy:

    python -m scripts.export_knowledge --live-examples
    python -m scripts.test_knowledge_export

Để truy vấn bằng tệp, không cần web, Neo4j đang chạy hoặc Internet:

    python scripts/query_knowledge_export.py exports/diabetes --question "HbA1c là gì?"

Chế độ này trả văn bản và quan hệ từ bản chụp, có nhãn `exported-snapshot`; không chạy Qwen. Hướng dẫn chạy độc lập từ code đóng gói, nạp lại đồ thị và các giới hạn nằm trong [README của bộ nộp](exports/diabetes/README.md). Chỉ mở chỉ mục joblib từ bộ nộp tin cậy.

Tập truy xuất có 20 câu cần tìm tài liệu và 2 câu cần từ chối: Hit@1 85%, Hit@4 100%, MRR@4 0,917. Đây là tập chức năng tự biên soạn, không phải độ chính xác tư vấn hoặc chẩn đoán. Agent KG hiện lấy cạnh theo tài liệu, chưa có tìm đường nhiều bước hoặc thuật toán cộng đồng Microsoft GraphRAG.

## Mã nguồn báo cáo

Thư mục [`reports/`](reports/) có hai báo cáo ở từng phiên bản V1, V2 và V3, cùng tài liệu ôn vấn đáp. Mã dựng báo cáo và hình minh họa nằm trong [`report_sources/`](report_sources/). Dùng `scripts/assemble_reports.py` để ghép nguồn V1, `scripts/build_v2_reports.py` để biên dịch V2 bằng Tectonic. Hai báo cáo V3 được biên dịch trực tiếp từ nguồn LaTeX trong `report_sources/v3/` với Times New Roman và Courier New. Từ thư mục gốc, chạy:

```bash
cd report_sources/v3
tectonic --outdir ../../reports project01_06_02_giangkt_v3.tex
tectonic --outdir ../../reports tieuluan_final_06_02_giangkt_v3.tex
```


## Cấu trúc thư mục

`app/` chứa backend, `web/` chứa giao diện, `data/` chứa KB và ví dụ, `models/` chứa checkpoint, `scripts/` chứa mã xử lý và kiểm thử. Kết quả thực nghiệm nằm trong `results/`, `experiments/` và `legacy_tieuluan/`.

.runtime/ chứa bộ chạy local và dữ liệu Neo4j; .local-models/ chứa trọng số; .local-training/ chứa checkpoint và bảng Q trên máy. Những thư mục này được bỏ qua khi đưa lên Git, nhưng một số tệp cần để vận hành trên máy hiện tại.

`scripts/clean_generated.ps1` mặc định chỉ liệt kê tệp có thể dọn; thêm `-Apply` để xóa danh sách đã kiểm tra. Script giữ tài nguyên đang chạy, kiểm tra đường dẫn và ghi lịch sử tại results/cleanup_manifest.json. Không xóa models/, experiments/ hoặc legacy_tieuluan/: các thư mục này chứa checkpoint và bằng chứng thực nghiệm được báo cáo sử dụng.

## Demo trên Vercel

[Mở demo GlucoGuide V3](https://glucoguide-giang254.vercel.app/#v3) để chạy CNN 1D và xem nhãn dương/âm của mẫu Pima. Chat trả lời bằng KB và luật có nguồn. Nếu Aura không kết nối, giao diện và agent KG đọc bản chụp tại `data/knowledge_graph_snapshot.json`. Bản chạy Mac dùng Qwen 4B, Neo4j trực tiếp và lưu audit metadata.

## Nguồn web/PDF và hỗ trợ sau mô hình

14 đoạn bổ sung được dựng từ web NIDDK, hai bài Vinmec, hai bài Nhà thuốc FPT Long Châu và PDF NIDDK Guiding Principles. PDF nguồn và văn bản web NIDDK lưu tại data/source_documents/; Vinmec và Long Châu chỉ lưu trích dẫn ngắn cùng URL và mã băm tệp đã lưu. data/source_curation.json ghi nội dung biên soạn và vị trí đối chiếu; chạy `python scripts/build_sourced_kb.py` để kiểm tra và dựng lại hoàn toàn offline. PDF là tài liệu lưu trữ: chỉ dùng các nguyên tắc tự chăm sóc đã chọn, không lấy ngưỡng chẩn đoán hoặc liều điều trị từ đó. Thu thập nguồn ban đầu có truy cập web theo yêu cầu; lúc hỏi đáp không tự tải nguồn hoặc gửi dữ liệu người dùng ra ngoài.

Nguồn Vimec Accessibility là thiết bị nâng, còn vimec.net.vn là công ty thiết bị y tế; các trang đã kiểm tra không được đưa vào KB tư vấn bệnh. Vinmec là nguồn y khoa tiếng Việt đã được người dùng xác nhận.

Sau khi chạy phân loại/hồi quy, bấm **Nhận xét và hỗ trợ**. Agent Nhận xét mô hình giải thích phạm vi; agent Hỗ trợ người dùng trả ba mục có nguồn: ăn uống, theo dõi và chuẩn bị đi khám. Những mục này là gợi ý chung, không được cá nhân hóa bằng nhãn tổng hợp. Mẫu được chuyển sang các lượt chat tiếp theo khi người dùng bấm nút; có thể bấm Bỏ ngữ cảnh mẫu hoặc Cuộc trò chuyện mới để xóa. Backend tự tính lại kết quả từ trường đầu vào, không nhận kết luận chẩn đoán do trình duyệt gửi.

Kiểm thử mới: `python -m scripts.test_sources_support` và `node scripts/test_support_view.cjs`. Tập 8 truy vấn kiểm tra nguồn PDF/Vinmec nằm trong data/rag_source_evaluation.json; kết quả được lưu riêng với tập 22 truy vấn hồi quy. Để xem PDF offline trên web, tìm PDF trong Dữ liệu & tài liệu, bấm Đọc tài liệu gốc; liên kết đi tới /api/source/{id} kèm số trang.

### Phân loại type 1 và type 2 (NHIS)

Mở [Phân loại type](http://localhost:8765/#type), chọn mẫu giả định rồi bấm **Chạy phân loại**. API `POST /api/v2/type-predict` nạp checkpoint MLP đã chọn qua validation và trả `type_1`, `type_2` hoặc `undetermined`. Demo dành cho mẫu nghiên cứu là người lớn đã được chẩn đoán ngoài thai kỳ.

Bộ khảo sát NHIS công khai lưu theo ba tệp ZIP chứa CSV trong `data/raw/nhis/`. Tải từ CDC cho [2022](https://www.cdc.gov/nchs/nhis/documentation/2022-nhis.html), [2023](https://www.cdc.gov/nchs/nhis/documentation/2023-nhis.html) và [2024](https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html), theo thứ tự train/validation/test. Chạy lại với `.venv/bin/python -m scripts.compare_diabetes_types data/raw/nhis`. Mã băm dữ liệu, số mẫu theo nhãn và kết quả có trong `results/v3/diabetes_types.json`. Nhãn là loại bệnh người tham gia thuật lại. Tám trường gồm tuổi hiện tại, tuổi lúc được chẩn đoán, nhóm BMI, giới tính, tiền sử tăng huyết áp, tiền sử cholesterol cao, từng hút ít nhất 100 điếu thuốc lá và sức khỏe tự đánh giá. Ba biến đầu là bắt buộc, năm biến sau có thể để trống. Macro-F1 test 2024 là 0,641 với tám biến và 0,644 với ba biến tại ngưỡng 0,5. Demo dùng hai ngưỡng 0,37 và 0,9, có nhãn cho 74,1% mẫu test.
