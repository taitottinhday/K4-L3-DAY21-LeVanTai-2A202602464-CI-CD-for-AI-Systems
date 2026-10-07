"""Call a running API and save verifiable local HTTP results."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--output", default="nop-bai/api-local.json")
    args = parser.parse_args()
    cases = [
        ("GET", "/healthz", None, 200, {"status": "ok"}),
        ("POST", "/score", [60, 2, 5, 2, 4, 0, 1, 0, 0, 45], 200,
         {"prediction": 0, "label": "thu_nhap_thap"}),
        ("POST", "/score", [28, 2, 14, 2, 11, 0, 1, 0, 0, 45], 200,
         {"prediction": 1, "label": "thu_nhap_cao"}),
        ("POST", "/score", [1, 2], 400, None),
    ]
    results = []
    for method, route, features, expected_status, expected_body in cases:
        payload = None if features is None else {"features": features}
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(args.base_url.rstrip("/") + route, data=data, method=method,
                          headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            status = response.code
            body = json.loads(response.read())
        assert status == expected_status, (status, body)
        if expected_body is not None:
            assert body == expected_body, body
        result = {"method": method, "url": request.full_url, "request": payload,
                  "status": status, "response": body}
        results.append(result)
        print(json.dumps(result, ensure_ascii=False))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "environment": "local (not Cloud VM evidence)",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
