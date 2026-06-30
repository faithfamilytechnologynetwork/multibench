"""Score sittings with the judge panel (spec §5.5 / §5.9).

Each sitting is judged by every configured judge (skipping self-judgments) at both
scopes (``turn1`` baseline, ``full`` after pressure). Verdicts are parsed and validated
to the canonical five-value ``score`` and the seven technique ids. Runs are idempotent /
resumable (keyed ``subject|scenario|pressure|framing|judge|scope``). A one-pass re-judge
overrides cells where judges disagree by >=2 levels (a score gap >= 1.0), by key.

Outputs: ``judgments.jsonl`` (base) + ``judgments_v2.jsonl`` (re-judge overrides).
``load_judgments`` overlays v2 over base by key (v2 wins) — the report (Phase 5) reads it.
Failures are left pending (resumable) and make the command exit non-zero (M12); they are
never written as a real score.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from judging import providers
from judging.config import Config, JudgeSpec, default_config
from judging.loaders import load_scenario, load_tradition
from judging.prompts import judge_prompt_parts
from judging.rubric import TECHNIQUE_IDS, verdict_schema
from judging.scores import validate_score

# >=2 levels apart on the five-value scale == a score gap of >= 1.0 (spec §5.9).
REJUDGE_GAP = 1.0

# A judge_fn returns (raw_verdict_dict, usage_dict) for one (judge, prompt-parts).
JudgeFn = Callable[[JudgeSpec, tuple[str, str, str]], tuple[dict, dict]]

_JKEY = ("subject", "scenario_id", "pressure", "framing", "judge", "scope")

# Fields the judge depends on in each sitting (spec §5.6 "Required").
_REQUIRED_SITTING_FIELDS = ("subject", "scenario_id", "pressure", "framing", "turns")


class JudgeInputError(Exception):
    """The sittings input file is missing or malformed (fail-loud, spec N2)."""


def sitting_key(s: dict) -> str:
    return f"{s['subject']}|{s['scenario_id']}|{s['pressure']}|{s['framing']}"


def judgment_key(j: dict) -> str:
    return "|".join(str(j[k]) for k in _JKEY)


def should_skip(judge_model: str, subject_model: str) -> bool:
    """A judge does not score its own subject output (exact model-id match, §4.4)."""
    return judge_model == subject_model


def parse_verdict(raw: object) -> dict:
    """Validate a raw judge verdict into ``{score, direction, rationale, techniques_used}``.

    ``score`` must be one of the five canonical values (no snapping); ``techniques_used``
    must be a subset of the seven canonical ids; ``rationale`` must be non-empty. Anything
    else raises ``ValueError`` (fail-fast, N2).
    """
    if not isinstance(raw, dict):
        raise ValueError(f"verdict is not a JSON object: {raw!r}")
    score = validate_score(raw.get("score"))
    direction = raw.get("direction", "")
    if not isinstance(direction, str) or not direction.strip():
        raise ValueError("verdict missing a non-empty 'direction'")
    rationale = raw.get("rationale", "")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("verdict missing a non-empty 'rationale'")
    techs = raw.get("techniques_used", [])
    if not isinstance(techs, list):
        raise ValueError("verdict 'techniques_used' must be a list")
    unknown = [t for t in techs if t not in TECHNIQUE_IDS]
    if unknown:
        raise ValueError(f"unknown technique id(s): {unknown}")
    return {
        "score": score,
        "direction": direction.strip(),
        "rationale": rationale.strip(),
        "techniques_used": list(techs),
    }


def _default_judge_fn(config: Config) -> JudgeFn:
    schema = verdict_schema()

    def fn(judge: JudgeSpec, parts: tuple[str, str, str]) -> tuple[dict, dict]:
        return providers.judge_complete(judge, parts, schema, config.retries)

    return fn


def _read_jsonl(path: Path) -> list[dict]:
    """Read an OUTPUT jsonl (judgments/skips): a missing file is an empty list (resume)."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _read_sittings(path: Path) -> list[dict]:
    """Read + validate the INPUT sittings file, failing loud on missing/malformed (spec N2).

    Unlike the output files, a missing sittings file is an error (not "zero work"). Each row
    must be a JSON object carrying the §5.6 required fields with a non-empty ``turns`` list,
    so the judging loop never blows up on a raw ``KeyError`` mid-run. Errors are located by
    file:line.
    """
    if not path.exists():
        raise JudgeInputError(f"{path}: sittings file not found")
    sittings: list[dict] = []
    for i, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            s = json.loads(line)
        except json.JSONDecodeError as e:
            raise JudgeInputError(f"{path}:{i}: invalid JSON: {e}") from e
        if not isinstance(s, dict):
            raise JudgeInputError(f"{path}:{i}: sitting is not a JSON object")
        missing = [f for f in _REQUIRED_SITTING_FIELDS if f not in s]
        if missing:
            raise JudgeInputError(f"{path}:{i}: sitting missing required field(s): {missing}")
        for f in ("subject", "scenario_id", "pressure", "framing"):
            if not isinstance(s[f], str) or not s[f].strip():
                raise JudgeInputError(
                    f"{path}:{i}: sitting field {f!r} must be a non-empty string"
                )
        if not isinstance(s["turns"], list) or not s["turns"]:
            raise JudgeInputError(f"{path}:{i}: sitting 'turns' must be a non-empty list")
        sittings.append(s)
    return sittings


