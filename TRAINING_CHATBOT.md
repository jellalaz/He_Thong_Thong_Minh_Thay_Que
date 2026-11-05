# Huấn luyện nhận diện ý định chatbot

Chạy `python scripts/train_intent.py`, sau đó `python -m scripts.test_intent` và `python -m scripts.test_chatbot`.

Dữ liệu `data/intent_examples.json`: 64 câu train và 16 câu test được viết riêng, 8 nhãn. Đây là dữ liệu phát triển tự biên soạn, không phải dữ liệu bệnh nhân hoặc bộ đánh giá độc lập của chuyên gia. Không sinh biến thể từ câu test vào train. TF-IDF ký tự 2–5 gram và Logistic Regression học từ train; không gọi API và không fine-tune LLM.

Checkpoint: `models/chat_intent.joblib`. Chỉ số và dự đoán từng câu: `results/intent_evaluation.json`. Tập test nhỏ nên kết quả cao không chứng minh chất lượng hội thoại rộng hoặc độ an toàn y khoa.

Khi luật không xác định được chủ đề, mô hình đề xuất ý định. Ngưỡng xác suất 0.42, chênh lệch hai lớp 0.15 và tương đồng 0.25 giúp từ chối câu thiếu bằng chứng; các ngưỡng là lựa chọn kỹ thuật ban đầu, chưa hiệu chuẩn trên tập validation độc lập. Lớp ngoài phạm vi luôn bị từ chối. Nội dung trả lời vẫn lấy từ KB và luật; điểm ý định không phải xác suất mắc bệnh. Các luật về đơn vị, thuốc và khẩn cấp vẫn áp dụng sau định tuyến.

## Nhánh Qwen chạy local

Nhánh hội thoại mới có thực nghiệm tinh chỉnh LoRA riêng trên Qwen3 1.7B. Xem `experiments/local_qwen/README.md` và log `results/local_qwen`. Mô hình ý định ở trên vẫn là một thành phần khác, không đồng nhất với Qwen. Bản Vercel dùng KB/luật; để dùng Qwen trên GPU máy cá nhân, chạy `run-local-qwen.ps1` rồi mở http://localhost:8766.
