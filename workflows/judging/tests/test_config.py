"""Default configuration (spec §5.7; architect-confirmed defaults)."""

from judging.config import (
    DEFAULT_JUDGES,
    DEFAULT_SUBJECTS,
    SCOPES,
    default_config,
)


def test_default_judge_panel_is_opus_plus_gemini_flash():
    assert [j.model for j in DEFAULT_JUDGES] == ["claude-opus-4-8", "gemini-3.5-flash"]
    by_provider = {j.provider: j for j in DEFAULT_JUDGES}
    assert set(by_provider) == {"anthropic", "gemini"}
    # Gemini judge runs safety-off (judging only); both think.
    assert by_provider["gemini"].safety_off is True
    assert by_provider["anthropic"].safety_off is False
    assert all(j.thinking for j in DEFAULT_JUDGES)


def test_default_subjects_are_claude_only():
    # Minimal Claude-only collector (spec §4.5).
    assert all(s.provider == "anthropic" for s in DEFAULT_SUBJECTS)
    assert [s.model for s in DEFAULT_SUBJECTS] == [
        "claude-opus-4-8",
        "claude-sonnet-4-6",
    ]
    # Subjects are never safety-off — there is no such field to flip on a subject.
    assert all(s.thinking is False for s in DEFAULT_SUBJECTS)


def test_config_defaults():
    c = default_config()
    assert c.framings == ("unstated", "stated", "guided")
    assert len(c.pressures) == 6
    assert c.scopes == SCOPES == ("turn1", "full")
    assert c.results_dir == "results"
