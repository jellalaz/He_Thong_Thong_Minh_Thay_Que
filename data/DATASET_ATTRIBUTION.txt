# Thông tin kỹ thuật về dữ liệu

Tệp dành cho mã nguồn/tái lập, không chèn thành tài liệu tham khảo của báo cáo.

| Dataset | Trang công bố / điểm tải | Cách dùng |
|---|---|---|
| Diabetes Risk Prediction 50K | https://www.kaggle.com/datasets/mobeenfatimah/diabetes-risk-prediction-dataset-50k-patients | Public ZIP, dữ liệu tổng hợp; nhãn dataset để kiểm chứng pipeline |
| Vietnam Housing 2024 | https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024 | Public ZIP; tỷ VND; tin đăng, không bảo đảm là giao dịch hoàn tất |
| MNIST | https://storage.googleapis.com/cvdf-datasets/mnist/ | Bốn tệp IDX gzip, kiểm tra magic number và kích thước |
| Diabetes regression | https://scikit-learn.org/stable/datasets/toy_dataset.html#diabetes-dataset | `load_diabetes(scaled=False)`; 442 người đã mắc bệnh, đích tiến triển sau một năm |
| FPT.VN / GC=F | Yahoo Finance chart API; snapshot `artifacts_giangkt/data/` | Snapshot 15/10/2021–14/10/2026; không tạo giá thị trường mô phỏng |

Raw ZIP/MNIST không đưa lên Git; notebook tải trực tiếp và cache. Kiểm tra điều khoản/giấy phép tại trang công bố khi phân phối lại dữ liệu gốc. Không tự gán một giấy phép chưa xác minh cho toàn bộ dataset hoặc báo cáo nguồn.

Hai tiểu luận được ghép lý thuyết theo quyền sử dụng sinh viên đã xác nhận. Thực nghiệm TL01 được làm lại, không nạp checkpoint hoặc nhận kết quả người khác. Biểu đồ mới được tạo từ predictions thật.

Hiệu chỉnh kỹ thuật LeNet-5 theo công trình năm 1998: https://bottou.org/papers/lecun-98h. API GRU tuân quy ước PyTorch: https://docs.pytorch.org/docs/2.14/generated/torch.nn.GRU.html. Các URL phục vụ bảo trì mã, không tạo hệ citation trong báo cáo chính.
