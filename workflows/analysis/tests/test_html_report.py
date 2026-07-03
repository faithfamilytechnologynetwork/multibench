"""HTML report tests (spec T5/T6/T6b + M10): numeric-only, self-contained,
injection-safe, deterministic, and the CLI writes the fixed output contract.
"""

import dataclasses
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from analysis.aggregate import aggregate_tradition
from analysis.cli import app
from analysis.html_report import esc, render_report
from analysis.loaders import load_run_dir
from analysis.stats import compute_tradition_stats

FIX = Path(__file__).resolve().parent / "fixtures"
BAND_NAMES = ("Burns", "Sparks", "Inert", "Scent", "Perfume")
runner = CliRunner()


@pytest.fixture(scope="module")
def rendered():
    aggs, stats = [], []
    for t in ("buddhism", "taoism"):
        agg = aggregate_tradition(load_run_dir(FIX / t))
        aggs.append(agg)
        stats.append(compute_tradition_stats(agg, n_boot=300, seed=12345))
    return render_report(aggs, stats)


# --- T5: numeric only, no band names -----------------------------------------

def test_no_band_names(rendered):
    for name in BAND_NAMES:
        assert name not in rendered, f"band name {name!r} must not appear (numeric only)"


def test_shows_ci_whiskers_and_gap_columns(rendered):
    assert "whisker" in rendered  # scorecard CI whiskers
    assert "recognition (S−U)" in rendered and "instruction (G−S)" in rendered


def test_steadfastness_cis_displayed():
    # M4: steadfastness CIs must be displayed, not just computed. The heatmap table twin
    # renders each cell as "point [lo, hi]" and the SVG cells carry the CI on hover.
    from analysis.html_report import _fci

    agg = aggregate_tradition(load_run_dir(FIX / "buddhism"))
    st = compute_tradition_stats(agg, n_boot=300, seed=12345)
    html = render_report([agg], [st])
    s = agg.subjects[0]
    pooled_ci = _fci(st.per_subject[s].steadfastness)
    assert pooled_ci in html, "pooled steadfastness CI must appear in the report"
    # a per-pressure steadfastness CI too
    some_pressure_ci = _fci(next(iter(st.per_subject[s].steadfastness_by_pressure.values())))
    assert some_pressure_ci in html


def test_is_full_html5_document(rendered):
    assert rendered.startswith("<!DOCTYPE html>")
    assert '<meta charset="utf-8"/>' in rendered
    assert "<title>" in rendered and "</html>" in rendered


def test_sections_present(rendered):
    for heading in ("tradition gradient", "framing staircase", "Steadfastness by pressure",
                    "Score distributions", "Judge agreement"):
        assert heading in rendered
    assert "Technique profile" not in rendered  # dropped from the seam (issue #28)


# --- T6: self-contained (no external asset loads) ----------------------------

def test_self_contained_no_external_assets(rendered):
    assert "<script" not in rendered.lower()  # no JS context at all
    assert "://" not in rendered              # no http(s)/protocol-relative asset URLs
    assert "<img" not in rendered.lower()
    # no external stylesheet/src references
    assert not re.search(r'(?:src|href)\s*=', rendered, re.IGNORECASE)


# --- T6b: injection safety ---------------------------------------------------

def test_esc_neutralizes_payload():
    out = esc('</script><img src=x onerror=alert(1)>&"')
    assert "<img" not in out and "</script>" not in out
    assert "&lt;" in out and "&amp;" in out


def test_artifact_text_is_escaped_in_report():
    payload = '</script><img src=x onerror=alert(1)>'
    agg = aggregate_tradition(load_run_dir(FIX / "buddhism"))
    agg = dataclasses.replace(agg, tradition=payload)
    stats = compute_tradition_stats(
        aggregate_tradition(load_run_dir(FIX / "buddhism")), n_boot=100, seed=12345
    )
    html = render_report([agg], [stats])
    assert payload not in html                 # never rendered raw
    assert "&lt;/script&gt;" in html           # rendered as escaped literal text
    assert "<img" not in html.lower()


# --- determinism / byte-stability --------------------------------------------

def test_render_is_deterministic():
    aggs = [aggregate_tradition(load_run_dir(FIX / t)) for t in ("buddhism", "taoism")]
    stats = [compute_tradition_stats(a, n_boot=200, seed=7) for a in aggs]
    assert render_report(aggs, stats) == render_report(aggs, stats)


# --- CLI: fixed output contract (M10) + byte-stable runs ---------------------

def test_cli_report_writes_contract_and_is_byte_stable(tmp_path):
    out1 = tmp_path / "run1"
    args = ["report", str(FIX / "buddhism"), str(FIX / "taoism"), "--out", str(out1),
            "--n-boot", "200", "--seed", "12345"]
    r1 = runner.invoke(app, args)
    assert r1.exit_code == 0, r1.output
    assert (out1 / "report.html").is_file()
    assert (out1 / "analysis_stats.json").is_file()
    html = (out1 / "report.html").read_text()
    assert "<script" not in html.lower() and "://" not in html

    # Re-run into a fresh dir with the same seed → byte-identical outputs (determinism).
    out2 = tmp_path / "run2"
    r2 = runner.invoke(app, [a if a != str(out1) else str(out2) for a in args])
    assert r2.exit_code == 0
    assert (out2 / "report.html").read_bytes() == (out1 / "report.html").read_bytes()
    assert (out2 / "analysis_stats.json").read_bytes() == (out1 / "analysis_stats.json").read_bytes()


def test_cli_idempotent_overwrite(tmp_path):
    out = tmp_path / "o"
    args = ["report", str(FIX / "buddhism"), "--out", str(out), "--n-boot", "100"]
    assert runner.invoke(app, args).exit_code == 0
    first = (out / "report.html").read_bytes()
    assert runner.invoke(app, args).exit_code == 0  # overwrite in place
    assert (out / "report.html").read_bytes() == first


def test_cli_bad_run_dir_fails_loudly(tmp_path):
    r = runner.invoke(app, ["report", str(tmp_path / "does-not-exist"), "--out", str(tmp_path / "o")])
    assert r.exit_code == 2
