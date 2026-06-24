"""One-time migration: JaleesBench data -> ``traditions/sunni-islam/`` (canonical format).

Reads a staged JaleesBench source tree (``probes.json`` + ``prompts.py`` + ``mapping.py``;
see Spec §3.3b — fetch via ``gh api`` into a gitignored ``tmp/jaleesbench-source/``) and
writes the file-based tradition: ``tradition.yaml`` + prose + one folder per scenario.

Run from the repo root:

    uv --project apps/tradition_validator run python -m tradition_validator.port_jaleesbench \\
        --source tmp/jaleesbench-source --out traditions/sunni-islam

The JaleesBench source is read with ``ast`` (no code execution): ``prompts.py`` and
``mapping.py`` are parsed and the needed constants resolved from literals.
"""

from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import typer
import yaml

from tradition_validator import core

SOURCE_MD = """\
# Source — Riyāḍ al-Ṣāliḥīn

The canonical source for the Sunni Islam tradition is **Riyāḍ al-Ṣāliḥīn**
("Gardens of the Righteous") by Imām al-Nawawī (d. 676 AH) — a topical compilation of
~372 chapters (abwāb) on character and conduct, each pairing Qurʾānic verses with curated
hadith.

## Why it is consensus-grade

- **Overwhelmingly Bukhārī/Muslim material** — the two most rigorously authenticated hadith
  collections; where weaker narrations appear, published gradings are applied as a filter.
- **Read across schools and regions** — from Morocco to Malaysia, it is one of the most
  widely taught adab/akhlāq texts, which keeps the bench out of live scholarly disputes by
  construction.
- **Ships its own ground truth** — each chapter carries the Qurʾān-and-hadith proof texts
  the judge is anchored to. In this format those live per scenario in `judge-guidance.md`, so
  the judge never supplies its own jurisprudence.
- **Inward before outward** — the book opens with sincerity of intention, the same ordering
  this construct adopts.

Ported from JaleesBench (github.com/iaser-ai/jaleesbench).
"""

README_MD = """\
# Sunni Islam

The first MultiBench tradition, in the canonical file-based format (ported from JaleesBench,
github.com/iaser-ai/jaleesbench).

- **Construct:** *al-jalīs al-ṣāliḥ* (the righteous companion) — judged by the residue an
  exchange leaves on the user, in the manner of the prophetic hadith of the perfume-seller
  and the blacksmith.
- **Canonical source:** *Riyāḍ al-Ṣāliḥīn* (al-Nawawī) — see [`source.md`](source.md).
- **Guide:** the Guided-framing companionship guide is in [`guide.md`](guide.md).
- **Scenarios:** scenario folders under [`scenarios/`](scenarios/), each with `scenario.yaml`,
  `turn1.md`, `judge-guidance.md`, and `pressures.md` (one section per core pressure).

Framings (unstated / stated / guided) and the six pressures are universal core; the only
faith-specific framing inputs here are `adherent_noun` (Stated) and `guide.md` (Guided).

Validate from the repo root:

```bash
uv --project apps/tradition_validator run python -m tradition_validator validate traditions/sunni-islam
```
"""

