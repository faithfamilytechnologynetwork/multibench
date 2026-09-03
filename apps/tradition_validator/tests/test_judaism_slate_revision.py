"""Regression guard for issue #111: Daniel Slate's judaism review corrections.

Expert reviewer Daniel Slate (Yeshiva/Kollel background) reviewed a 10-scenario sample
of the judaism module; his corrections were applied to ``guide.md`` and to the
``judge-guidance.md`` of MSR-010, MSR-015, MSR-020, and MSR-029 as a versioned revision
(the published ``20260803`` results were judged against the pre-revision guidance and are
unaffected — this is instrument integrity, not a score correction).

This test pins the load-bearing corrections so an accidental revert is caught, and
re-asserts that the real on-disk module still validates clean after the edits. It reads
the actual ``traditions/judaism`` tree (not a fixture), mirroring the other real-tradition
guards in this suite.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from tradition_validator.validator import validate_tradition

REPO_ROOT = Path(__file__).resolve().parents[3]
JUDAISM = REPO_ROOT / "traditions" / "judaism"


def _guide() -> str:
    return (JUDAISM / "guide.md").read_text(encoding="utf-8")


def _judge_guidance(scenario_id: str) -> str:
    return (JUDAISM / "scenarios" / scenario_id / "judge-guidance.md").read_text(
        encoding="utf-8"
    )


def test_module_still_validates_clean():
    """The edits keep the module valid (no errors, no warnings)."""
    report = validate_tradition(JUDAISM)
    assert report.ok(strict=True), report.render()


def test_scholar_review_credits_slate():
    """scholar_review records the expert reviewer and moves off 'none'."""
    manifest = yaml.safe_load((JUDAISM / "tradition.yaml").read_text(encoding="utf-8"))
    review = manifest["scholar_review"]
    assert review["status"] == "in_progress"
    assert "Daniel Slate" in review["reviewers"]


def test_readme_records_the_revision():
    """The README carries a Revisions note crediting the reviewer and preserving the
    provenance of the published results."""
    readme = (JUDAISM / "README.md").read_text(encoding="utf-8")
    assert "## Revisions" in readme
    assert "Daniel Slate" in readme
    # The published run was judged against the pre-revision guidance and is unaffected.
    assert "20260803" in readme


def test_guide_read_this_person_correction():
    """The 'read this person' paragraph drops the Prov 22:6 child-training framing and
    adds *yishuv ha-daat*."""
    guide = _guide()
    assert "yishuv ha-daat" in guide
    assert "help that one" in guide
    # The child-training framing (Prov 22:6, "al pi darko") was removed.
    assert "22:6" not in guide
    assert "al pi darko" not in guide


def test_msr010_matriarchs_rebuked_and_nechama_is_comfort():
    text = _judge_guidance("MSR-010")
    # The matriarchs are rebuked, not placed beyond reproach.
    assert "Gen 30:2" in text
    assert "Gen 18:13" in text
    # nechama is comfort that accepts grief, not manufactured/held hope.
    assert "does not manufacture hope" in text
    # Only Chana is cited for un-rebuked anger (Rachel's demand is rebuked).
    assert "Chana was not rebuked for hers" in text


def test_msr015_distancing_is_the_essence():
    text = _judge_guidance("MSR-015")
    assert "distancing is the essence of the command" in text
    # The weaker "mere distance" framing was removed.
    assert "mere *distance*" not in text


def test_msr020_leniency_authority_and_new_anchors():
    text = _judge_guidance("MSR-020")
    assert "Mishlei 24:16" in text
    # Teshuva / Hashem's love anchor.
    assert "teshuva" in text.lower()
    # The counsel may not grant a leniency it has no authority to grant.
    assert "no standing to grant" in text or "no authority to give" in text


def test_msr029_pinchas_permitted_but_untaught():
    text = _judge_guidance("MSR-029")
    assert "permitted-but-untaught" in text
    # Zealotry is a leniency no one may grant / be instructed into.
    assert "no one may hand out the Pinchas model" in text
