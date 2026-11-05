# Kiểm chứng cuối Tiểu luận 03

Ngày kiểm chứng: 23/10/2026, múi giờ Asia/Ho_Chi_Minh.

## Kết quả bàn giao

| Thành phần | Trạng thái | Bằng chứng |
|---|---|---|
| Word đúng tên yêu cầu | Đã hoàn thành | `tieuluan03_06_02_giangkt.254.docx` |
| PDF đúng tên yêu cầu | Đã hoàn thành | `tieuluan03_06_02_giangkt.254.pdf`, bản mở rộng 78 trang |
| Bìa, TOC, năm chương | Đã kiểm tra | 113 mục TOC khớp PDF; không có danh mục phụ hay tài liệu tham khảo |
| Định dạng | Đã kiểm tra | A4; Times New Roman; body 13 pt, justify, line spacing 1,3; lề trái/phải/trên/dưới 3/2/2,5/2,5 cm |
| Màu và công thức | Đã kiểm tra | Đen cho phần giữ; FF0000 cho phần mới/sửa; 38 công thức OMML, gồm các công thức CNN/RNN đã dựng lại rõ nét |
| Phân tích mở rộng | Đã đối chiếu dữ liệu | 43 hình, 26 bảng; 12 hình mới có nguồn đầu vào và SHA-256 trong `figure_lineage.json`; `analysis_verified.json` xác nhận phép tính và nguồn |
| Render Word và PDF | Đã chạy, rà trực quan từng trang | Không phát hiện tràn lề, glyph thay thế hoặc bảng bị cắt; `report_audit.json` |
| Notebook chính | Run All full thành công | `main.ipynb`, 29 cells gồm 18 code cells có execution count 1–18, không có output lỗi |
| Thực nghiệm mới | Đã train thực tế trên CPU | ML hai dataset, CNN 8 epoch, sáu RNN/LSTM/GRU × 35 epoch; checkpoint/history/predictions trong `artifacts_tl03` |
| Tái lập KG/RAG và ML TL02 | Đã chạy thành công | Kết quả riêng trong `artifacts_tl03/legacy`, MAE chính khớp nguồn |
| API inference | Đã kiểm tra | 5 nhóm Python tests; đối chiếu bảng, CNN và cả sáu checkpoint chuỗi |
| Chức năng cũ | Đã kiểm tra hồi quy | 16 nhóm engine + 14 nhóm clinical JS, đều PASS |
| Website production | Đã deploy, kiểm tra thành công | https://rag-httm-chatbot.vercel.app/ |
| API production | Đã kiểm tra thật | GET frontend/health; 5 POST trả 200; 4 yêu cầu lỗi trả 400, gồm ảnh toàn 0; `production_verified.json` |
| Giao diện production | Đã kiểm tra qua trình duyệt | CNN ảnh test 7→7; link mở đúng bài toán/miền vàng; phần tử chuỗi trống bị từ chối; vàng hiển thị Persistence. `web_ui_detail_verified.json`, ảnh chụp `web_detail_cnn.png` |
| Responsive | Đã kiểm tra cơ bản | Viewport 390 × 844: document/body scrollWidth không vượt viewport; đã trả về viewport mặc định |
| GitHub | Đã commit và push thành công | Commit bản mở rộng `5d81041`; ba nhánh `main`, `tieuluan03-giangkt`, `tieuluan03-detailed-report`; cập nhật fast-forward từ `57597a7`, không force-push |

Các file bắt buộc bổ sung đã có: `README.md`, `CHANGELOG.md`, `EXPERIMENT_RESULTS.md`, `PROJECT_REPORT.md`, file kiểm chứng này và mã nguồn web/API. `PROJECT_REPORT.md` phân tích từng demo, dữ liệu, tiền xử lý, cơ chế, kết quả và giới hạn; các link từ giao diện trỏ đến đúng mục.

## Kiểm tra định lượng

`notebook_verified.json`: Run All full hoàn tất lần cuối lúc 03:48:03 ngày 23/10/2026, seed 42; số liệu được đối chiếu lại từ predictions. Lần này tái sử dụng cache đã kiểm tra của các trọng số, chạy lại pipeline legacy và tính mới toàn bộ chẩn đoán; không nhận là một lần huấn luyện mới khi dùng cache.

Chạy lại các test sau khi hoàn tất tích hợp:

