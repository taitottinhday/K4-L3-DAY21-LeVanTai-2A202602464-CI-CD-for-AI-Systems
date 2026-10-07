"""The same quality rule is used locally, in CI, and before promotion."""

import argparse
import json
import math

F1_THRESHOLD = 0.65


def check_quality(f1: float, previous_f1: float | None = None) -> None:
    if not math.isfinite(f1) or not 0 <= f1 <= 1:
        raise ValueError("f1_score must be a finite number in [0, 1]")
    if f1 < F1_THRESHOLD:
        raise ValueError(f"Quality gate failed: F1 {f1:.4f} < {F1_THRESHOLD:.2f}")
    if previous_f1 is not None:
        if not math.isfinite(previous_f1) or not 0 <= previous_f1 <= 1:
            raise ValueError("Previous f1_score is invalid")
        if f1 < previous_f1:
            raise ValueError(f"Promotion blocked: F1 {f1:.4f} < previous {previous_f1:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="outputs/report.json")
    parser.add_argument("--f1", type=float)
    args = parser.parse_args()
    if args.f1 is None:
        with open(args.report, encoding="utf-8") as file:
            f1 = float(json.load(file)["f1_score"])
    else:
        f1 = args.f1
    try:
        check_quality(f1)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(f"Quality gate passed: F1={f1:.4f} >= {F1_THRESHOLD:.2f}")
