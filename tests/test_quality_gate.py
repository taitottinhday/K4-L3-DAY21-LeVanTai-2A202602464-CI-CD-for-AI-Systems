import pytest

from src.quality_gate import check_quality


@pytest.mark.parametrize("f1", [0.65, 0.7149, 0.7354])
def test_gate_accepts_passing_models(f1):
    check_quality(f1)


@pytest.mark.parametrize("f1", [0.6051, 0.64, float("nan"), float("inf"), -1, 1.01])
def test_gate_rejects_bad_or_invalid_scores(f1):
    with pytest.raises(ValueError):
        check_quality(f1)


def test_promotion_blocks_regression():
    with pytest.raises(ValueError, match="Promotion blocked"):
        check_quality(0.70, 0.72)
    check_quality(0.72, 0.72)
    check_quality(0.74, 0.72)
