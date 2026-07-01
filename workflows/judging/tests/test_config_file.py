"""Config-file overrides (spec §5.7): a YAML file overrides defaults field-by-field, fails
loud on bad shapes (N2), and — threaded into ``report`` — makes coverage counts correct for
non-default panels/scopes (the standalone-report coverage bug).
"""

import json

import pytest
import yaml
from typer.testing import CliRunner

from judging.cli import app
from judging.config import ConfigError, default_config, load_config
from judging.report import build_report

runner = CliRunner()


def _write(tmp_path, obj):
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(obj), encoding="utf-8")
    return p


def test_load_config_overrides_only_present_keys(tmp_path):
    cfg = load_config(_write(tmp_path, {"framings": ["unstated"], "retries": 0}))
    assert cfg.framings == ("unstated",)
    assert cfg.retries == 0  # 0 is valid (no retry)
    # Untouched keys keep their defaults.
    assert cfg.subjects == default_config().subjects
    assert cfg.scopes == default_config().scopes


def test_load_config_builds_judge_and_subject_specs(tmp_path):
    cfg = load_config(
        _write(
            tmp_path,
            {
                "judges": [{"model": "claude-opus-4-8", "provider": "anthropic"}],
                "subjects": [{"model": "claude-opus-4-8"}],  # provider defaults to anthropic
            },
        )
    )
    assert [j.model for j in cfg.judges] == ["claude-opus-4-8"]
    assert cfg.judges[0].thinking is True  # judge default
    assert cfg.subjects[0].provider == "anthropic"


@pytest.mark.parametrize(
    "obj,needle",
    [
        ({"nope": 1}, "unknown config key"),
        ({"judges": [{"model": "m", "provider": "anthropic", "bad": 1}]}, "unknown judge key"),
        ({"judges": [{"model": "m", "provider": "openai"}]}, "provider must be one of"),
        ({"judges": []}, "non-empty list"),
        ({"framings": ["made-up"]}, "unknown framings value"),
        ({"pressures": ["not-a-pressure"]}, "unknown pressures value"),
        ({"retries": -1}, "non-negative integer"),
        ({"concurrency": 0}, "positive integer"),
        ({"subjects": [{"model": ""}]}, "non-empty string"),
        ({"judges": [{"model": "m", "provider": "anthropic", "thinking": "yes"}]}, "must be a boolean"),
    ],
)
def test_load_config_fails_loud(tmp_path, obj, needle):
    with pytest.raises(ConfigError) as ei:
        load_config(_write(tmp_path, obj))
    assert needle in str(ei.value)


def test_load_config_missing_file(tmp_path):
    with pytest.raises(ConfigError) as ei:
        load_config(tmp_path / "nope.yaml")
    assert "not found" in str(ei.value)


def test_load_config_non_mapping(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ConfigError) as ei:
        load_config(p)
    assert "must be a mapping" in str(ei.value)


def test_report_coverage_uses_supplied_config_not_defaults(sunni, tmp_path):
    # The standalone-report coverage bug: with a non-default single-judge/single-scope config,
    # expected coverage must reflect THAT config, not default_config()'s 2 judges x 2 scopes.
    from judging.config import Config, JudgeSpec, SubjectSpec

    (tmp_path / "sittings.jsonl").write_text(
        json.dumps(
            {
                "subject": "claude-sonnet-4-6",
                "scenario_id": "JLS-001",
                "pressure": "secularize",
                "framing": "unstated",
                "turns": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    cfg = Config(
        subjects=(SubjectSpec("claude-sonnet-4-6"),),
        judges=(JudgeSpec("judge-x", "anthropic"),),
        scopes=("full",),
    )
    # With the supplied config: 1 judge x 1 scope over 1 sitting -> 1 expected cell.
    assert build_report(tmp_path, sunni, cfg)["counts"]["expected_cells"] == 1
    # With defaults (2 judges, neither == the sonnet subject, x 2 scopes) -> 4. The bug was
    # reporting 4 for artifacts actually produced under the single-judge config.
    assert build_report(tmp_path, sunni)["counts"]["expected_cells"] == 4


def test_cli_report_accepts_config_file(sunni, tmp_path):
    cfg = _write(tmp_path, {"judges": [{"model": "judge-x", "provider": "anthropic"}], "scopes": ["full"]})
    (tmp_path / "judgments.jsonl").write_text(
        json.dumps(
            {
                "sitting_key": "s|JLS-001|secularize|unstated",
                "subject": "s",
                "tradition": "sunni-islam",
                "scenario_id": "JLS-001",
                "pressure": "secularize",
                "framing": "unstated",
                "judge": "judge-x",
                "scope": "full",
                "score": 1.0,
                "direction": "d",
                "rationale": "r",
                "techniques_used": [],
                "usage": {},
                "ts": "t",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["report", str(sunni), "--results-dir", str(tmp_path), "--config", str(cfg)]
    )
    assert result.exit_code == 0, result.output


def test_cli_bad_config_exits_two(sunni, tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("judges: []\n", encoding="utf-8")
    result = runner.invoke(app, ["report", str(sunni), "--results-dir", str(tmp_path), "--config", str(bad)])
    assert result.exit_code == 2  # config error, distinct from a run failure (exit 1)
    assert "config error" in result.output
