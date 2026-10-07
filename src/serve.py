from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, FiniteFloat
import boto3
from contextlib import asynccontextmanager
from pathlib import Path
import pandas as pd
import joblib
import os

ARTIFACT_BUCKET = os.getenv("ARTIFACT_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
MODEL_KEY = "artifacts/current/model.joblib"
MODEL_PATH = os.path.expanduser(os.getenv("MODEL_PATH", "~/models/model.joblib"))
model = None
_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", region_name=AWS_REGION)
    return _s3_client


def download_model():
    """
    Tai file model.joblib tu cloud storage ve may khi server khoi dong.

    Ham nay duoc goi trong FastAPI lifespan. Tren EC2, boto3 su dung
    credential tam thoi tu IAM instance profile.
    """
    if not ARTIFACT_BUCKET:
        raise RuntimeError("ARTIFACT_BUCKET is not configured")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    get_s3_client().download_file(ARTIFACT_BUCKET, MODEL_KEY, MODEL_PATH)
    print("Model da duoc tai xuong tu cloud storage.")


@asynccontextmanager
async def lifespan(app):
    global model
    if os.getenv("LOCAL_MODEL_PATH"):
        model_path = Path(os.environ["LOCAL_MODEL_PATH"])
        print(f"Loading local model: {model_path}")
    else:
        download_model()
        model_path = Path(MODEL_PATH)
    model = joblib.load(model_path)
    yield


app = FastAPI(title="Adult Income API", lifespan=lifespan)


class ScoreRequest(BaseModel):
    features: list[FiniteFloat]


@app.get("/healthz")
def healthz():
    """
    Endpoint kiem tra suc khoe server.
    GitHub Actions goi endpoint nay sau khi deploy de xac nhan server dang chay.

    Tra ve: {"status": "ok"}
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not ready")
    return {"status": "ok"}


@app.post("/score")
def score(req: ScoreRequest):
    """
    Endpoint suy luan chinh.

    Dau vao : JSON {"features": [f1, f2, ..., f10]}
    Dau ra  : JSON {"prediction": <0|1>, "label": <"thu_nhap_thap"|"thu_nhap_cao">}

    Thu tu 10 dac trung (khop voi thu tu trong FEATURE_NAMES cua test):
        age, workclass, education_num, marital_status, occupation,
        relationship, sex, capital_gain, capital_loss, hours_per_week
    """
    if len(req.features) != 10:
        raise HTTPException(
            status_code=400,
            detail="Expected 10 features (adult income)",
        )

    if model is None:
        raise HTTPException(status_code=503, detail="Model is not ready")
    columns = getattr(model, "feature_names_in_", None)
    features = pd.DataFrame([req.features], columns=columns)
    prediction = int(model.predict(features)[0])
    label = "thu_nhap_cao" if prediction == 1 else "thu_nhap_thap"
    return {"prediction": prediction, "label": label}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
