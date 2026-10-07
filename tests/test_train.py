import os
import json
import numpy as np
import pandas as pd
import pytest
from src.train import train


FEATURE_NAMES = [
    "age", "workclass", "education_num", "marital_status", "occupation",
    "relationship", "sex", "capital_gain", "capital_loss", "hours_per_week",
]


@pytest.fixture(autouse=True)
def isolated_tracking(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", (tmp_path / "mlruns").as_uri())
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "unit-tests")


def _make_temp_data(tmp_path):
    """
    Tao dataset nho voi cung schema Adult de su dung trong test.

    pytest cung cap `tmp_path` la mot thu muc tam thoi, tu dong xoa sau khi test ket thuc.
    Ham nay dung du lieu ngau nhien nen khong can ket noi cloud storage hay tai file CSV thuc.
    """
    rng = np.random.default_rng(0)
    n = 200

    X = rng.random((n, len(FEATURE_NAMES)))

    y = rng.integers(0, 2, size=n)

    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["target"] = y

    train_path = str(tmp_path / "train.csv")
    eval_path = str(tmp_path / "holdout.csv")
    df.iloc[:160].to_csv(train_path, index=False)
    df.iloc[160:].to_csv(eval_path, index=False)

    return train_path, eval_path


def test_train_returns_float(tmp_path):
    """Kiem tra ham train() tra ve mot so thuc nam trong [0.0, 1.0]."""
    train_path, eval_path = _make_temp_data(tmp_path)

    f1 = train(
        {"n_estimators": 10, "learning_rate": 0.1, "max_depth": 2},
        data_path=train_path,
        eval_path=eval_path,
    )
    assert isinstance(f1, float)
    assert 0.0 <= f1 <= 1.0


def test_report_file_created(tmp_path, capsys):
    """Kiem tra file outputs/report.json duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "learning_rate": 0.1, "max_depth": 2},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert os.path.exists("outputs/report.json")
    with open("outputs/report.json", encoding="utf-8") as f:
        report = json.load(f)
    assert "f1_score" in report
    assert "accuracy" in report
    assert len(report["confusion_matrix"]) == 2
    assert sum(map(sum, report["confusion_matrix"])) == 40
    assert report["train_samples"] == 160
    assert report["best_f1_score"] >= report["f1_score"]
    with open("outputs/thresholds.json", encoding="utf-8") as f:
        sweep = json.load(f)
    assert len(sweep) == 17
    assert sweep[0]["threshold"] == 0.1
    assert sweep[-1]["threshold"] == 0.9
    assert os.path.exists("outputs/detail.txt")
    assert "DATA DRIFT" in capsys.readouterr().out


def test_model_file_created(tmp_path):
    """Kiem tra file models/model.joblib duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "learning_rate": 0.1, "max_depth": 2},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert os.path.exists("models/model.joblib")
