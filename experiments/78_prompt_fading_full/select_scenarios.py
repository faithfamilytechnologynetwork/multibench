"""Experiment 78 — scenario manifest (full corpus, or seeded-capped fallback).

Writes ``data/output/scenarios.json`` = ``{tradition_id: [scenario_id, ...]}`` (sorted), committed
BEFORE any data. Two modes, chosen by the architect's grid ruling:

- ``--mode all`` (Option A, DEFAULT): enumerate ALL scenario_ids in every tradition. No draw — the
  sample-size and easy-draw concerns disappear by construction. This is the issue's stated intent
  ("ALL scenarios, no draw").
- ``--mode capped`` (Option B fallback): keep the ``--full-traditions`` (default the powered normative
  claims roman-catholicism + sunni-islam) FULL, and take a seeded stratified sample of the remaining
  traditions so the grand total is ``--cap-total`` (default 366). Seed 3446 (the project's standing
  seed), reproducible.

Run:
  uv --project workflows/judging run python experiments/78_prompt_fading_full/select_scenarios.py --mode all
  uv --project workflows/judging run python experiments/78_prompt_fading_full/select_scenarios.py --mode capped --cap-total 366
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
    mode: str = typer.Option("all", help="'all' (Option A) or 'capped' (Option B)"),
    traditions_dir: Path = typer.Option(REPO_ROOT / "traditions", help="traditions/ root"),
    out: Path = typer.Option(
        Path(__file__).resolve().parent / "data" / "output" / "scenarios.json"
    ),
    full_traditions: str = typer.Option(
        "roman-catholicism,sunni-islam",
        help="capped mode: traditions kept FULL (the powered per-tradition claims)",
    ),
    cap_total: int = typer.Option(366, help="capped mode: target grand total across all traditions"),
    seed: int = typer.Option(SEED),
) -> None:
    if mode not in ("all", "capped"):
        raise typer.Exit(f"unknown mode {mode!r} (use 'all' or 'capped')")

    trad_ids = sorted(p.parent.name for p in traditions_dir.glob("*/tradition.yaml"))
    if not trad_ids:
        raise typer.Exit(f"no traditions found under {traditions_dir}")

    ids_by_trad: dict[str, list[str]] = {}
    for tid in trad_ids:
        trad = load_tradition(traditions_dir / tid)
        ids_by_trad[tid] = sorted(trad.scenario_ids)  # sort -> selection independent of index order

    selection: dict[str, list[str]]
    if mode == "all":
        selection = {tid: list(ids_by_trad[tid]) for tid in trad_ids}
    else:
        full = [t.strip() for t in full_traditions.split(",") if t.strip()]
        for t in full:
            if t not in ids_by_trad:
                raise typer.Exit(f"full-tradition {t!r} not found (known: {trad_ids})")
        selection = {t: list(ids_by_trad[t]) for t in full}
        kept_full = sum(len(v) for v in selection.values())
        remaining_budget = cap_total - kept_full
        others = [t for t in trad_ids if t not in full]
        pool_total = sum(len(ids_by_trad[t]) for t in others)
        if remaining_budget <= 0:
            raise typer.Exit(
                f"full traditions already total {kept_full} >= cap {cap_total}; raise --cap-total"
            )
        if remaining_budget > pool_total:
            raise typer.Exit(
                f"cap {cap_total} needs {remaining_budget} from a pool of only {pool_total}"
            )
        # Proportional per-tradition quota (largest-remainder), then seeded sample within each.
        rng = random.Random(seed)
        raw = {t: remaining_budget * len(ids_by_trad[t]) / pool_total for t in others}
        quota = {t: int(raw[t]) for t in others}
        leftover = remaining_budget - sum(quota.values())
        for t in sorted(others, key=lambda t: raw[t] - int(raw[t]), reverse=True)[:leftover]:
            quota[t] += 1
        for t in others:
            selection[t] = sorted(rng.sample(ids_by_trad[t], quota[t]))

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "seed": seed if mode == "capped" else None,
        "traditions": trad_ids,
        "total": sum(len(v) for v in selection.values()),
        "scenarios": {tid: selection[tid] for tid in trad_ids},
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out} — mode={mode}, {payload['total']} scenarios across {len(trad_ids)} traditions")
    for tid in trad_ids:
        print(f"  {tid}: {len(selection[tid])} scenarios")


if __name__ == "__main__":
    app()
