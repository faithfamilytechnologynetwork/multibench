"""Matplotlib figure tests (spec T7/S1): figures write both formats, a non-default
--fig-format is honored, the colormap matches the HTML score_color, and the HTML
path stays matplotlib-free. Skips cleanly when matplotlib is not installed.
"""

import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from analysis.cli import app

matplotlib = pytest.importorskip("matplotlib")  # T7: skip if the 'figures' extra is absent

FIX = Path(__file__).resolve().parent / "fixtures"
runner = CliRunner()


def _load_pairs():
    from analysis.aggregate import aggregate_tradition
    from analysis.loaders import load_run_dir
    from analysis.stats import compute_tradition_stats

    aggs = [aggregate_tradition(load_run_dir(FIX / t)) for t in ("buddhism", "taoism")]
    stats = [compute_tradition_stats(a, n_boot=100, seed=12345) for a in aggs]
    return aggs, stats


def test_emit_figures_writes_all_figures_both_formats(tmp_path):
    from analysis.figures import emit_figures

    aggs, stats = _load_pairs()
    written = emit_figures(aggs, stats, tmp_path, ["pdf", "png"])
    names = {"scorecard", "framing", "steadfastness", "distribution"}
    for name in names:
        assert (tmp_path / f"{name}.pdf").is_file()
        assert (tmp_path / f"{name}.png").is_file()
    assert len(written) == len(names) * 2


def test_non_default_fig_format_writes_only_requested(tmp_path):
    from analysis.figures import emit_figures

    aggs, stats = _load_pairs()
    emit_figures(aggs, stats, tmp_path, ["png"])
    assert (tmp_path / "scorecard.png").is_file()
    assert not (tmp_path / "scorecard.pdf").exists()


def test_bad_format_rejected(tmp_path):
    from analysis.figures import emit_figures

    aggs, stats = _load_pairs()
    with pytest.raises(ValueError, match="unsupported figure format"):
        emit_figures(aggs, stats, tmp_path, ["svg"])


def test_band_color_endpoints_match_html_score_color():
    # F3/D1/D2: the matplotlib colormap and the HTML score_color share the same stops.
    # Endpoints are exact; the centre may differ by matplotlib's 256-level LUT quantization.
    from analysis.colors import score_color
    from analysis.figures import band_color

    def rgb(h):
        return [int(h[i:i + 2], 16) for i in (1, 3, 5)]

    def hexrgb(rgba):
        return "#" + "".join(f"{round(c * 255):02X}" for c in rgba[:3])

    def close(a_hex, b_hex, tol):
        return all(abs(x - y) <= tol for x, y in zip(rgb(a_hex), rgb(b_hex)))

    assert close(hexrgb(band_color(-1.0)), score_color(-1.0), 0)  # endpoint: exact
    assert close(hexrgb(band_color(1.0)), score_color(1.0), 0)    # endpoint: exact
    assert close(hexrgb(band_color(0.0)), score_color(0.0), 2)    # centre: LUT quantization


def test_cli_figures_flag_writes_figures_dir(tmp_path):
    out = tmp_path / "o"
    r = runner.invoke(
        app,
        ["report", str(FIX / "buddhism"), str(FIX / "taoism"), "--out", str(out),
         "--figures", "--n-boot", "100", "--fig-format", "png"],
    )
    assert r.exit_code == 0, r.output
    assert (out / "report.html").is_file()
    figs = list((out / "figures").glob("*.png"))
    assert {p.stem for p in figs} == {"scorecard", "framing", "steadfastness", "distribution"}
    assert not list((out / "figures").glob("*.pdf"))  # only png requested


def test_html_path_does_not_import_matplotlib(tmp_path):
    # The default (no --figures) path must never import matplotlib (spec §7.3 / D7).
    out = tmp_path / "o"
    # Run in a subprocess so we observe a clean import graph.
    import subprocess

    code = (
        "import sys, subprocess;"
        "from typer.testing import CliRunner; from analysis.cli import app;"
        f"r=CliRunner().invoke(app,['report',{str(FIX / 'buddhism')!r},'--out',{str(out)!r},'--n-boot','50']);"
        "assert r.exit_code==0, r.output;"
        "assert 'matplotlib' not in sys.modules, 'HTML path must not import matplotlib';"
        "print('ok')"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "ok" in proc.stdout
