# Huấn luyện nhận diện ý định chatbot

Chạy `python scripts/train_intent.py`, sau đó `python -m scripts.test_intent` và `python -m scripts.test_chatbot`.

Dữ liệu gồm `data/intent_examples.json` và `data/intent_expansion.json`: tổng 112 câu train, 32 câu test và 8 nhãn. Đây là dữ liệu phát triển tự biên soạn, không phải hồ sơ bệnh nhân hoặc bộ đánh giá độc lập của chuyên gia. TF-IDF ký tự 2–5 gram và Logistic Regression học từ train. Accuracy nội bộ là 93,75%, macro-F1 là 0,937; kết quả từng câu nằm trong `results/intent_evaluation.json`.

Checkpoint: `models/chat_intent.joblib`. Chỉ số và dự đoán từng câu: `results/intent_evaluation.json`. Tập test nhỏ nên kết quả cao không chứng minh chất lượng hội thoại rộng hoặc độ an toàn y khoa.

Khi luật không xác định được chủ đề, mô hình đề xuất ý định. Ngưỡng xác suất 0.42, chênh lệch hai lớp 0.15 và tương đồng 0.25 giúp từ chối câu thiếu bằng chứng; các ngưỡng là lựa chọn kỹ thuật ban đầu, chưa hiệu chuẩn trên tập validation độc lập. Lớp ngoài phạm vi luôn bị từ chối. Nội dung trả lời vẫn lấy từ KB và luật; điểm ý định không phải xác suất mắc bệnh. Các luật về đơn vị, thuốc và khẩn cấp vẫn áp dụng sau định tuyến.

## Nhánh Qwen chạy local

Sản phẩm hiện dùng Qwen3 4B Q4_K_M cùng RAG trên máy, khởi động bằng `START_CHATBOT_LOCAL.cmd` và mở http://localhost:8765. Trọng số 4B không được tinh chỉnh lại. Hai lượt LoRA 1.7B được giữ làm thực nghiệm trong `experiments/local_qwen/` và `results/local_qwen*`. Bộ phân loại an toàn chạy trước định tuyến; kiểm thử nội bộ bằng `python -m scripts.test_safety_offline`.