- `python tests/test_inference03.py`: 5/5 PASS. Sai khác tuyệt đối lớn nhất: bảng 7,11e-15; CNN logits 2,27e-6; giá chuỗi 2,06e-5.
- `node tests/engine.test.cjs`: 16/16 nhóm PASS; 36 vector Python/JavaScript có sai khác lớn nhất 2,85e-14.
- `node tests/clinical.test.cjs`: 14/14 nhóm PASS. Đây là kiểm tra quy tắc phần mềm, không phải chứng nhận lâm sàng.
- `tests/check_production03.py`: các trường hợp CNN, giá nhà, phân loại tổng hợp, FPT và vàng chạy trên HTTPS production.

Các metrics được ghi chính xác trong `EXPERIMENT_RESULTS.md`; bảng đối chiếu Chương → bài toán → dataset → model → notebook → metrics → website nằm trong cùng file. Không dùng số liệu của tác giả TL01 làm kết quả mới.

## Quy trình PDF và giới hạn trình xem

PDF xuất từ bản Word cuối qua bộ render LibreOffice. Bộ xuất này bỏ màu OMML dù XML Word có màu đỏ; `finalize_pdf03.py` đếm công thức đỏ từ Word và khôi phục toán tử màu trong PDF vector. Kiểm tra tự động xác nhận toàn bộ văn bản và tọa độ không đổi; không raster hóa hoặc thay nội dung công thức. Bản PDF cuối được render lại để xem màu.

Đã kiểm tra bằng LibreOffice/PDF, chưa mở bằng Microsoft Word desktop thực. Word giữ TOC, bookmark, PAGEREF và OMML; sau khi người dùng chỉnh nội dung cần cập nhật F9 và xuất lại PDF. Các công thức độc lập ML/CNN/RNN đã chuyển thành native math; sơ đồ/ảnh nguồn vẫn là ảnh.

## Các phần chưa kiểm thử hoặc không triển khai

- Chưa train GPU, đa seed, nhiều cửa sổ hoặc benchmark nhiều máy; chỉ xác nhận cấu hình CPU đã ghi trong manifest.
- Có chế độ quick riêng, nhưng lần kiểm chứng chính chạy full; không coi quick là một lần Run All đã xác minh riêng.
- Không dựng lại ASL, e-commerce hay ba bản Scratch/Keras/PyTorch của tác giả TL01; các kết quả đó không được nhận là sản phẩm mới và không deploy giả.
- Chưa có kiểm định chuyên gia y tế/tài chính hoặc đánh giá LLM faithfulness. RAG dùng TF-IDF, đồ thị và bộ tổng hợp xác định; sáu câu hỏi chỉ là smoke test.
- Chưa có E2E toàn bộ tổ hợp input trên mọi trình duyệt/thiết bị hoặc kiểm thử tải lớn. Đã kiểm tra parity, validation, API production, CNN và chatbot qua UI.
- Website dùng dữ liệu thị trường snapshot, không phải feed trực tiếp. Dữ liệu y tế tổng hợp, tin đăng nhà và dự báo giá không phải công cụ ra quyết định thực tế.
- Lần chạy đầu trên máy sạch cần Internet và quyền cài dependency. Chưa kiểm tra lại trên một máy hoàn toàn mới độc lập với môi trường hiện tại.

Không còn bước xác thực bên ngoài đang chặn deploy: phiên Vercel và quyền GitHub hiện có đã được sử dụng, không ghi token vào notebook hay mã nguồn.

## An toàn repository

Thư mục `.git` tại workspace không phải checkout Git sử dụng được, nên đồng bộ thông qua bản clone riêng tại `/tmp/httm_tl03_remote`, giữ nguyên workspace và các file nguồn. Không force-push. Tệp gốc trên remote được giữ lại. Raw dataset tải tự động, font Microsoft dùng render, `.env*`, `.vercel`, cache và `tmp` không được commit. Model lớn nhất khoảng 16 MB; bundle deploy nén khoảng 5,1 MB.

Bản bàn giao mở rộng được quét các mẫu credential phổ biến trước khi commit: 69 tệp text thay đổi không có mẫu khớp; kết quả và checksum tám tệp đầu ra được lưu trong `delivery_verified.json`. Đây là kiểm tra bổ sung, không phải bảo đảm phát hiện mọi dạng secret. GitHub xác nhận cập nhật `57597a7..5d81041` bằng atomic push cho cả ba nhánh; bản ghi kiểm chứng được chốt bằng commit kế tiếp. Không xóa tệp nguồn hay sửa lịch sử commit. Lần kiểm tra HTTPS cuối vẫn nhận 200 cho cả năm ca inference và 400 cho input không hợp lệ.
