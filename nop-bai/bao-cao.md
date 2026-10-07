# Báo cáo Lab Day 21 - CI/CD cho AI Systems

| Thông tin | Giá trị |
|---|---|
| Họ và tên | Lê Văn Tài |
| MSSV | 2A202602464 |
| Lớp | K4 |
| Repository | https://github.com/taitottinhday/K4-L3-DAY21-LeVanTai-2A202602464-CI-CD-for-AI-Systems |

## 1. Bộ siêu tham số đã chọn

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---:|---:|---:|---:|---:|
| 1 | 100 | 0.10 | 3 | 0.7109 | 0.8780 |
| 2 | 50 | 0.05 | 2 | 0.6051 | 0.8460 |
| 3 | 200 | 0.10 | 5 | 0.7149 | 0.8740 |

Chọn `200/0.1/5` vì có F1 cao nhất trong ba thí nghiệm và vượt ngưỡng 0.65. Cấu hình 50 cây, learning rate thấp và cây nông bị underfit. Số cây và learning rate có quan hệ đánh đổi: learning rate thấp thường cần nhiều cây hơn.

## 2. Vì sao Quality Gate dùng F1

Lớp dương chỉ chiếm khoảng 24,8%, nên accuracy có thể cao dù mô hình bỏ sót nhiều người có thu nhập cao. F1 được tính bằng `f1_score(y_eval, preds)` cho riêng lớp dương, kết hợp precision và recall, phù hợp hơn với mục tiêu phát hiện lớp thiểu số. Quality Gate đặt `f1_score >= 0.65`, không dùng macro hoặc weighted average.

## 3. Khó khăn và cách giải quyết

Pip bị hủy giữa chừng làm môi trường thiếu pandas; tôi kích hoạt lại `.venv` và cài đủ requirements. GCP yêu cầu khoản trả trước 800.000 đồng sau khi khoản thanh toán trước đó được hoàn, nên chuyển sang ánh xạ AWS theo tài liệu lab: S3 thay Cloud Storage, EC2 thay VM và IAM OIDC thay khóa dài hạn. Lần chạy Actions đầu bị lỗi `AssumeRoleWithWebIdentity` do GitHub dùng immutable OIDC subject; tôi kiểm tra claim thực tế, sửa trust policy đúng repository/branch và rerun thành công.

## 4. So sánh Bước 2 và Bước 3

| Chỉ số | Bước 2 (22.361 mẫu) | Bước 3 (44.722 mẫu) |
|---|---:|---:|
| f1_score | 0.7149 | 0.7354 |
| accuracy | 0.8740 | 0.8820 |

Bước 2 được kích hoạt bởi commit code và chạy đủ Unit Test, Train, Quality Gate, Release. Bước 3 được kích hoạt tự động bởi commit `data: bổ sung 22361 mẫu dữ liệu mới (train_batch2)`, không cần thao tác thủ công trên Actions. Thêm dữ liệu cùng phân phối làm F1 tăng 0.0205 và accuracy tăng 0.0080; cả hai lần đều vượt Quality Gate. API EC2 trả `/healthz` là `{"status":"ok"}` và `/score` trả nhãn hợp lệ.

## 5. Bonus đã thực hiện

- [ ] Bonus 1 - Không dùng DagsHub; tracking MLflow giữ cục bộ.
- [x] Bonus 2 - Quét threshold 0.1 đến 0.9; threshold 0.3 đạt F1 holdout 0.7537.
- [x] Bonus 3 - Lưu precision, recall, confusion matrix và classification report.
- [x] Bonus 4 - Release chỉ promote khi F1 mới không thấp hơn bản hiện tại và lưu bản previous.
- [x] Bonus 5 - Kiểm tra data drift so với tỷ lệ dương 24,8%; cả hai lần không cảnh báo.