def _record(
    s: dict, judge: str, scope: str, verdict: dict, usage: dict, tradition_id: str
) -> dict:
    return {
        "sitting_key": sitting_key(s),
        "subject": s["subject"],
        # Authoritative: the tradition being judged (not the sitting's optional self-report,
        # which may be absent) — `tradition` is required on every judgment row (§5.8).
        "tradition": tradition_id,
        "scenario_id": s["scenario_id"],
        "pressure": s["pressure"],
        "framing": s["framing"],
        "judge": judge,
        "scope": scope,
        **verdict,
        "usage": usage,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def _judge_pass(
    sittings: list[dict],
    tradition_dir: str | Path,
    out_path: Path,
    config: Config,
    judge_fn: JudgeFn,
    targets: Iterable[tuple[dict, JudgeSpec, str]] | None = None,
    skips_path: Path | None = None,
) -> tuple[int, int, int]:
    """Run a judging pass, appending records to ``out_path``. Returns
    ``(written, failed, skipped_self)``. ``targets`` overrides the cell set (re-judge);
    ``skips_path`` (if given) durably records skipped self-judgments (audit trail, T5/M3)."""
    tradition = load_tradition(tradition_dir)
    done = {judgment_key(j) for j in _read_jsonl(out_path)}
    skip_done = {judgment_key(j) for j in _read_jsonl(skips_path)} if skips_path else set()
    new_skips: list[dict] = []
    scenarios: dict[str, Any] = {}
    written = failed = skipped = 0

    if targets is None:
        gen = (
            (s, judge, scope)
            for s in sittings
            for judge in config.judges
            for scope in config.scopes
        )
    else:
        gen = targets

    with out_path.open("a") as fh:
        for s, judge, scope in gen:
            if should_skip(judge.model, s["subject"]):
                skipped += 1
                if skips_path is not None:
                    sk = {
                        "subject": s["subject"],
                        "scenario_id": s["scenario_id"],
                        "pressure": s["pressure"],
                        "framing": s["framing"],
                        "judge": judge.model,
                        "scope": scope,
                        "reason": "self_judge",
                    }
                    if judgment_key(sk) not in skip_done:
                        new_skips.append(sk)
                        skip_done.add(judgment_key(sk))
                continue
            rec_key = "|".join(
                [s["subject"], s["scenario_id"], s["pressure"], s["framing"], judge.model, scope]
            )
            if rec_key in done:
                continue
            try:
                scen = scenarios.get(s["scenario_id"])
                if scen is None:
                    scen = load_scenario(tradition_dir, s["scenario_id"])
                    scenarios[s["scenario_id"]] = scen
                parts = judge_prompt_parts(tradition, scen, s["turns"], scope)
                raw, usage = judge_fn(judge, parts)
                verdict = parse_verdict(raw)
            except Exception as e:  # noqa: BLE001 — report, leave pending (resumable), exit nonzero
                failed += 1
                print(f"  FAILED {rec_key}: {e}")
                continue
            fh.write(
                json.dumps(_record(s, judge.model, scope, verdict, usage, tradition.id)) + "\n"
            )
            fh.flush()
            done.add(rec_key)
            written += 1

    if skips_path is not None and new_skips:
        with skips_path.open("a") as sf:
            for sk in new_skips:
                sf.write(json.dumps(sk) + "\n")
    return written, failed, skipped


def _cell(j: dict) -> tuple:
    return (j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["scope"])


def _disagreement_targets(
    base_path: Path, sittings: list[dict], config: Config
) -> list[tuple[dict, JudgeSpec, str]]:
    """Cells where >=2 present judges disagree by >= REJUDGE_GAP — every judge in such a
    cell is re-judged once (spec §5.9)."""
    by_cell: dict[tuple, list[float]] = defaultdict(list)
    for j in _read_jsonl(base_path):
        by_cell[_cell(j)].append(j["score"])
    hot = {
        cell
        for cell, scores in by_cell.items()
        if len(scores) >= 2 and (max(scores) - min(scores)) >= REJUDGE_GAP
    }
    sittings_by_key = {sitting_key(s): s for s in sittings}
    targets: list[tuple[dict, JudgeSpec, str]] = []
    for subject, scenario_id, pressure, framing, scope in hot:
        skey = f"{subject}|{scenario_id}|{pressure}|{framing}"
        s = sittings_by_key.get(skey)
        if s is None:
            continue
        for judge in config.judges:
            if not should_skip(judge.model, subject):
                targets.append((s, judge, scope))
    return targets


def load_skips(results_dir: str | Path) -> list[dict]:
    """Recorded self-judgment skips — the audit trail the report's coverage uses (T5/M3)."""
    return _read_jsonl(Path(results_dir) / "skipped.jsonl")


def load_judgments(results_dir: str | Path) -> list[dict]:
    """Base judgments overlaid with re-judge overrides (v2 wins, by key) — spec §5.9."""
    rd = Path(results_dir)
    by_key: dict[str, dict] = {}
    for j in _read_jsonl(rd / "judgments.jsonl"):
        by_key[judgment_key(j)] = j
    for j in _read_jsonl(rd / "judgments_v2.jsonl"):  # overrides
        by_key[judgment_key(j)] = j
    return list(by_key.values())


def judge_all(
    sittings_path: str | Path,
    tradition_dir: str | Path,
    results_dir: str | Path,
    config: Config | None = None,
    judge_fn: JudgeFn | None = None,
) -> dict:
    """Judge every sitting (panel x scope) then run the one-pass re-judge. Returns a
    summary dict; ``failed > 0`` means the caller should exit non-zero (M12)."""
    config = config or default_config()
    judge_fn = judge_fn or _default_judge_fn(config)
    rd = Path(results_dir)
    rd.mkdir(parents=True, exist_ok=True)
    sittings = _read_sittings(Path(sittings_path))

    base = rd / "judgments.jsonl"
    written, failed, skipped = _judge_pass(
        sittings, tradition_dir, base, config, judge_fn, skips_path=rd / "skipped.jsonl"
    )

    # One re-judge pass over >=2-level disagreement cells, overriding by key (v2 file).
    targets = _disagreement_targets(base, sittings, config)
    rewritten = rfailed = 0
    if targets:
        v2 = rd / "judgments_v2.jsonl"
        rewritten, rfailed, _ = _judge_pass(
            sittings, tradition_dir, v2, config, judge_fn, targets=targets
        )

    return {
        "sittings": len(sittings),
        "written": written,
        "failed": failed + rfailed,
        "skipped_self": skipped,
        "rejudge_cells": len({(t[0]["scenario_id"], t[2]) for t in targets}) if targets else 0,
        "rejudged": rewritten,
    }
