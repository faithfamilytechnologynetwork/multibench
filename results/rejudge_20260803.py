"""Reproducible re-judge tooling for the `20260803` grid completion (issue #120, Phase 1).

Enumerates the cells missing an Opus verdict across the four source roots, builds a **filtered**
sittings file per (tradition, framing-group) containing ONLY those sittings, and prints the exact
`judging judge` commands to run plus the pre-spend work-count. It never spends: it writes filtered
sittings and prints commands; the human runs the printed `judge` commands with the CEFE Opus judge
key. This is the permanent, executable record behind `results/REJUDGE-20260803.md`.

Why filtered sittings + a work-count: `judging judge` scores a WHOLE sittings.jsonl (no cell
targeting); handing it a full merged file would judge ~21,840 cells (hundreds of USD) with no
error. Feeding only the missing sittings + asserting the work-count bounds the spend.

Routing (roots spell subjects differently and hold different framings):
  unstated       transcripts <- 20260803-merged (canonical ids); verdicts -> 20260803-unstated-opus
  stated/guided  transcripts <- 20260823-opus-fullgrid (provider slugs); verdicts -> same root

Run from the repo root (source roots live under tmp/judging-runs/; from a builder worktree they are
at ../../tmp/judging-runs/):

    uv --project workflows/analysis run python results/rejudge_20260803.py --runs tmp/judging-runs
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from analysis.export_results import normalize_subject, read_run_root, resolve_judgments

_OPUS = "claude-opus-4-8"
_ROOT_NAMES = (
    "20260803-merged", "20260803-unstated-opus",
    "20260803-framings-opus-sample", "20260823-opus-fullgrid",
)


def missing_opus_sittings(runs: Path) -> dict[tuple[str, str], set[tuple]]:
    """(tradition, group) -> set of missing sitting keys (norm_subject, scenario, pressure, framing).

    A group is 'unstated' or 'stated_guided'. A sitting is missing if any of its cells lacks an
    Opus verdict across the four roots (resolved with root-order precedence)."""
    per = [read_run_root(str(runs / n)) for n in _ROOT_NAMES]
    traditions = sorted({t for root in per for t in root})
    out: dict[tuple[str, str], set[tuple]] = collections.defaultdict(set)
    for t in traditions:
        present = [(i, root[t]) for i, root in enumerate(per) if t in root]
        rows = resolve_judgments([rt for _i, rt in present], [i for i, _rt in present])
        cells: dict[tuple, set[str]] = collections.defaultdict(set)
        for j in rows:
            cells[(j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["scope"])].add(j["judge"])
        for c, judges in cells.items():
            if _OPUS not in judges:
                grp = "unstated" if c[3] == "unstated" else "stated_guided"
                out[(t, grp)].add((c[0], c[1], c[2], c[3]))
    return out


_SCOPES = ("turn1", "full")


def _existing_rec_keys(judgments_path: Path) -> set[str]:
    """The judge's resume keys already present in a target layer: subject|scenario|pressure|framing|model|scope."""
    keys: set[str] = set()
    if not judgments_path.is_file():
        return keys
    for line in judgments_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        j = json.loads(line)
        parts = [j["subject"], j["scenario_id"], j["pressure"], j["framing"], j["judge"], j["scope"]]
        keys.add("|".join(parts))
    return keys


def work_count(runs: Path, tradition: str, group: str, filtered_lines: list[str],
               model: str = _OPUS) -> int:
    """The judge's ACTUAL post-resume work: filtered (sitting x scope) cells NOT already judged in
    the target layer — exactly what `judge` will bill. This is the pre-spend guard (mirrors
    `_judge_pass`'s rec_key + resume set); asserting it bounds the spend precisely.
    """
    dst_root = "20260803-unstated-opus" if group == "unstated" else "20260823-opus-fullgrid"
    done = _existing_rec_keys(runs / dst_root / tradition / "judgments.jsonl")
    work = 0
    for line in filtered_lines:
        s = json.loads(line)
        for scope in _SCOPES:
            k = "|".join([s["subject"], s["scenario_id"], s["pressure"], s["framing"], model, scope])
            if k not in done:
                work += 1
    return work


def _load_sittings(path: Path) -> dict[tuple, str]:
    """Key sittings by NORMALIZED subject (merged=canonical, fullgrid=slugs); emit the line verbatim."""
    idx: dict[tuple, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        s = json.loads(line)
        idx[(normalize_subject(s["subject"]), s["scenario_id"], s["pressure"], s["framing"])] = line
    return idx


def build(runs: Path, out_dir: Path, config: str, assert_work: int | None = None) -> int:
    """Write one filtered sittings file per (tradition, group), print each judge command, and
    compute the ACTUAL post-resume work count (cells the judge will bill). Returns that total
    work count; with ``assert_work`` set, raises unless it matches — the pre-spend guard.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    miss = missing_opus_sittings(runs)
    total_work = 0
    blocks: list[str] = []
    for (t, grp), keys in sorted(miss.items()):
        src_root = "20260803-merged" if grp == "unstated" else "20260823-opus-fullgrid"
        dst_root = "20260803-unstated-opus" if grp == "unstated" else "20260823-opus-fullgrid"
        idx = _load_sittings(runs / src_root / t / "sittings.jsonl")
        # Resolve transcripts BEFORE writing anything; raise on any absent (raise-before-write).
        lines: list[str] = []
        absent: list[tuple] = []
        for k in sorted(keys):
            (lines.append(idx[k]) if k in idx else absent.append(k))
        if absent:
            raise SystemExit(f"ERROR {t}/{grp}: transcripts absent in {src_root}: {absent}")
        out = out_dir / f"{t}__{grp}.sittings.jsonl"
        out.write_text("\n".join(lines) + ("\n" if lines else ""))
        work = work_count(runs, t, grp, lines)
        total_work += work
        blocks.append(
            f"# {t}/{grp}: {len(lines)} sittings, {work} post-resume cells -> {dst_root}/{t}/\n"
            f"uv --project workflows/judging run python -m judging judge \\\n"
            f"  {out} traditions/{t} \\\n"
            f"  --results-dir {runs}/{dst_root}/{t} --config {config}\n"
        )
    print("# filtered sittings + judge commands (run each with the CEFE Opus judge key):\n")
    print("\n".join(blocks))
    print(f"# TOTAL post-resume work (cells the judge will bill = pre-spend bound): {total_work}")
    print("# BACK UP each target judgments.jsonl before running (in-place append, gitignored source).")
    if assert_work is not None and total_work != assert_work:
        raise SystemExit(
            f"PRE-SPEND GUARD FAILED: work={total_work} != expected {assert_work} — do NOT run judge.")
    return total_work


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="tmp/judging-runs", help="dir holding the four source roots")
    ap.add_argument("--out", default="tmp/rejudge-120/filtered-sittings", help="filtered-sittings output dir")
    ap.add_argument("--config", default="tmp/opus-judge.yaml",
                    help="Opus judge config path (from a builder worktree: ../../tmp/opus-judge.yaml)")
    ap.add_argument("--assert-work", type=int, default=None,
                    help="pre-spend guard: fail unless the post-resume work count equals this")
    a = ap.parse_args()
    build(Path(a.runs), Path(a.out), a.config, a.assert_work)
