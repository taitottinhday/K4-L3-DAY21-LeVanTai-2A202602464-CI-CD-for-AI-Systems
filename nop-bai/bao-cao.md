# Báo Cáo Lab Day 21 - CI/CD cho AI Systems

| | |
|---|---|
| Họ và tên | Lê Văn Tài |
| MSSV | 2A202602464 |
| Lớp / Khóa | K4 |
| Repo GitHub | https://github.com/taitottinhday/K4-L3-DAY21-LeVanTai-2A202602464-CI-CD-for-AI-Systems |
| Ngày nộp | 07/10/2026 |

---

## 1. Bộ Siêu Tham Số Đã Chọn và Lý Do

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---:|---:|---:|---:|---:|
| 1 | 100 | 0.1 | 3 | 0.7109 | 0.8780 |
| 2 | 50 | 0.05 | 2 | 0.6051 | 0.8460 |
| 3 | 200 | 0.1 | 5 | 0.7149 | 0.8740 |

**Bộ siêu tham số đã chọn:** `n_estimators=200`, `learning_rate=0.1`, `max_depth=5`.

**Lý do:** Lần 3 có F1 cao nhất và vượt Quality Gate 0.65. Lần 1 có accuracy cao nhất nhưng F1 thấp hơn, cho thấy accuracy chưa phản ánh tốt lớp dương. Lần 2 bị underfit. Tăng số cây và độ sâu ở lần 3 cải thiện F1; learning rate 0.1 giữ cân bằng giữa tốc độ học và số cây.

---

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Tập Adult có khoảng 24,8% mẫu lớp dương (thu nhập trên 50K) và 75,2% lớp âm. Mô hình luôn dự đoán lớp âm vẫn đạt accuracy xấp xỉ 75% nhưng không phát hiện được người có thu nhập cao. F1 của lớp dương kết hợp precision và recall, phản ánh cả dự đoán dương đúng lẫn khả năng tìm đủ mẫu dương. Vì vậy Quality Gate dùng `f1_score >= 0.65`. Mã nguồn gọi trực tiếp `f1_score(y_eval, preds)`, không dùng `average="macro"` hay `average="weighted"`, để lớp đa số không che lấp chất lượng thật của lớp dương.

---

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| Cài đặt dừng giữa chừng | `pip install` bị hủy nên pandas chưa có | Kích hoạt lại `.venv` và cài đủ requirements. |
| MLflow lỗi SQLite | SQLAlchemy mới không tương thích MLflow 2.13.0 | Khóa `SQLAlchemy==2.0.29`. |
| Chưa có Cloud Storage/VM | Project GCP chưa bật billing, chưa có bucket | Hoàn thiện workflow và kiểm thử local; phần cloud cần billing và secrets. |

---

## 4. So Sánh Bước 2 và Bước 3

| | f1_score | accuracy |
|---|---:|---:|
| Bước 2 (chỉ `train_batch1`) | 0.7149 | 0.8740 |
| Bước 3 (thêm `train_batch2`) | 0.7354 | 0.8820 |

**Nhận xét:** Thêm 22.361 mẫu cùng phân phối làm F1 tăng 0.0205 và accuracy tăng 0.0080 trong local. Kết quả vẫn vượt Quality Gate; phần DVC, GitHub Actions và VM cần Cloud Storage, secrets và máy chủ thực tế.

## 5. Phần Bonus Đã Thực Hiện

- [x] Bonus 2 - Điều chỉnh ngưỡng quyết định: quét ngưỡng 0.1–0.9; ngưỡng 0.3 cho F1 tốt nhất 0.7537.
- [x] Bonus 3 - Báo cáo precision / recall tự động: ghi precision, recall và confusion matrix vào `outputs/report.json` và MLflow artifact.
- [x] Bonus 5 - Cảnh báo lệch lạc dữ liệu: so sánh tỷ lệ lớp dương với mốc 24,8%; hiện lệch 0,016% và không cảnh báo.
