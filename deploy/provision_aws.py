"""Provision the lab with temporary AWS CLI credentials; no access keys on disk."""

import argparse
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import zipfile

import boto3
from botocore.exceptions import ClientError
import requests

REGION = "ap-southeast-1"
ACCOUNT = "513594860142"
BUCKET = "income-cicd-513594860142-20261007"
REPO = "taitottinhday/K4-L3-DAY21-LeVanTai-2A202602464-CI-CD-for-AI-Systems"
EC2_ROLE = "income-api-ec2"
CI_ROLE = "income-cicd-github"
ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "aws-cli-session" / "resources.json"


def session():
    os.environ["AWS_CONFIG_FILE"] = str(ROOT.parent / "aws-cli-session" / "config")
    credentials = json.loads(subprocess.check_output(
        ["aws", "configure", "export-credentials", "--profile", "default", "--format", "process"],
        text=True,
    ))
    result = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=REGION,
    )
    assert result.client("sts").get_caller_identity()["Account"] == ACCOUNT
    return result


def save_state(**updates):
    values = json.loads(STATE.read_text()) if STATE.exists() else {}
    values.update(updates)
    STATE.write_text(json.dumps(values, indent=2), encoding="utf-8")
    print(json.dumps(values, indent=2))
    return values


def roles(sess):
    iam = sess.client("iam")
    provider_arn = f"arn:aws:iam::{ACCOUNT}:oidc-provider/token.actions.githubusercontent.com"
    providers = iam.list_open_id_connect_providers()["OpenIDConnectProviderList"]
    if not any(p["Arn"] == provider_arn for p in providers):
        iam.create_open_id_connect_provider(
            Url="https://token.actions.githubusercontent.com",
            ClientIDList=["sts.amazonaws.com"],
            Tags=[{"Key": "Project", "Value": "income-lab"}],
        )
    trusts = {
        EC2_ROLE: {"Version": "2012-10-17", "Statement": [{
            "Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }]},
        CI_ROLE: {"Version": "2012-10-17", "Statement": [{
            "Effect": "Allow", "Principal": {"Federated": provider_arn},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {"StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                "token.actions.githubusercontent.com:sub": f"repo:{REPO}:ref:refs/heads/main",
            }},
        }]},
    }
    for name, trust in trusts.items():
        try:
            iam.get_role(RoleName=name)
        except iam.exceptions.NoSuchEntityException:
            iam.create_role(
                RoleName=name, AssumeRolePolicyDocument=json.dumps(trust),
                Description="Day21 income lab: scoped runtime role",
                Tags=[{"Key": "Project", "Value": "income-lab"}],
            )
        else:
            iam.update_assume_role_policy(RoleName=name, PolicyDocument=json.dumps(trust))
    # Narrow the Autopilot baseline to plain S3 GetObject/PutObject.
    # No KMS, Object Lambda, ACL, retention or tagging variants are used by this lab.
    policies = {
        EC2_ROLE: {"Version": "2012-10-17", "Statement": [{
            "Sid": "ReadModelAndDeployment", "Effect": "Allow", "Action": "s3:GetObject",
            "Resource": [f"arn:aws:s3:::{BUCKET}/artifacts/current/*",
                         f"arn:aws:s3:::{BUCKET}/deploy/income-api-source.zip"],
        }]},
        CI_ROLE: {"Version": "2012-10-17", "Statement": [
            {"Sid": "ListDvcAndArtifacts", "Effect": "Allow", "Action": "s3:ListBucket",
             "Resource": f"arn:aws:s3:::{BUCKET}",
             "Condition": {"StringLike": {"s3:prefix": ["dvc", "dvc/*", "artifacts", "artifacts/*"]}}},
            {"Sid": "ReadDvc", "Effect": "Allow", "Action": "s3:GetObject",
             "Resource": f"arn:aws:s3:::{BUCKET}/dvc/*"},
            {"Sid": "ReadWriteModelArtifacts", "Effect": "Allow",
             "Action": ["s3:GetObject", "s3:PutObject"],
             "Resource": f"arn:aws:s3:::{BUCKET}/artifacts/*"},
            {"Sid": "UseShellDocument", "Effect": "Allow", "Action": "ssm:SendCommand",
             "Resource": f"arn:aws:ssm:{REGION}::document/AWS-RunShellScript"},
            {"Sid": "DeployLabInstance", "Effect": "Allow", "Action": "ssm:SendCommand",
             "Resource": f"arn:aws:ec2:{REGION}:{ACCOUNT}:instance/*",
             "Condition": {"StringEquals": {"ssm:resourceTag/Project": "income-lab"}}},
            {"Sid": "ReadDeploymentResult", "Effect": "Allow",
             "Action": "ssm:GetCommandInvocation", "Resource": "*"},
        ]},
    }
    for name, policy in policies.items():
        iam.put_role_policy(RoleName=name, PolicyName="income-lab-scoped", PolicyDocument=json.dumps(policy))
    iam.attach_role_policy(RoleName=EC2_ROLE, PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")
    try:
        profile = iam.get_instance_profile(InstanceProfileName=EC2_ROLE)["InstanceProfile"]
    except iam.exceptions.NoSuchEntityException:
        profile = iam.create_instance_profile(InstanceProfileName=EC2_ROLE)["InstanceProfile"]
    if not profile["Roles"]:
        iam.add_role_to_instance_profile(InstanceProfileName=EC2_ROLE, RoleName=EC2_ROLE)
    save_state(bucket=BUCKET, region=REGION, ci_role_arn=f"arn:aws:iam::{ACCOUNT}:role/{CI_ROLE}", instance_profile=EC2_ROLE)


def instance(sess):
    ec2 = sess.client("ec2")
    existing = ec2.describe_instances(Filters=[
        {"Name": "tag:Project", "Values": ["income-lab"]},
        {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
    ])
    instances = [i for r in existing["Reservations"] for i in r["Instances"]]
    if instances:
        assert len(instances) == 1, "More than one lab instance; inspect before continuing"
        save_state(instance_id=instances[0]["InstanceId"], public_ip=instances[0].get("PublicIpAddress"))
        return
    ami = sess.client("ssm").get_parameter(
        Name="/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
    )["Parameter"]["Value"]
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
    assert len(vpcs) == 1, "Expected one default VPC"
    vpc_id = vpcs[0]["VpcId"]
    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
    subnet = sorted(subnets, key=lambda s: s["AvailabilityZone"])[0]
    groups = ec2.describe_security_groups(Filters=[
        {"Name": "vpc-id", "Values": [vpc_id]}, {"Name": "group-name", "Values": ["income-api-sg"]}
    ])["SecurityGroups"]
    if groups:
        sg = groups[0]["GroupId"]
    else:
        sg = ec2.create_security_group(
            GroupName="income-api-sg", Description="Income API from student IP only", VpcId=vpc_id,
            TagSpecifications=[{"ResourceType": "security-group", "Tags": [{"Key": "Project", "Value": "income-lab"}]}],
        )["GroupId"]
    response = requests.get("https://api.ipify.org", timeout=20)
    response.raise_for_status()
    client_ip = str(ipaddress.IPv4Address(response.text.strip()))
    try:
        ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[{
            "IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080,
            "IpRanges": [{"CidrIp": f"{client_ip}/32", "Description": "Student lab API test"}],
        }])
    except ec2.exceptions.ClientError as exc:
        if exc.response["Error"]["Code"] != "InvalidPermission.Duplicate":
            raise
    image = ec2.describe_images(ImageIds=[ami])["Images"][0]
    launched = ec2.run_instances(
        ImageId=ami, InstanceType="t3.micro", MinCount=1, MaxCount=1,
        IamInstanceProfile={"Name": EC2_ROLE},
        NetworkInterfaces=[{"DeviceIndex": 0, "SubnetId": subnet["SubnetId"],
                            "Groups": [sg], "AssociatePublicIpAddress": True}],
        BlockDeviceMappings=[{"DeviceName": image["RootDeviceName"],
                              "Ebs": {"VolumeSize": 8, "VolumeType": "gp3", "Encrypted": True, "DeleteOnTermination": True}}],
        MetadataOptions={"HttpTokens": "required", "HttpEndpoint": "enabled"},
        CreditSpecification={"CpuCredits": "standard"},
        TagSpecifications=[{"ResourceType": "instance", "Tags": [
            {"Key": "Name", "Value": "income-api"}, {"Key": "Project", "Value": "income-lab"},
        ]}],
        ClientToken="income-lab-20261007",
    )["Instances"][0]
    save_state(instance_id=launched["InstanceId"], security_group=sg, ami=ami)


def status(sess):
    state = json.loads(STATE.read_text())
    instance_id = state["instance_id"]
    node = sess.client("ec2").describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
    managed = sess.client("ssm").describe_instance_information(
        Filters=[{"Key": "InstanceIds", "Values": [instance_id]}]
    )["InstanceInformationList"]
    save_state(public_ip=node.get("PublicIpAddress"), instance_state=node["State"]["Name"],
               ssm_status=managed[0]["PingStatus"] if managed else "not registered")


def deploy(sess):
    state = json.loads(STATE.read_text())
    package = ROOT.parent / "aws-cli-session" / "income-api-source.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in ["src/__init__.py", "src/serve.py", "deploy/requirements-serving.txt", "deploy/income-api.service.template"]:
            archive.write(ROOT / relative, relative)
    sess.client("s3").upload_file(str(package), BUCKET, "deploy/income-api-source.zip")
    command = sess.client("ssm").send_command(
        InstanceIds=[state["instance_id"]], DocumentName="AWS-RunShellScript",
        TimeoutSeconds=1200,
        Parameters={"commands": [
            "set -eu",
            "export DEBIAN_FRONTEND=noninteractive",
            "apt-get update -qq",
            "apt-get install -y -qq python3-venv python3-pip unzip awscli",
            "mkdir -p /home/ubuntu/income-lab /home/ubuntu/models",
            f"aws s3 cp s3://{BUCKET}/deploy/income-api-source.zip /tmp/income-api-source.zip --region {REGION}",
            "unzip -oq /tmp/income-api-source.zip -d /home/ubuntu/income-lab",
            "cd /home/ubuntu/income-lab",
            "python3 -m venv .venv",
            ".venv/bin/python -m pip install --quiet -r deploy/requirements-serving.txt",
            f"printf 'ARTIFACT_BUCKET={BUCKET}\\nAWS_REGION={REGION}\\n' > .env",
            "chown -R ubuntu:ubuntu /home/ubuntu/income-lab /home/ubuntu/models",
            "sed 's/USER_NAME/ubuntu/g' deploy/income-api.service.template > /etc/systemd/system/income-api.service",
            "systemctl daemon-reload",
            "systemctl enable income-api",
            "systemctl restart income-api",
            "for attempt in $(seq 1 24); do if curl --fail --silent http://127.0.0.1:8080/healthz; then exit 0; fi; sleep 5; done",
            "journalctl -u income-api --no-pager -n 40; exit 1",
        ]},
        Comment="Install and start Day21 income API",
    )["Command"]
    save_state(deploy_command_id=command["CommandId"])


def result(sess):
    state = json.loads(STATE.read_text())
    output = sess.client("ssm").get_command_invocation(
        CommandId=state["deploy_command_id"], InstanceId=state["instance_id"],
    )
    print(json.dumps({key: output.get(key) for key in ["Status", "ResponseCode", "StandardOutputContent", "StandardErrorContent"]}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["roles", "instance", "status", "deploy", "result"])
    args = parser.parse_args()
    globals()[args.action](session())


if __name__ == "__main__":
    main()
