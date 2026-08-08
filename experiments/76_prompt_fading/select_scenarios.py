"""Experiment 76 — seeded, stratified scenario selection.

Picks N scenarios per tradition (default 6) from all traditions under ``traditions/``, seeded
(seed 3446, the project's standing seed) so the sample is reproducible and committed BEFORE any
data. Writes ``data/output/scenarios.json`` = ``{tradition_id: [scenario_id, ...]}`` (sorted).

Run:
  uv --project workflows/judging run python experiments/76_prompt_fading/select_scenarios.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import typer

from judging.loaders import load_tradition

app = typer.Typer(add_completion=False)

SEED = 3446
REPO_ROOT = Path(__file__).resolve().parents[2]


@app.command()
def main(
    traditions_dir: Path = typer.Option(REPO_ROOT / "traditions", help="traditions/ root"),
    out: Path = typer.Option(
        Path(__file__).resolve().parent / "data" / "output" / "scenarios.json"
    ),
    per_tradition: int = typer.Option(6, help="scenarios sampled per tradition"),
    seed: int = typer.Option(SEED),
) -> None:
    trad_ids = sorted(p.parent.name for p in traditions_dir.glob("*/tradition.yaml"))
    if not trad_ids:
        raise typer.Exit(f"no traditions found under {traditions_dir}")

    rng = random.Random(seed)
    selection: dict[str, list[str]] = {}
    for tid in trad_ids:
        trad = load_tradition(traditions_dir / tid)
        ids = sorted(trad.scenario_ids)  # sort first -> selection independent of index.json order
        if len(ids) < per_tradition:
            raise typer.Exit(f"{tid}: only {len(ids)} scenarios (< {per_tradition})")
        selection[tid] = sorted(rng.sample(ids, per_tradition))

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "seed": seed,
        "per_tradition": per_tradition,
        "traditions": trad_ids,
        "total": sum(len(v) for v in selection.values()),
        "scenarios": selection,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out} — {payload['total']} scenarios across {len(trad_ids)} traditions (seed {seed})")
    for tid in trad_ids:
        print(f"  {tid}: {selection[tid]}")


if __name__ == "__main__":
    app()
