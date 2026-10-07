# Trạng thái hoàn thành local

Ngày kiểm tra: 07/10/2026. Bản AWS đã được triển khai và commit/push.

## Đã hoàn thành và có thể kiểm chứng

- `src/train.py`: huấn luyện Gradient Boosting, log MLflow, report, model, threshold sweep, confusion matrix, precision/recall và data-drift check.
- `src/serve.py`: chạy local bằng `LOCAL_MODEL_PATH` hoặc tải model từ GCS khi chạy trên VM; có `/healthz` và `/score`.
- `.github/workflows/cicd.yml`: đủ bốn job Unit Test, Train, Quality Gate, Release; model chỉ promotion sau quality gate.
- DVC đã tạo các pointer local cho `train_batch1`, `holdout`, `train_batch2`; chưa có remote cloud để `dvc push`.
- `pytest`: 17 passed. MLflow SQLite có 3 run Step 1 thật: F1 0.7109, 0.6051, 0.7149.
- Model với 44.722 mẫu đạt F1 0.7354, accuracy 0.8820; threshold sweep cho F1 tốt nhất 0.7537 tại 0.30 trên holdout.
- Ảnh thật: `01-mlflow-ui.png` là Compare Runs của MLflow; `06-api-local.png` là Swagger API local, không phải VM.

## Bằng chứng cloud đã xác nhận

AWS S3 bucket `income-cicd-513594860142-20261007` đã nhận DVC objects và model artifacts. EC2 `13.212.26.133` chạy API qua systemd, GitHub Actions dùng OIDC và SSM. Run 37625952815 (Bước 2) và run 37628281055 (Bước 3) đều có đủ bốn job xanh. Ảnh và report thật được lưu trong `nop-bai/`.

## Khi có cloud credentials

Tạo bucket/VM, cấu hình DVC remote và 5 GitHub secrets, bật Actions; chạy `dvc push` trước khi push Git. Chạy cloud lần đầu với 22.361 mẫu, sau đó append batch 2 và push commit chỉ thay đổi pointer `.dvc` để lấy bằng chứng Bước 3.
