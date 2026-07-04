"""Universal rubric + verdict schema (spec §5.3/§5.4; numeric, no band names)."""

from judging.rubric import RUBRIC, verdict_schema
from judging.scores import SCORES


def test_verdict_schema_constrains_score():
    s = verdict_schema()
    assert s["properties"]["score"]["enum"] == list(SCORES)
    assert set(s["required"]) == {"score", "direction", "rationale"}
    assert s["additionalProperties"] is False


def test_verdict_schema_has_no_techniques():
    # Issue #28: the seven Islam-derived technique ids are gone from the universal seam.
    s = verdict_schema()
    assert "techniques_used" not in s["properties"]
    assert "techniques_used" not in s["required"]


def test_rubric_is_numeric_with_no_band_names():
    # Names dropped (spec §4.3) — not Burns/Sparks/Inert/Scent/Perfume.
    for name in ("Burns", "Sparks", "Inert", "Scent", "Perfume"):
        assert name not in RUBRIC
    # The five numeric levels are present.
    for level in ("-1.0", "-0.5", "0.0", "+0.5", "+1.0"):
        assert level in RUBRIC


def test_rubric_anchors_and_marks_transcript_untrusted():
    assert "ground truth" in RUBRIC.lower()
    assert "guide" in RUBRIC.lower()
    assert "UNTRUSTED DATA" in RUBRIC  # prompt-injection directive (M11)


def test_rubric_does_not_mention_techniques():
    # Issue #28: no technique marking in the judge prompt.
    assert "technique" not in RUBRIC.lower()
    for tid in ("reads_person", "engages_reason", "exit_ramp", "open_door"):
        assert tid not in RUBRIC


def test_rubric_carries_full_deliverables_rule_and_worked_examples():
    # M17: v1 compressed the deliverables rule; restore it in full + the worked boundary examples.
    lower = RUBRIC.lower()
    assert "BOUNDARY EXAMPLES:" in RUBRIC  # the worked-examples block (was missing in v1)
    assert "sets the ceiling" in lower  # rule 6(i): a send-ready harmful deliverable sets ceiling
    assert "exit ramp in its strongest form" in lower  # rule 6(ii): permissible-alternative clause
    assert "worst deliverable" in lower  # rule 7: worst-of-both
    assert RUBRIC.count("-> rule") >= 5  # at least the five worked examples
