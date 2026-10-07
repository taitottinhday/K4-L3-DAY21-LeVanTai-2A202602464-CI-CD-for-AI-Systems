import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
import json
import joblib
import os
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# Nguong chat luong cua lab nay la f1_score, KHONG phai accuracy.
# Ly do: bo du lieu Adult co ty le lop 75/25. Mot mo hinh doan bua
# "thu nhap thap" cho moi mau da dat accuracy 0.75 ma khong hoc duoc gi.
F1_THRESHOLD = 0.65
BASELINE_POSITIVE_RATE = 0.248


def train(
    params: dict,
    data_path: str = "data/train_batch1.csv",
    eval_path: str = "data/holdout.csv",
) -> float:
    """
    Huan luyen mo hinh va ghi nhan ket qua vao MLflow.

    Tham so:
        params     : dict chua cac sieu tham so cho GradientBoostingClassifier.
        data_path  : duong dan den file du lieu huan luyen.
        eval_path  : duong dan den file du lieu danh gia (holdout).

    Tra ve:
        f1 (float): diem F1 cua lop duong (thu nhap > 50K) tren tap holdout.
    """

    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    mlflow.set_experiment("adult-income-classification")

    with mlflow.start_run():
        mlflow.log_params(params)

        model = GradientBoostingClassifier(**params, random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict(X_eval)
        probabilities = model.predict_proba(X_eval)[:, 1]
        f1 = float(f1_score(y_eval, preds))
        acc = float(accuracy_score(y_eval, preds))
        precision = float(precision_score(y_eval, preds, zero_division=0))
        recall = float(recall_score(y_eval, preds, zero_division=0))

        # Bonus 2: tìm ngưỡng xác suất tốt hơn ngưỡng mặc định 0.5.
        threshold_results = []
        for threshold in [i / 10 for i in range(1, 10)]:
            threshold_preds = (probabilities >= threshold).astype(int)
            threshold_results.append(
                (float(f1_score(y_eval, threshold_preds)), threshold)
            )
        best_f1, best_threshold = max(threshold_results)

        # Bonus 5: theo dõi tỷ lệ lớp dương so với mốc của bộ Adult.
        positive_rate = float(y_train.mean())
        drift_delta = abs(positive_rate - BASELINE_POSITIVE_RATE)
        drift_warning = drift_delta > 0.05
        matrix = confusion_matrix(y_eval, preds).tolist()

        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("best_threshold", best_threshold)
        mlflow.log_metric("best_f1_score", best_f1)
        mlflow.log_metric("positive_rate", positive_rate)
        mlflow.log_metric("drift_delta", drift_delta)
        mlflow.set_tag("data_drift_warning", str(drift_warning).lower())
        mlflow.sklearn.log_model(model, "model")

        print(f"F1: {f1:.4f} | Accuracy: {acc:.4f}")

        os.makedirs("outputs", exist_ok=True)
        report = {
            "f1_score": f1,
            "accuracy": acc,
            "precision": precision,
            "recall": recall,
            "best_threshold": best_threshold,
            "best_f1_score": best_f1,
            "positive_rate": positive_rate,
            "drift_delta": drift_delta,
            "drift_warning": drift_warning,
            "confusion_matrix": matrix,
        }
        with open("outputs/report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        mlflow.log_text(json.dumps(report, indent=2), "metrics/bonus_metrics.json")

        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.joblib")

    return f1


if __name__ == "__main__":
    with open("params.yaml") as f:
        params = yaml.safe_load(f)
    train(params)
