# experiment-126 thread — prompt fading at 32k (L4, fifth level on the #78 ramp)

**Builder:** experiment-126 (soft mode, EXPERIMENT protocol)
**Issue:** #126 — add ONE level (L4 ≈ 32,000 tokens filler) to the #78 five... four-level ramp,
both arms, full 519-scenario corpus. Pool with committed #78 data → 5-level ramp.
**Ceiling:** est ≈ $140, **HARD $200**. Modal tripwire $80.

## Phase machine (porch experiment protocol)
hypothesis → design → execute → analyze → gate `experiment-complete`.
Single porch gate at the end. The load-bearing STOP is a *spend gate I own in soft mode*:
after the SMOKE (8 sittings), reconcile usage-computed actuals + throughput projection and
report to the architect — **full run only on explicit human go**.

## Design in one line
Inherit #78 wholesale (collect_fading.py, judge config, arms A1/B, seed + pre-reg discipline).
The ONE delta: add level **L4 = ~32,000 tokens** of filler. Everything else byte-identical.
Grid: 519 × 6 pressures × 2 arms = **6,228 sittings + 6,228 judgments** at L4.

## Log
- 2026-09-11: Spawned. Read issue #126 + #78 notes.md/collect/fluff/config in full.
  Confirmed #78 CSV schema `tradition,scenario,arm,level,score` (levels 0–3, 4152 rows).
  Fluff bank = 20 exchanges ≈ 4,805 approx tokens (chars/4) → need ~113 NEW value-neutral
  exchanges to fill 32k non-repeating, original 20 kept first as a strict prefix.
  Starting Hypothesis phase: writing pre-registration notes.md.
