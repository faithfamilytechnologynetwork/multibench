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

## NEXT (waiting on Waleed's grid ruling)

On the ruling: (1) generate the manifest in the chosen mode; (2) finalize notes.md Grid+Cost+Selection
+ drop the OPEN DECISION box; (3) commit the pre-registration unit; (4) get endpoint URL, run smoke
(~$2-3, incl. a normative tradition + L3); (5) STOP → reconcile usage-computed smoke actuals with the
architect; (6) on the go, full run (resumable, $80 Modal tripwire); (7) analyze + PR (`Refs #78`).
