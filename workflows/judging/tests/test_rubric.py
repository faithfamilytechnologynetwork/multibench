"""Universal rubric + verdict schema (spec §5.3/§5.4; numeric, no band names)."""

from judging.rubric import RUBRIC, TECHNIQUE_IDS, verdict_schema
from judging.scores import SCORES


def test_seven_canonical_technique_ids():
    assert TECHNIQUE_IDS == (
        "reads_person",
        "engages_reason",
        "gentleness",
        "gradualism",
        "exit_ramp",
        "proportion",
        "open_door",
    )


def test_verdict_schema_constrains_score_and_techniques():
    s = verdict_schema()
    assert s["properties"]["score"]["enum"] == list(SCORES)
    assert s["properties"]["techniques_used"]["items"]["enum"] == list(TECHNIQUE_IDS)
    assert set(s["required"]) == {"score", "direction", "rationale", "techniques_used"}
    assert s["additionalProperties"] is False


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
    # All seven technique ids are listed for the model.
    for tid in TECHNIQUE_IDS:
        assert tid in RUBRIC
