# workflows/judging

The MultiBench **judging** workflow: score an AI assistant's responses to a tradition's
scenarios — under the universal framings (unstated / stated / guided) and the six pressures —
against each scenario's `judge-guidance.md` (the binding ground truth), on the canonical
**−1…+1** scale (the five values `−1, −0.5, 0, +0.5, +1`).

- Spec: `codev/specs/8-workflows-judging-the-judging-.md`
- Plan: `codev/plans/8-workflows-judging-the-judging-.md`

```bash
uv --project workflows/judging run python -m judging --help
```

> Built phase by phase. The commands (`collect`, `judge`, `report`, `run`) are wired here and
> implemented across the plan's phases; full usage + the sittings/results contracts land in the
> final phase.
