"""The universal core is reused, not forked (spec M9)."""

import tradition_validator.core as tv_core

from judging import core_imports


def test_reexports_are_the_same_objects_as_core():
    # Identity, not just equality: we re-export, we don't redefine.
    assert core_imports.FRAMINGS is tv_core.FRAMINGS
    assert core_imports.PRESSURES is tv_core.PRESSURES
    assert core_imports.STATED_TEMPLATE is tv_core.STATED_TEMPLATE
    assert core_imports.IDENTITY_SIGNALS is tv_core.IDENTITY_SIGNALS
    assert core_imports.normalize_heading is tv_core.normalize_heading
    assert core_imports.stated_prompt is tv_core.stated_prompt


def test_framings_and_pressures_values():
    assert core_imports.FRAMINGS == ("unstated", "stated", "guided")
    assert core_imports.PRESSURES == (
        "secularize",
        "insistence",
        "false_authority",
        "good_cause",
        "flattery",
        "personal_appeal",
    )
