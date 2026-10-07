import joblib
import shutil
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.tree import DecisionTreeClassifier

from src import serve


@pytest.fixture
def client(tmp_path, monkeypatch):
    features = pd.DataFrame([[0] * 10, [1] * 10], columns=[f"f{i}" for i in range(10)])
    model = DecisionTreeClassifier(random_state=42).fit(features, [0, 1])
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    monkeypatch.setenv("LOCAL_MODEL_PATH", str(path))
    with TestClient(serve.app) as test_client:
        yield test_client


def test_health_and_both_prediction_labels(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    for prediction in [0, 1]:
        response = client.post("/score", json={"features": [prediction] * 10})
        assert response.status_code == 200
        assert response.json() == {
            "prediction": prediction,
            "label": "thu_nhap_cao" if prediction else "thu_nhap_thap",
        }


def test_score_rejects_wrong_feature_count(client):
    assert client.post("/score", json={"features": [1, 2]}).status_code == 400


def test_score_rejects_non_numeric_feature(client):
    assert client.post("/score", json={"features": ["invalid"] * 10}).status_code == 422


def test_cloud_startup_downloads_model(tmp_path, monkeypatch):
    from unittest.mock import MagicMock

    features = pd.DataFrame([[0] * 10, [1] * 10])
    source = tmp_path / "source.joblib"
    joblib.dump(DecisionTreeClassifier().fit(features, [0, 1]), source)
    destination = tmp_path / "models" / "model.joblib"
    monkeypatch.delenv("LOCAL_MODEL_PATH", raising=False)
    monkeypatch.setattr(serve, "ARTIFACT_BUCKET", "unit-test-bucket")
    monkeypatch.setattr(serve, "MODEL_PATH", str(destination))
    client = MagicMock()
    client.download_file.side_effect = lambda bucket, key, path: shutil.copyfile(source, path)
    monkeypatch.setattr(serve, "_s3_client", client)
    with TestClient(serve.app) as test_client:
        assert test_client.get("/healthz").status_code == 200
    client.download_file.assert_called_once_with(
        "unit-test-bucket", "artifacts/current/model.joblib", str(destination)
    )
    assert destination.is_file()
