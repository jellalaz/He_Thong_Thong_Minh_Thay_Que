# Bộ nộp KB, KG và RAG tiểu đường

Thư mục này chứa dữ liệu và code có thể kiểm tra, không chỉ ảnh demo. KB gồm 46 đoạn từ 19 nguồn; KG được đọc và đối chiếu trực tiếp từ Neo4j local, có 143 khái niệm và 86 quan hệ.

## Các tệp

- kb/knowledge.json: nội dung, từ khóa, mã tài liệu, nguồn và bộ ba.
- kg/nodes.csv, kg/relationships.csv: nút và cạnh UTF-8, có mã tài liệu, trích đoạn và URL.
- kg/graph.json, kg/import.cypher: bản chụp đồ thị và lệnh MERGE để nạp lại.
- rag/index.joblib, rag/settings.json: chỉ mục TF-IDF đã fit và cấu hình đầy đủ.
- rag/queries.json, rag/evaluation.json: câu hỏi, tài liệu kỳ vọng, kết quả từng câu và chỉ số truy xuất.
- examples/agent_runs.json: phản hồi và trace từ ứng dụng local nếu xuất với --live-examples.
- code/: các module điều phối, truy xuất, agent đồ thị, luật, prompt và script chạy lại.
- manifest.json: số lượng và SHA-256 của từng tệp. Không có mật khẩu, API key, hồ sơ bệnh nhân hoặc trọng số Qwen trong bộ nộp.

## Truy vấn bộ nộp hoàn toàn offline

Từ thư mục này, dùng Python đã có các thư viện theo requirements.txt:

    python code/scripts/query_knowledge_export.py . --question "HbA1c là gì?"

Lệnh kiểm tra checksum, đọc chỉ mục đã lưu, chạy các agent qua MessageBus và trả văn bản cùng quan hệ của bản chụp. Chế độ này không chạy Qwen, không giả lập kết nối Neo4j và không gọi Internet. Chỉ nạp index.joblib từ bộ nộp tin cậy; checksum kiểm tra tính toàn vẹn, không xác thực người phát hành.

## Nạp lại Neo4j local

    python code/scripts/restore_knowledge_export.py .

Script hỏi mật khẩu hoặc đọc NEO4J_PASSWORD từ môi trường. MERGE không xóa dữ liệu khác. Có thể dùng kg/import.cypher để kiểm tra bằng công cụ Neo4j. Không dùng địa chỉ máy chủ ngoài.

## Chạy sản phẩm đầy đủ

Mã nguồn gốc: https://github.com/jellalaz/He_Thong_Thong_Minh_Thay_Que

Trên máy đã có Qwen3 4B và Neo4j, chạy START_CHATBOT_LOCAL.cmd trong project gốc rồi mở http://localhost:8765. Agent đồ thị lấy quan hệ theo tài liệu đã truy xuất; quan hệ phải khớp bộ ba, văn bản và nguồn trước khi cấp cho Qwen. Nhánh cấp cứu trả bằng luật trước RAG/KG.

Đồ thị còn 57 cụm rời nhau; chưa phải ontology y khoa đầy đủ hay Microsoft GraphRAG. Tập câu hỏi do project biên soạn, chưa thay thế đánh giá độc lập hoặc thẩm định lâm sàng. Kết quả truy xuất không phải độ chính xác chẩn đoán.
