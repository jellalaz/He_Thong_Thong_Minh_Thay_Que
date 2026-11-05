# GlucoGuide – Hệ đa agent cho bệnh tiểu đường

Hai báo cáo LaTeX độc lập nằm trong `reports/`: tiểu luận final và Project 01.

## Hai chế độ demo

- Bản công khai: https://glucoguide-giang254.vercel.app – KB, luật, mô hình dữ liệu bảng và Neo4j Aura Free.
- Bản Qwen local: chạy `run-local-qwen.ps1`, mở http://localhost:8766. Cần mô hình nền và adapter đã huấn luyện. Suy luận trên GPU máy cá nhân; không gọi API LLM bên ngoài, không bật thanh toán.

## Huấn luyện và kiểm tra

- Hướng dẫn Qwen LoRA: `experiments/local_qwen/README.md`.
- Mô hình nhận diện ý định: `TRAINING_CHATBOT.md`.
- Kiểm thử: `python -m scripts.test_chatbot`, `python -m scripts.test_intent`, `python -m scripts.test_local_agents`.
- Kết quả mô hình và dữ liệu đánh giá: `results/`.

Qwen hỗ trợ diễn đạt kiến thức có tài liệu. Thông số, thuốc và tình huống khẩn cấp đi qua luật; sản phẩm phục vụ học tập và hỗ trợ tra cứu, không xác nhận chẩn đoán hoặc kê đơn. Hai tập kiểm tra hội thoại nội bộ không phải dữ liệu lâm sàng độc lập.

Không đưa `.env`, thông tin đăng nhập, mô hình nền hoặc cache lên Git. Neo4j local dùng cấu hình `.env`; thông tin mẫu ở `.env.example`.

Bản local có nút phản hồi dưới câu trả lời kiến thức. Bảng Q học cách trình bày từ phản hồi; checkpoint Qwen của lượt thử hội thoại thứ hai chưa được triển khai vì còn lỗi câu trả lời.
