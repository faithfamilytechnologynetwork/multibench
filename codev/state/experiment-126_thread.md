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
- 2026-09-12: Hypothesis committed (64e76b5b), advanced to Design. Notified architect.
- 2026-09-12 Design prep (no spend):
  - **Context length VERIFIED from model config** (not memory): Gemma 4 31B
    `text_config.max_position_embeddings = 262144` (256k) → 49k window fine.
  - Copied #78 reuse files into experiments/126_prompt_fading_32k/. Deltas applied:
    collect_fading.py `LEVELS` += `L4:32000`, `--levels` default now `L4` (this run collects
    only L4; L0–L3 pooled from #78). serve copy → `--max-model-len 49152`, app renamed
    `multibench-gemma-fading-32k-serve` (keeps #78's endpoint intact).
  - **SCOPE decision (architect-approved):** live corpus GREW to 655/9 (protestantism +100,
    protestant-unified +36, specs 89/119) — no #78 L0–L3 → unpoolable → OUT of scope. Pinned
    126 manifest to a verbatim copy of #78's 519/7; guarded select_scenarios (regen reproduces
    519 byte-for-byte, verified). Architect confirmed: do not run the 2 Protestant modules.
  - **analyze.py rewritten** for the 5-level pool: loads #78 per_scenario_78.csv (L0–L3) +
    this run's L4 judgments; FaithfulBench tiers (low/med/high, mean-of-tradition-means);
    primary L3→L4 change + A1−B diff, secondary 5-level slopes / total L0→L4 vs τ / immunity;
    writes summary_126.json + per_scenario_126.csv (5 levels, #78 columns) + 5-level figures.
  - **Analyzer validated end-to-end on synthetic full-coverage L4 (zero spend):** pools 519/7,
    and the pooled L0–L3 means reproduce #78's Results table EXACTLY (continuity check passes).
    All scripts compile in their uv venvs.
  - **fluff_bank.md extended + AUDITED.** Subagent drafted 102 new exchanges (172.8k chars);
    I read ALL 102 in full + ran two banned-content keyword screens (religion/spiritual,
    politics/violence/health, emotion/prescriptive/legal/relationship). PASS — every exchange is
    strictly value-neutral (physics/chem/bio-mechanics/astronomy/earth-sci/meteorology/food-sci/
    tech/mechanisms/timekeeping/cartography/math/acoustics); keyword hits were benign idioms
    ("by virtue of being hot", storms that "weaken and die", cooking "should/must"). Assembled:
    original 20 first (strict prefix) + 102 new = 122 exchanges, ~47k approx tokens. Verified via
    the collector's own build_fluff: **L4 → 32,358 tok, 88 exchanges, cycled=False** (no repeat).
  - Design/pre-registration COMPLETE and committed before any data. Advancing to Execute → smoke.
- SMOKE PLAN (execute): deploy serve (49k), collect RC ×2 scenarios ×2 pressures ×2 arms ×L4 =
  8 sittings, judge, then STOP → reconcile usage-computed actuals + throughput projection →
  architect go before any full run. Keys: export ONLY OPENROUTER+ANTHROPIC from
  /Users/mwk/Development/fftn/taqwabench/.env (never GEMINI — key-seam scar).
- 2026-09-12 SMOKE DONE (8 sittings, 8 judgments, 0 failures) — PASS:
  - Window fit: max gen input 28,846 tok << 49,152 (real tokens < chars/4 estimate for prose).
  - Zero leakage (turns = clean 4-turn dilemma); arm→subject/level→framing survive; both arms
    served correctly (A1 guide, B stated from stated_prompt()).
  - EXACT banding: \$0.1015/8 = \$0.01268/judgment (RC upper bound). Serve ~\$1.5-2 (coldstart 292s
    engine init + 10-min scaledown). Smoke total ~\$1.6-2.1 (within \$1-2).
  - **Prefix caching 75-87%**: all sittings share the identical system+32k-fluff prefix → 32k
    prefill amortized (prefilled once per arm). Big favorable cost lever.
  - Warm: 8 sittings/~40s @ conc8 = ~720/h. FULL-RUN PROJECTION: banding ~\$82 + serve ~\$15-50
    (conc-dependent; prefix-cached prefill → should approach #78's 2540/h @ conc64) = **~\$97-133**
    all-in vs \$200 ceiling; Modal well under \$80 tripwire.
  - Directional preview (sanity only, n=2): A1 @L4 mean +0.00 vs B +1.00 (consistent w/ #78 H3).
  - GOTCHA for full run: judge writes judgments.jsonl DIRECTLY into --results-dir, so judge
    PER-TRADITION with --results-dir data/output/<tradition> (moved the smoke's flat file into RC).
- **STOPPED at smoke per protocol.** Sent architect actuals + projection. AWAITING EXPLICIT GO
  before the full run. Serve app deployed & idle (scale-to-zero): multibench-gemma-fading-32k-serve.
