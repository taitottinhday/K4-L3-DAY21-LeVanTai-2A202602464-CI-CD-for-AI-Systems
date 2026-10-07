# Chạy và kiểm tra bài lab trong VS Code (PowerShell)

Tất cả lệnh dưới đây chạy tại thư mục gốc repository. Các thay đổi mới đang được giữ local theo yêu cầu của Lê Văn Tài.

## MLflow

```powershell
.\.venv\Scripts\Activate.ps1
$env:MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
$env:MLFLOW_ARTIFACT_ROOT = "./mlartifacts"
python src/train.py
mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

Mở `http://localhost:5000`. Experiment: `adult-income-classification`. Lọc `tags.lab_step = 'step1'` để thấy đúng ba thí nghiệm ban đầu; sắp xếp `f1_score` giảm dần. Chọn cả ba run và nhấn Compare để xem đủ tham số và metrics trên màn hình nhỏ.

Dataset hiện có 44.722 mẫu; không chạy lại `prepare_data.py` nếu muốn giữ trạng thái Bước 3. `append_batch.py` đã có kiểm tra để tránh ghép trùng batch 2.

## Kiểm thử và API local

```powershell
python -m pytest tests/ -v
python -m src.quality_gate --report outputs/report.json
$env:LOCAL_MODEL_PATH = (Resolve-Path models/model.joblib).Path
python -m uvicorn src.serve:app --host 127.0.0.1 --port 18080
```

Mở terminal thứ hai, kích hoạt `.venv`, rồi chạy:

```powershell
python scripts/check_api.py
```

API local dùng cổng 18080 vì Windows đang từ chối bind cổng 8080. Kết quả `/healthz`, hai mẫu thu nhập và lỗi thiếu đặc trưng được lưu tại `nop-bai/api-local.json`. Đây là kiểm thử local, chưa phải bằng chứng VM.

Tests dùng dữ liệu, tracking và thư mục tạm riêng nên không ghi đè model/report thật. `f1_score` trong report và Quality Gate vẫn tính lớp dương ở ngưỡng mặc định 0.5. `best_threshold` là kết quả nghiên cứu trên holdout, cần xác nhận lại trên dữ liệu chưa dùng trước khi đưa vào phục vụ.

## Cấu hình AWS đã hoàn thành

Lab đã dùng AWS theo ánh xạ trong `tasks/buoc-2.md`: S3 bucket `income-cicd-513594860142-20261007`, EC2 `13.212.26.133`, IAM OIDC cho GitHub Actions và SSM cho Release. Hai workflow cloud đều hoàn thành đủ bốn job. API VM được kiểm tra từ CloudShell; xem `nop-bai/anh-chup-man-hinh/04-curl-api.png`.

Sau khi có bucket và file credentials riêng (không commit), cấu hình local:

```powershell
$env:ARTIFACT_BUCKET = "TEN_BUCKET_THUC_TE"
$env:GOOGLE_APPLICATION_CREDENTIALS = (Resolve-Path sa-key.json).Path
dvc remote add -d labstore "gs://$env:ARTIFACT_BUCKET/dvc"
dvc remote modify --local labstore credentialpath $env:GOOGLE_APPLICATION_CREDENTIALS
dvc push
```

Chuẩn bị VM bằng cùng `requirements.txt` để scikit-learn khớp phiên bản model. Dùng `deploy/income-api.service.template`, thay `USER_NAME` đúng tên tài khoản VM. File `.env` trên VM chứa `ARTIFACT_BUCKET` và `GOOGLE_APPLICATION_CREDENTIALS`; bỏ `LOCAL_MODEL_PATH` để server tải model GCS. Kiểm tra cổng 8080/firewall và SSH trước khi chạy workflow.

GitHub cần 5 secrets: `STORAGE_CREDENTIALS`, `ARTIFACT_BUCKET`, `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`. Workflow lưu model ở `artifacts/candidates/<commit>/`; sau Quality Gate mới đưa sang `artifacts/current/`, kiểm tra F1 không giảm so với model hiện tại và giữ bản cũ trong `artifacts/previous/`.

Quy trình đã thực hiện đúng: chạy cloud lần đầu với 22.361 mẫu, sau đó ghép batch 2, `dvc push` thành công trước commit/push dữ liệu. Run Bước 3 được kích hoạt tự động bởi commit data. Chưa tự nộp VLearn vì đây là thao tác cuối cùng trên nền tảng bên ngoài repository.
