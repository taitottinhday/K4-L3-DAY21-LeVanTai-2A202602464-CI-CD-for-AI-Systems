"""Stage artifacts under the commit SHA; promotion happens after quality gate."""

import os

import boto3


def main():
    client = boto3.client("s3", region_name=os.environ["AWS_REGION"])
    bucket = os.environ["ARTIFACT_BUCKET"]
    prefix = f"artifacts/candidates/{os.environ['GITHUB_SHA']}"
    client.upload_file("models/model.joblib", bucket, f"{prefix}/model.joblib")
    client.upload_file("outputs/report.json", bucket, f"{prefix}/report.json")
    print(f"Staged candidate at {prefix}")


if __name__ == "__main__":
    main()
