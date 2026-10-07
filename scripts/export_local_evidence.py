"""Export actual MLflow runs and reports; never substitute for cloud evidence."""

import json
import shutil
from pathlib import Path

from mlflow.tracking import MlflowClient


def main():
    client = MlflowClient(tracking_uri="sqlite:///mlflow.db")
    experiment = client.get_experiment_by_name("adult-income-classification")
    runs = client.search_runs(
        [experiment.experiment_id], "tags.lab_step = 'step1'",
        order_by=["metrics.f1_score DESC"],
    )
    assert len(runs) == 3, "Expected the three real Step 1 runs"
    run_results = [{
        "run_id": run.info.run_id,
        "run_name": run.data.tags.get("mlflow.runName"),
        "params": run.data.params,
        "metrics": {key: run.data.metrics[key] for key in ["f1_score", "accuracy", "train_samples"]},
    } for run in runs]
    step3 = json.loads(Path("outputs/report.json").read_text(encoding="utf-8"))
    assert step3["train_samples"] == 44722
    evidence = {
        "environment": "local; Step 2/3 GitHub Actions artifacts are still pending",
        "tracking_uri": "sqlite:///mlflow.db",
        "step1": run_results,
        "baseline_22361_samples": run_results[0]["metrics"],
        "updated_44722_samples": step3,
    }
    Path("nop-bai/ket-qua-local.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    shutil.copyfile("outputs/detail.txt", "nop-bai/detail-local.txt")
    shutil.copyfile("outputs/thresholds.json", "nop-bai/thresholds-local.json")
    print("Exported actual experiment metrics, threshold sweep and per-class report.")


if __name__ == "__main__":
    main()
