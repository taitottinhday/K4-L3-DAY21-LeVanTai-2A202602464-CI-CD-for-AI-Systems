# Nộp Bài - Day 21: CI/CD cho AI Systems

Thư mục này là nơi chứa **bằng chứng nộp bài**. Bạn không cần tạo thêm thư mục nào khác:
điền vào các file có sẵn và bỏ ảnh chụp màn hình vào đúng tên file đã quy định.

```
nop-bai/
├── README.md                  <- file này (checklist)
├── bao-cao.md                 <- template báo cáo, không quá 1 trang A4
└── anh-chup-man-hinh/
    ├── README.md              <- mô tả yêu cầu của từng ảnh
    ├── 01-mlflow-ui.png
    ├── 02-actions-buoc-2.png
    ├── 03-actions-buoc-3.png
    ├── 04-curl-api.png
    └── 05-cloud-storage.png
```

---

## Checklist Trước Khi Nộp

Đánh dấu `[x]` khi hoàn thành từng mục. Checklist này phân biệt bằng chứng local đã có với phần cloud chưa thể chạy:

- [x] Repo GitHub ở chế độ **public** và chứa toàn bộ code, cấu hình đã hoàn thiện.
- [x] Đủ 5 ảnh trong `anh-chup-man-hinh/`, đúng tên file, đúng thứ tự (xem
      [yêu cầu chi tiết](anh-chup-man-hinh/README.md)).
- [x] `bao-cao.md` đã điền đủ các mục cloud và không vượt quá 1 trang A4.
- [x] Đã `git push` toàn bộ thư mục `nop-bai/` lên GitHub.
- [ ] Dán URL repo GitHub vào bài nộp trên **https://vlearn.dev**.
- [ ] Mở lại URL vừa nộp ở chế độ ẩn danh để chắc chắn repo public và người chấm xem được.

---

## Ảnh Chụp Màn Hình Tương Ứng Với Rubric

| Ảnh | Chứng minh hạng mục nào trong rubric | Điểm |
|---|---|---|
| `01-mlflow-ui.png` | Bước 1 - MLflow tracking, Bước 1 - Độ đo | 20 |
| `02-actions-buoc-2.png` | Bước 2 - CI/CD (bốn jobs màu xanh) | 16 |
| `03-actions-buoc-3.png` | Bước 3 - Tự động hóa | 12 |
| `04-curl-api.png` | Bước 2 - Serving | 12 |
| `05-cloud-storage.png` | Bước 2 - DVC | 12 |

Phần `bao-cao.md` chứng minh hạng mục **Bước 1 - Phân tích** (4 điểm) và là nơi bạn giải
trình khi một ảnh nào đó chưa thể hiện đủ (ví dụ quality gate đã chặn đúng một lần).

## Trạng thái hoàn thành ngày 07/10/2026

- [x] MLflow local có 3 run Step 1; F1 lần lượt là 0.7109, 0.6051 và 0.7149.
- [x] Huấn luyện với 44.722 mẫu: F1 0.7354, accuracy 0.8820; Quality Gate đạt.
- [x] `pytest`: 17 passed; API EC2 đã kiểm tra `/healthz` và `/score` từ AWS CloudShell.
- [x] Đủ 5 ảnh PNG, mỗi ảnh dưới 1 MB; có report thật của hai workflow trong `artifacts/step2` và `artifacts/step3`.
- [x] S3 có dữ liệu DVC, candidate/current/previous model; EC2 chạy API qua SSM.
- [x] Đã commit và push code, commit dữ liệu Bước 3 và hồ sơ nộp bài lên GitHub.

---

## Quy Ước Chung

- **Định dạng ảnh**: năm ảnh chính dùng `.png`, mỗi ảnh dưới 1 MB.
- **Không đổi số thứ tự đầu tên file.** Thứ tự này là thứ tự chấm bài.
- **Không che thông tin cần chấm**: tên job, trạng thái màu xanh, giá trị `f1_score`,
  đường dẫn bucket. Được phép che email cá nhân và khóa bí mật.
- **Cần chụp cả URL trên thanh địa chỉ** với các ảnh chụp từ trình duyệt (MLflow UI,
  GitHub Actions, Cloud Storage Console) để xác nhận đúng repo/project của bạn.
- **Tuyệt đối không commit khóa bí mật**: `sa-key.json`, nội dung GitHub Secrets, access
  key của cloud. Nếu ảnh lỡ chứa các thông tin này, hãy che lại trước khi commit.

---

## Ghi Chú Về Kích Thước Repo

Ảnh chụp màn hình được commit trực tiếp vào Git. Giữ mỗi ảnh dưới **1 MB** (chụp vùng cần
thiết thay vì toàn màn hình 4K, hoặc nén lại trước khi commit) để repo không phình to.

Nếu bạn dùng macOS, có thể nén nhanh bằng lệnh sẵn có:

```bash
sips -Z 1600 nop-bai/anh-chup-man-hinh/01-mlflow-ui.png
```
