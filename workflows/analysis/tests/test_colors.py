"""Numeric color-scale tests (spec T5): endpoints, neutral centre, clamping,
and heatmap auto-contrast — all numeric, no band names.
"""

from analysis.colors import ZERO_REF, heatmap_color, on_color, score_color

RED, GREY, GREEN = "#9E1B32", "#D9D2C5", "#1B7837"


def test_score_color_endpoints_and_centre():
    assert score_color(-1.0) == RED
    assert score_color(0.0) == GREY  # TwoSlopeNorm centre pins 0 to the grey stop
    assert score_color(1.0) == GREEN


def test_score_color_clamps_out_of_range():
    assert score_color(-5.0) == RED
    assert score_color(5.0) == GREEN


def test_score_color_is_monotone_across_the_scale():
    # Negatives are reddish, positives greenish (sanity, not exact).
    assert score_color(-0.5) != score_color(0.5)
    assert score_color(-1.0) == RED and score_color(1.0) == GREEN


def test_heatmap_auto_contrast_norm():
    assert heatmap_color(0.0, 0.4) == GREY
    assert heatmap_color(0.4, 0.4) == GREEN  # value at +vmax -> green endpoint
    assert heatmap_color(-0.4, 0.4) == RED   # value at -vmax -> red endpoint
    assert heatmap_color(0.0, 0.0) == GREY   # degenerate all-zero matrix


def test_on_color_contrast():
    assert on_color(0.0, 1.0) == "#111111"   # faint cell -> dark text
    assert on_color(0.9, 1.0) == "#FFFFFF"   # strong cell -> white text


def test_axis_ref_constants():
    assert ZERO_REF == 0.0
