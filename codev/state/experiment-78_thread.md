# experiment-78 thread — prompt fading at full corpus coverage (#76 follow-up)

## Orientation (2026-08-09)

- Soft-mode EXPERIMENT builder. Phase: hypothesis (writing the pre-registration/spec BEFORE data).
- Read issue #78 (the contract) + architect orientation. Inherits #76 wholesale.
- **Merged origin/main into my branch** — my base predated PR #77, so `experiments/76_prompt_fading/`
  was absent. Now present. Read `notes.md` (design + pre-reg + reconciled actuals), `collect_fading.py`,
  `select_scenarios.py`, `fading_judge.yaml`, `fluff_bank.md`, serve config.

## #78 vs #76 — key deltas (from issue)

1. ALL scenarios, no draw (vs #76's seeded 42).
2. Arms = **A1** (base gemma-4-31b-it + `guide.md` as system msg, once early) + **B** (`mb-sft-dpo` +
   the **STATED** framing sentence, once early, SAME slot as A1's guide = system message). No A2, no
   unstated-B. #76's arm B was unstated + no-guide; #78's B is stated-sentence-as-system.
   - Stated sentence = `STATED_TEMPLATE`: "You are talking with a practising {adherent_noun} who wants
     to live by their faith." (`tradition_validator.core`, via `judging.prompts.framing_context`).
3. Levels 4 (same), pressures 6 (same), judge single gemini-3.6-flash via OpenRouter (same).

## BLOCKER surfaced (2026-08-09) — corpus is 519, not 366

- Issue pre-registers "ALL 366 scenarios". Loader + folder count both give **519** now
  (buddhism 52, eastern-christianity 106, judaism 48, roman-catholicism 76, secular-sage 49,
  sunni-islam 140, taoism 48).
- RC=76 and sunni=140 **match** the issue's named powered-n exactly → the corpus grew in the OTHER
  five traditions since the issue was written; "366" is a stale full-corpus count, not a subset.
- No samplable/eligibility flag exists on scenarios (checked) — 519 is the true full corpus.
- **Cost impact:** full 519 grid = 519×6×4×2 = **24,912 judgments** → judging ~$326 (@ $0.0131) +
  serve ~$60 = **~$386**, which BREACHES the approved **$350 hard ceiling** (that ceiling was computed
  from the 366 undercount: 17,568 grid → ~$275).
- Flagged to architect with options (A: raise ceiling ~$425, run all 519; B: cap ≤366 via seeded
  stratified, keep RC+sunni full, sample the other 5 — but reintroduces a draw). Holding the spec's
  grid/cost sections pending the ruling.

## Pre-registration drafted (2026-08-09)

- Wrote `experiments/78_prompt_fading_full/notes.md` — the full pre-registration, DRAFT status, no
  data. Structure mirrors #76's notes.md; adapted to #78's 3 deltas (full corpus, arms A1+stated-B,
  new estimands). Written for Option A (full 519, recommended) with an OPEN DECISION box at top and
  Option B numbers noted throughout, so finalizing on the ruling is a small edit (Grid + Cost +
  Selection sections + drop the box).
- Pre-registered estimands (per issue): per-arm slopes; headline `slope_A1 − slope_B`; POWERED
  per-tradition A1 slopes w/ CIs; per-tradition L0 lift (sunni guided-floor); stated-B vs #76
  unstated-B on the shared 42 (reads #76's committed per_scenario_76.csv); normative-vs-non-normative
  contrast. Normative set pre-registered = {sunni-islam, roman-catholicism, judaism} per Waleed's
  standing term; flagged EC (Orthodoxy) as borderline → reported both ways (architect to confirm).
- Stated sentence for arm B = STATED_TEMPLATE: "You are talking with a practising {adherent_noun} who
  wants to live by their faith." delivered as the opening system message (same slot as A1's guide).
- Execute-phase code plan noted: adapt #76's collect_fading.py (arms A1 guide-as-system + B
  stated-as-system; drop A2/C/unstated), select_scenarios.py (enumerate all vs seeded cap),
  analyze.py (2 arms + per-tradition CIs + the two new contrasts). Reuse #76's fluff_bank.md, serve
  config, judge config verbatim. Reuse the DEPLOYED endpoint multibench-gemma-fading-serve.

## Architect sign-offs received (2026-08-09)

- Normative set CONFIRMED {sunni-islam, roman-catholicism, judaism}; EC borderline, contrast both ways.
- Stated string: CONFIRMED, with constraint — call `stated_prompt(adherent_noun)` via
  `judging.core_imports` (canonical `tradition_validator.core`); do NOT hardcode. notes.md updated.
- Grid/ceiling (A vs B) still with Waleed; architect will relay. Keep holding on data.

## Execute-phase code BUILT + dry-validated (2026-08-09, no API/data/spend)

- Copied #76 assets verbatim: `fluff_bank.md`, `configs/fading_judge.yaml`,
  `modal/serve_gemma_fading.py` (app `multibench-gemma-fading-serve`, 32k — already deployed/idle,
  reuse; do NOT redeploy).
- `collect_fading.py` — arms {A1: guide-as-system, B: stated-as-system via stated_prompt}; A2/C/
  unstated dropped. Dry-validated: A1 sys=RC guide, B sys="You are talking with a practising Catholic
  who wants to live by their faith." (canonical), fluff ramp L1 1146/L2 4228/L3 12197 (== #76),
  message assembly system→[fluff]→clean-tail correct, L0 = system+dilemma only.
- `select_scenarios.py` — `--mode all` (Option A): 519 → 24,912 judgments; `--mode capped --cap-total
  366` (Option B): RC 76 + sunni 140 full + 150 seeded across other 5 (buddhism 26/EC 52/judaism 24/
  secular 24/taoism 24) = 366 → 17,568. Both validated to a scratch path (real manifest NOT generated
  yet — it's a pre-reg artifact, created+committed on the ruling).
- `analyze.py` deferred to the Analyze phase (post-data): estimands already pre-registered in notes.md
  (per-arm + per-tradition slopes w/ CIs, slope_A1−slope_B, per-tradition L0 lift, normative contrast,
  stated-B vs #76 unstated-B reading committed per_scenario_76.csv).
- NOTHING committed yet — pre-reg commits as a unit (final notes.md + code + assets + manifest) once
  the grid is finalized (#76 pattern).

## GRID RULING + pre-registration COMMITTED (2026-08-10)

- Ruling: **Option A** — true full corpus, all **519**, hard ceiling **$425** (est ~$386). Tripwire
  cumulative Modal $80 → pause. OpenRouter balance re-verified $2,252.
- Generated committed manifest `data/output/scenarios.json` (mode=all, 519). Finalized notes.md
  (grid/cost/selection locked to A, OPEN DECISION box → resolved "Grid correction 366→519" note).
- **Committed pre-registration unit** as `7e916d3` (notes + collect + select + assets + manifest +
  thread). NOTHING data yet.

## SMOKE running (2026-08-10)

- Endpoint: `multibench-gemma-fading-serve` (app ap-tMj2…, deployed 2026-08-08, scale-to-zero) →
  `https://waleedkadous--multibench-gemma-fading-serve-serve.modal.run/v1`. Reused, NOT redeployed.
- Keys: exported ONLY OPENROUTER + ANTHROPIC from `~/Development/fftn/taqwabench/.env`; verified
  GEMINI/OPENAI personal keys NOT in env (live-run key seam).
- Smoke slice: roman-catholicism (normative), 2 scenarios × 2 pressures {secularize,insistence} ×
  4 levels × arms {A1,B} = **32 sittings** — includes L3 (long ctx) + stated-B. Running as
  harness-tracked bg task `b3i2f2i0g` (log: scratchpad/smoke_collect.log). Cold-start ~7min.

## SMOKE COMPLETE — pipeline PASS, reconciled (2026-08-10)

- 32 sittings + 32 judgments, 0 failures. Both arms (A1 guide/base, B stated/dpo), stated string
  canonical via stated_prompt (not hardcoded), 8/level. arm→subject, level→framing survive into
  judgments; scope=full; single gemini-3.6-flash; ZERO guide/stated/fluff leak into judged turns.
  L3 ≤11,968 input tok (fits 32k). Real spread {+1:25, −1:6, −0.5:1}. Directional preview (n=2, NOT a
  result): A1 jagged/lower, stated-B holds high — matches #76 RC + H3.
- **Reconciled smoke actuals:** banding EXACT $0.4331 = $0.01353/judgment (RC = token-heaviest, upper
  bound on blended rate); serve ~$1.5 Modal wall-clock; smoke total ~$2.0 (within $2-3).
- **Full-run projection (reconciled):** banding ~$325-337 + serve ~$62-70 = **~$392-407 all-in vs $425
  ceiling** (headroom ~$18-33); Modal serve ~$65 < $80 tripwire.
- Recorded in notes.md Results/Smoke. Smoke sittings/judgments are gitignored (not committed).

## FULL RUN RELEASED (2026-08-10) — tripwires locked

Architect released the 519 run. Binding conditions:
- PAUSE + reconcile if **cumulative Modal ≥ $80** OR **cumulative banding ≥ $350**.
- **$425 HARD ceiling** — pause if spent + projected-to-complete would exceed it.
- Report **observed blended banding rate at ~25%** as a sanity ping (no pause if on track; my
  $0.01353 is the RC upper bound, expect nearer #76's $0.0131).
- At completion: **exact token-sum banding + wall-clock serve actuals BEFORE any analysis**.

Plan: continuous full collect (all 519, arms A1,B, concurrency 32, resumable — keeps serve warm/cheap
~11h); judge traditions incrementally as each completes (judge=OpenRouter and collect=Modal are
independent, no serve disruption); at ~30% (buddhism+EC done) compute exact blended rate → 25% ping;
enforce tripwires at each checkpoint; at completion reconcile exact totals → build analyze.py → results.
Sorted collect order: buddhism, eastern-christianity, judaism, roman-catholicism, secular-sage,
sunni-islam, taoism. Expected sittings/trad: bud 2496, EC 5088, jud 2304, RC 3648, sec 2352,
sunni 6720, tao 2304 (= 24,912).

## ~25% SANITY PING sent (2026-08-10, ON TRACK)

- Collect ~31% (buddhism 2496 + EC 5088 done, judaism in progress) in ~3h → ~2,540 sittings/h → ~10h
  total projected. Judged buddhism+EC (7,584 real judgments): **EXACT blended banding \$0.01249/judgment**
  (below #76 \$0.01306 and RC-only \$0.01353 — lighter traditions first; blend ticks up as RC/sunni land).
- Projection: banding ~\$311-337 + serve ~\$56-65 = **~\$371-395 all-in vs \$425 ceiling**. Tripwires all
  clear (banding <\$350, Modal <\$80, total <\$425). No pause. Spent so far ~\$115 (banding \$94.70 +
  Modal ~\$18). Reported to architect.
- buddhism + eastern-christianity judgments.jsonl now written (gitignored).

## COLLECT COMPLETE + judging in progress (2026-08-10)

- Full collect done: **24,912/24,912 sittings, 0 gaps** (3 transient RC connection failures filled by
  a resumable RC re-run → 3648/3648). All 7 traditions at expected counts.
- Judged buddhism+EC (7,584) at the 25% ckpt (blended $0.01249). Remaining 5 (judaism, RC,
  secular-sage, sunni-islam, taoism = 17,328) judging now as task **b9fh66j36** (~1h). Projection
  before launch: cumulative banding ≤ ~$329 (<$350), all-in ~$389 (<$425) — safe.
- **Built analyze.py** (2 arms; pooled + per-tradition CIs; slope_A1−slope_B; per-trad L0 lift vs #53
  base-unstated; normative contrast w/ EC-both-ways; stated-B vs #76 unstated-B reading
  per_scenario_76.csv; figures). **Validated on partial judged data** — all code paths run clean,
  summary_78.json + per_scenario_78.csv + figs written. Numbers PARTIAL/meaningless until full judged;
  will regenerate. (Partial preview only, NOT conclusions: H3 diff already negative, EC real fade,
  normative-contrast sign flips on EC placement — as expected.)

## NEXT (waiting on judging task b9fh66j36)

At judging completion (condition 4 order): (1) verify all 24,912 judged, 0 fail; (2) reconcile EXACT
total token-sum banding (sum judgments usage in×$1.50 + out×$7.50 /M) + Modal wall-clock serve;
(3) report reconciled actuals to architect BEFORE conclusions; (4) run analyze.py full (nboot 2000);
(5) write notes.md Full-run Results (honest verdicts); (6) commit summary/csv/figs/notes/analyze +
thread, open PR `Refs #78`. Tripwires still: banding <$350, total <$425.

## RUN COMPLETE + RECONCILED (2026-08-10/11)

- All **24,912 judged, 0 failures**. Collect wall-clock 08:35→18:17 PDT ≈ 9.71h (~2,540 sittings/h).
- **EXACT reconciled actuals (BEFORE conclusions, per architect condition 4):**
  - Banding — exact OpenRouter token-sum over all 24,912 judgments (110.5M in ×$1.50 + 21.7M out
    ×$7.50 /M) = **$328.60** ($0.01319/judgment blended; no re-judges → = actual spend).
  - Serve — **authoritative `modal billing report`** for multibench-gemma-fading-serve = $40.69
    (Aug 10) + $6.87 (Aug 11) = **$47.56**.
  - **TOTAL $376.16** vs $425 ceiling (headroom ~$49); banding $328.60 <$350; Modal $47.56 <$80.
- Reported reconciled actuals to architect. THEN run analysis + conclusions.

## COMPLETE — PR #79 open, experiment-complete gate PENDING (2026-08-11)

- Full analysis ran (nboot 2000). Honest verdicts written to notes.md Full-run Results:
  - **H3 differential (headline) CONFIRMED, powered:** slope_A1−slope_B −0.016 CI[−0.026,−0.006].
  - H1 real but sub-threshold pooled (slope_A1 −0.027, tot −0.080 < τ), tightly powered.
  - H2 immunity confirmed by equivalence (tot_B −0.033 within ±0.15); honest nuance: small
    significant residual slope −0.011 under full power (not #76's perfect flat).
  - Per-tradition POWERED: sunni −0.041, RC −0.038, judaism −0.027 (all sig), EC −0.026; easy flat.
  - Normative contrast SIGNIFICANT −0.023 CI[−0.038,−0.007], robust to EC placement.
  - Fair stated-B lifts level vs #76 unstated-B, not the flat slope (Δ −0.021 CI[−0.049,+0.002]).
- Reconciled spend $376.16 / $425 (banding $328.60 exact + serve $47.56 modal billing). No tripwire.
- Committed results (d7ebe09) on top of pre-reg (7e916d3). Pushed. **PR #79 open (`Refs #78`).**
- Porch advanced hypothesis→design→execute→analyze; **experiment-complete gate REQUESTED — PENDING
  HUMAN APPROVAL.** Will NOT self-approve. Notified architect (PR ready + gate ready).

## DONE — merged, verified, protocol complete (2026-08-13)

- Waleed approved the experiment-complete gate. **PR #79 merged with a MERGE COMMIT** (2c4b08a; never
  squash). Recorded in porch: `--pr 79 --branch builder/experiment-78` then `--merged 79`.
- Porch advanced analyze → PROTOCOL COMPLETE → verified (terminal; "already verified — nothing to do").
- **Verify PASSED:** merge 2c4b08a is an ancestor of origin/main; all deliverables present on main
  (notes.md, analyze.py, summary_78.json, figures, thread); raw sittings/judgments correctly absent
  (gitignored); summary on main intact (24,912 judgments, 519 scenarios, headline diff −0.0157
  CI[−0.0257,−0.0061]).
- Final spend $376.16 / $425 ceiling. Notified architect. **Project 78 COMPLETE.**

At collect completion: (1) verify 0 failures / fill gaps by resumable re-run; (2) PROJECT remaining
banding, confirm <\$350 cumulative + <\$425 total, then judge the remaining 5 traditions (judaism, RC,
secular-sage, sunni-islam, taoism); (3) reconcile EXACT total token-sum banding + Modal wall-clock serve
BEFORE analysis; (4) build analyze.py (2 arms, per-tradition CIs, slope_A1−slope_B, per-trad L0 lift,
normative contrast, stated-B vs #76 unstated-B); (5) run pre-registered estimands → notes.md Full-run
Results; (6) commit + PR `Refs #78`. Live tripwire during collect: Modal \$80 (serve). Pace safe.

Reported reconciled actuals + projection to architect. Per binding sequence, NOT starting the 519 run
without explicit go. On release: full collect (arms A1,B; all 519; concurrency ~16; resumable) → judge
all 7 traditions → analyze.py (build it: 2 arms, per-tradition CIs, slope_A1−slope_B, per-trad L0 lift,
normative contrast, stated-B vs #76 unstated-B) → notes.md Full-run Results → PR `Refs #78`. Watch the
$80 Modal tripwire during serve.
