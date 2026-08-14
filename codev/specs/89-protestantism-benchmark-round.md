# Spec 89 — ProtestantBench benchmark round

## What

Run the full MultiBench benchmark round on the `protestantism` tradition (100 scenarios,
PRO-001..PRO-100, landed in #82, validator-strict clean) and publish the results as a committed,
browsable dataset tier — score tier (`results/`) + raw tier (`results-raw/`) — that the
multibrowser SPA discovers at runtime.

## Why

ProtestantBench is a newly authored normative tradition; it needs to be scored under the same
benchmark-of-record convention as the 20260803 run so its subjects are comparable to the other
seven traditions, and so the `/results` explorer can surface it (leaderboard + per-scenario raw
transcripts/verdicts).

## Success criteria

- **Roster + convention derived from the real 20260803 record**, not docs: the same 5 subject
  models, the dual-judge pair (Gemini ranking, full grid + Opus validation, badge-only), the three
  universal framings, the six pressures, both scopes.
- **Full battery**: 100 scenarios × 5 subjects × 6 pressures × 3 framings collected; Gemini judges
  the full grid; Opus provides validation coverage.
- **Exported tiers** under a new run-id, **additive** — `20260803` stays byte-for-byte untouched
  (it is guarded by the paper-reconciliation test and is a fixed 7/519 snapshot).
- **Spend disciplined**: smoke first → reconcile usage-computed actuals → architect go → hard
  ceiling honored; per-key spend reported.
- Coverage reported **honestly** in the manifest (no silent zeros); partial Opus is a smaller badge,
  never a re-rank.

## Constraints / baked decisions

- **Keys**: subjects + Gemini judge via `OPENROUTER_API_KEY`; Opus judge via an Anthropic key.
  Sourced only from `taqwabench/.env`. Never a personal Gemini key.
- **Never mutate `results/20260803`**; propose the integration shape (new-run-id vs superset) at the
  smoke checkpoint. (Chosen: new run-id `20260813-protestantism`, superset deferred.)
- **Budget** governed by an architect-set hard ceiling with alert + pause tripwires.
- The judge seam is each scenario's `judge-guidance.md`; no proof-text corpus.

## Open questions (resolved during the run)

- Opus coverage shape (full grid vs validation sample) — resolved to **full-grid intent, batched**;
  in practice landed at **46 % validation** due to an Anthropic org usage cap, with a backfill plan.
- Integration shape — resolved to **new run-id, protestantism-only**.
