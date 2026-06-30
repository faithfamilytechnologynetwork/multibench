"""Scoring-scale tests (spec T1, T2; §4.2/§5.3/§5.9)."""

import pytest

from judging.scores import SCORES, is_valid_score, mean, validate_score


def test_scores_are_the_five_canonical_values():
    assert SCORES == (-1.0, -0.5, 0.0, 0.5, 1.0)


@pytest.mark.parametrize("value", [-1.0, -0.5, 0.0, 0.5, 1.0, -1, 0, 1])
def test_validate_accepts_canonical_values(value):
    # T1: a verdict score must be one of the five values.
    assert validate_score(value) in SCORES


@pytest.mark.parametrize(
    "value", [0.7, 3, -2, 2, 0.25, 1.5, -0.75, "1", "0.5", None, True, False]
)
def test_validate_rejects_non_canonical_values(value):
    # T2: anything off the five-value grid is a hard error (no snapping).
    assert not is_valid_score(value)
    with pytest.raises(ValueError):
        validate_score(value)


def test_mean_is_unweighted_on_minus1_to_plus1():
    # T15: two scores +1.0 and 0.0 -> +0.5.
    assert mean([1.0, 0.0]) == 0.5
    assert mean([-1.0, -0.5, 0.0, 0.5, 1.0]) == 0.0
    assert mean([-1.0, -1.0]) == -1.0


def test_mean_of_empty_is_none_not_zero():
    # §5.9: an uncovered cell has no score — None, never 0.0.
    assert mean([]) is None
