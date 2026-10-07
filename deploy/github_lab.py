"""Configure and inspect this repository using its existing Git credential."""

import argparse
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

import requests

REPO = "taitottinhday/K4-L3-DAY21-LeVanTai-2A202602464-CI-CD-for-AI-Systems"
ROOT = Path(__file__).resolve().parents[1]


def client():
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    credentials = subprocess.run(
        ["git", "-c", "credential.interactive=never", "credential", "fill"],
        input=f"url=https://github.com/{REPO}.git\n\n",
        text=True, capture_output=True, env=env, check=True,
    )
    values = dict(line.split("=", 1) for line in credentials.stdout.splitlines() if "=" in line)
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {values['password']}",
                            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    return session


def api(session, method, path, **kwargs):
    response = session.request(method, f"https://api.github.com/repos/{REPO}{path}", timeout=60, **kwargs)
    if not response.ok:
        raise RuntimeError(f"GitHub API {method} {path}: HTTP {response.status_code}: {response.text[:500]}")
    return response.json() if response.content else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["repo", "secrets", "runs", "jobs", "report", "logs"])
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--step", choices=["step2", "step3"])
    args = parser.parse_args()
    sess = client()
    if args.action == "repo":
        repo = api(sess, "GET", "")
        print(json.dumps({k: repo[k] for k in ["full_name", "private", "default_branch", "permissions"]}, indent=2))
    elif args.action == "secrets":
        from nacl import public, encoding
        state = json.loads((ROOT.parent / "aws-cli-session" / "resources.json").read_text())
        key = api(sess, "GET", "/actions/secrets/public-key")
        box = public.SealedBox(public.PublicKey(key["key"], encoding.Base64Encoder))
        values = {"ARTIFACT_BUCKET": state["bucket"], "AWS_ROLE_ARN": state["ci_role_arn"], "INSTANCE_ID": state["instance_id"]}
        for name, value in values.items():
            encrypted = base64.b64encode(box.encrypt(value.encode())).decode()
            api(sess, "PUT", f"/actions/secrets/{name}", json={"encrypted_value": encrypted, "key_id": key["key_id"]})
            print(f"Configured {name}")
        print(json.dumps(api(sess, "GET", "/actions/secrets"), indent=2))
    elif args.action == "runs":
        runs = api(sess, "GET", "/actions/runs?per_page=8")["workflow_runs"]
        print(json.dumps([{k: r[k] for k in ["id", "display_title", "event", "status", "conclusion", "head_sha", "html_url"]} for r in runs], indent=2))
    elif args.action == "jobs":
        jobs = api(sess, "GET", f"/actions/runs/{args.run_id}/jobs")["jobs"]
        print(json.dumps([{k: j[k] for k in ["id", "name", "status", "conclusion", "steps"]} for j in jobs], indent=2))
    elif args.action in {"report", "logs"}:
        assert args.run_id and args.step
        if args.action == "report":
            artifacts = api(sess, "GET", f"/actions/runs/{args.run_id}/artifacts")["artifacts"]
            artifact = next(a for a in artifacts if a["name"] == "report")
            response = sess.get(f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact['id']}/zip", timeout=60)
        else:
            response = sess.get(f"https://api.github.com/repos/{REPO}/actions/runs/{args.run_id}/logs", timeout=60)
        response.raise_for_status()
        folder = ROOT / "nop-bai" / "artifacts" / args.step
        folder.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for item in archive.infolist():
                target = (folder / item.filename).resolve()
                assert target.is_relative_to(folder.resolve()), "Unsafe archive path"
            archive.extractall(folder)
        print(f"Saved actual {args.action} from run {args.run_id} to {folder}")
        if args.action == "report":
            report = json.loads((folder / "report.json").read_text())
            print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