def _resolve(node: ast.AST, env: dict) -> object:
    """Resolve a constant expression node to a Python value (literals + Name + str/`+`)."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return [_resolve(e, env) for e in node.elts]
    if isinstance(node, ast.Dict):
        return {_resolve(k, env): _resolve(v, env) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _resolve(node.left, env) + _resolve(node.right, env)
    raise ValueError(f"unsupported expression: {ast.dump(node)[:80]}")


def extract_constants(src: str) -> dict:
    """ast-parse module source and resolve simple top-level constant assignments."""
    env: dict = {}
    for node in ast.parse(src).body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            try:
                env[node.targets[0].id] = _resolve(node.value, env)
            except (ValueError, KeyError, TypeError):
                continue  # skip non-constant assignments (functions, computed exprs)
    return env


def port(
    source: Path = typer.Option(..., help="Staged JaleesBench source dir."),
    out: Path = typer.Option(..., help="Output tradition dir (e.g. traditions/sunni-islam)."),
) -> None:
    """Generate the Sunni Islam tradition from the staged JaleesBench source."""
    bank = json.loads((source / "probes.json").read_text(encoding="utf-8"))
    prompts_env = extract_constants((source / "prompts.py").read_text(encoding="utf-8"))
    mapping_env = extract_constants((source / "mapping.py").read_text(encoding="utf-8"))

    guide = prompts_env["GUIDE"]
    stated = prompts_env["STATED"]
    pillars = sorted(mapping_env["PILLARS"])
    hearts = sorted(mapping_env["HEARTS"])
    if "Muslim" not in stated:
        raise typer.BadParameter("STATED prompt did not contain 'Muslim'; check the source.")

    manifest = {
        "id": "sunni-islam",
        "schema_version": 1,
        "display_name": "Sunni Islam",
        "construct": (
            "al-jalīs al-ṣāliḥ — the righteous companion, judged by the residue an "
            "exchange leaves on the user (hadith of the perfume-seller and the blacksmith)."
        ),
        "canonical_source": {
            "title": "Riyāḍ al-Ṣāliḥīn",
            "author": "al-Nawawī",
            "locus_unit": "bab",
        },
        "adherent_noun": "Muslim",
        "maintainers": [
            {"name": "MultiBench maintainers", "contact": "github.com/iaser-ai/jaleesbench"}
        ],
        "scholar_review": {"status": "none", "reviewers": []},
        "taxonomies": {
            "pillars": {
                "description": "Conduct pillars (Ibn al-Qayyim, Madārij al-Sālikīn)",
                "applies_to": "scenario",
                "values": pillars,
            },
            "hearts": {
                "description": "Heart states / saving virtues (al-Ghazālī, Iḥyāʾ ʿUlūm al-Dīn)",
                "applies_to": "response",
                "values": hearts,
            },
        },
        "scenario_id_pattern": r"^JLS-\d{3}$",
    }

    out.mkdir(parents=True, exist_ok=True)
    (out / "tradition.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    (out / "source.md").write_text(SOURCE_MD, encoding="utf-8")
    (out / "README.md").write_text(README_MD, encoding="utf-8")
    (out / "guide.md").write_text(guide.rstrip() + "\n", encoding="utf-8")

    scenarios_dir = out / "scenarios"
    shutil.rmtree(scenarios_dir, ignore_errors=True)  # deterministic regen
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    ids: list[str] = []
    for p in bank["probes"]:
        pid = p["id"]
        ids.append(pid)
        folder = scenarios_dir / pid
        folder.mkdir(parents=True, exist_ok=True)
        meta = {
            "id": pid,
            "tags": {"pillars": p["pillars"], "hearts": p["hearts"]},
            "source_locus": p["bab"],
            "locus_label": p["chapter"],
            "identity_signal": p["islamic"],
        }
        (folder / "scenario.yaml").write_text(
            yaml.safe_dump(meta, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        (folder / "turn1.md").write_text(p["turn1"].rstrip() + "\n", encoding="utf-8")
        (folder / "judge-guidance.md").write_text(
            p["proof_texts"].rstrip() + "\n", encoding="utf-8"
        )
        sections = [f"## {pr}\n\n{p['pressure_turns'][pr].rstrip()}\n" for pr in core.PRESSURES]
        (folder / "pressures.md").write_text("\n".join(sections), encoding="utf-8")

    (scenarios_dir / "index.json").write_text(
        json.dumps({"schema_version": 1, "scenarios": sorted(ids)}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    typer.echo(f"ported {len(ids)} scenarios -> {out}")


if __name__ == "__main__":  # pragma: no cover
    typer.run(port)
