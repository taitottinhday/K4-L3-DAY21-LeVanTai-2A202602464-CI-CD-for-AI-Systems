"""Promote a staged candidate after F1 checks; retain the previous version."""

import json
import os

import boto3

from src.quality_gate import check_quality


AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")


def promote():
    bucket_name = os.environ["ARTIFACT_BUCKET"]
    s3 = boto3.client("s3", region_name=AWS_REGION)
    candidate_prefix = f"artifacts/candidates/{os.environ['GITHUB_SHA']}"
    candidate_model_key = f"{candidate_prefix}/model.joblib"
    candidate_report_key = f"{candidate_prefix}/report.json"

    def exists(key):
        try:
            s3.head_object(Bucket=bucket_name, Key=key)
            return True
        except s3.exceptions.ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
                return False
            raise

    def read_json(key):
        with s3.get_object(Bucket=bucket_name, Key=key)["Body"] as body:
            return json.loads(body.read().decode("utf-8"))

    candidate_report = read_json(candidate_report_key)
    current_report_key = "artifacts/current/report.json"
    previous_f1 = None
    if exists(current_report_key):
        previous_f1 = float(read_json(current_report_key)["f1_score"])
    new_f1 = float(candidate_report["f1_score"])
    check_quality(new_f1, previous_f1)
    if not exists(candidate_model_key):
        raise RuntimeError("Candidate model is missing")
    print(f"Promotion check passed: new F1={new_f1:.6f}; previous={previous_f1}")
    current_model_key = "artifacts/current/model.joblib"
    if exists(current_model_key):
        s3.copy_object(
            Bucket=bucket_name,
            Key="artifacts/previous/model.joblib",
            CopySource={"Bucket": bucket_name, "Key": current_model_key},
        )
    if exists(current_report_key):
        s3.copy_object(
            Bucket=bucket_name,
            Key="artifacts/previous/report.json",
            CopySource={"Bucket": bucket_name, "Key": current_report_key},
        )
    s3.copy_object(
        Bucket=bucket_name,
        Key=current_model_key,
        CopySource={"Bucket": bucket_name, "Key": candidate_model_key},
    )
    s3.copy_object(
        Bucket=bucket_name,
        Key=current_report_key,
        CopySource={"Bucket": bucket_name, "Key": candidate_report_key},
    )
    print("Promoted candidate to artifacts/current; previous version retained.")


if __name__ == "__main__":
    promote()
