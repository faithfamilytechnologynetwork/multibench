# bugfix-17 — Remove tradition-specific scoring band names (normalize to numeric −1…+1)

GitHub issue #17. BUGFIX protocol, strict mode.

## Investigate (complete)

**Goal:** strip each tradition's invented band *names* from `README.md` band tables and
every `judge-guidance.md`, replacing scoring labels with bare numbers on the canonical
scale −1, −0.5, 0, +0.5, +1. Constructs / guides / source / turn1 / pressures untouched.

### Scope (measured)
- **judge-guidance.md files with band labels:** eastern-christianity 106/106, judaism 39/40
  (MSR-030 only has them line-wrapped), buddhism 40/40, taoism 40/40 → **225 files**.
- **README band tables to rewrite:** eastern-christianity, judaism, buddhism, taoism (4).
- **sunni-islam:** README has **no** band table; judge-guidance is proof-text (hadith) style —
  **zero band labels. Nothing to change.** (The issue listed it, but the named bands
  Perfume/Scent/Inert/Sparks/Burns are not present in the file-based port.)

### Key facts that shape the fix
- Every scoring label is **bolded** (`**Myrrh**`, `**Like water** (+1)`, `**a stumbling block**`).
  No unbolded scoring labels anywhere; none in `scenario.yaml`. Teaching imagery (water, myrrh,
  aroma) lives only in source quotes / guide.md / construct — never as a bare bolded band token.
  → A bolded band-name token in judge-guidance.md is *always* a scoring label.
- **Edge cases the replacer must handle:**
  - Names wrap across line breaks: `**Apples\nof gold**`, `**the wheel and\nthe hoof**`, etc.
    → need perl slurp mode with `\s+` between words.
  - Lowercase variants: `**idle words**` (MSR-030).
  - Missing article: `**hard and stiff**` (TAO-012), `**A/a stumbling block**`.
  - Taoism carries redundant trailing annotations: `**Like water** (+1)`, `**Not the Way** (−1)`,
    `**The hard and stiff** (−0.5)` — strip the `(...)` since the number becomes the label.

### Per-tradition name → number map
- eastern-christianity: Myrrh→+1, Fragrance→+0.5, Idle word→0, Smoke→−0.5, Stench→−1
- judaism: Apples of gold→+1, Light→+0.5, Idle words→0, Dust→−0.5, (a) stumbling block→−1
- buddhism: Fragrance of virtue→+1, Wholesome→+0.5, Idle word→0, Unwholesome→−0.5, the wheel and the hoof→−1
- taoism: Like water→+1, the soft and living→+0.5, Many words→0, the hard and stiff→−0.5, Not the Way→−1

### README handling
- Rewrite each band table to `| Score | Meaning |` using the issue's **canonical neutral
  meanings** (identical across traditions). Drop the `Band`/name column.
- EC README prose line "blessing of a passion is **Stench**" → `**−1**`.
- Remove the "The names are drawn from …" sentences (judaism/buddhism/taoism intros) — they
  enumerate the now-removed names.

### Regression test
- Add `apps/tradition_validator/tests/test_band_names_normalized.py` scanning real
  `traditions/*/README.md` + `*/scenarios/*/judge-guidance.md` for any known band-name label;
  assert none remain. Fails pre-fix, passes post-fix. Touching apps/tradition_validator makes
  the dispatcher (`.codev/checks/test.sh`) run pytest.

### Scope/LOC note
Large (225 data files) but purely mechanical, single-concern, fully contained — stays within
BUGFIX. Net diff will exceed the 300-LOC *guideline* on line count alone; that's expected for a
normalization sweep and not architectural. Will note in the PR. Acceptance gate:
`validate-all traditions --strict` still passes.

## Fix (complete)

Applied a deterministic, targeted normalization (regex matched only the exact bolded band
name + an optional redundant `(±n)` annotation, newline- and case-tolerant — so prose can't
be touched by construction):
- **226 judge-guidance.md** files, **670 label replacements**; zero residual band names, zero
  dangling annotations. Spot-checked the tricky cases (line-wrapped `**Apples\nof gold**`,
  lowercase `**idle words**`, article-less `**hard and stiff**`, taoism `(+1)`/`(−1)` strip,
  `**Smoke** to **Stench**`, and the `(Dhp 1)` citation correctly *kept*).
- **4 README band tables** (EC/judaism/buddhism/taoism) rewritten to `| Score | Meaning |`
  with the issue's canonical neutral meanings (identical across traditions); dropped the
  "names are drawn from…" sentences; EC prose `is **Stench**` → `is **−1**`.
- **sunni-islam:** untouched (no band table, proof-text judge-guidance — zero labels).
- Genuine construct imagery KEPT: buddhism README construct bullet "the **fragrance of virtue**
  that travels even against the wind", taoism "**water**"/"**the water-like good**", judaism
  "**apple of gold in its setting of silver**", and all guide.md/tradition.yaml/source/turn1/
  pressures. Regression test scopes its README scan to the `## The five bands` section so it
  never flags construct imagery.

Regression test `apps/tradition_validator/tests/test_band_names_normalized.py` (fails pre-fix,
passes post-fix). `validate-all traditions --strict` → ALL PASS (5 traditions). Full
tradition_validator suite: **100 passed, 2 failed**.

### BLOCKER (pre-existing, unrelated to #17)
The 2 failures are `test_governance_docs.py::test_hot_context_mirror_in_sync[CLAUDE.md]` and
`[AGENTS.md]`: the HOT CONTEXT block in CLAUDE.md/AGENTS.md is stale vs
`codev/resources/arch-critical.md`. Confirmed pre-existing: those 4 files are unchanged in my
diff and the mismatch already exists at HEAD (`62384f2`). Regenerated by `codev update`, i.e.
governance scope, not band-name scope. BUT my regression test lives under apps/tradition_validator,
so the porch tests-dispatcher runs the whole suite and these 2 will block `porch done`.
Notifying architect for guidance (regenerate the mirror, or fix on main + rebase) before
advancing. Not bypassing the check, not skipping the governance tests.

## PR phase

Architect unblocked (chose: fix on main + rebase): local main got 3242371 (mirror regen).
Rebased onto local main (clean), force-pushed builder/bugfix-17, full suite green, porch done
fix→pr, opened **PR #18** (base main; 3242371 rides along since origin/main lacks it — expected).

### CMAP (3-way PR review)
- **gemini: APPROVE**
- **codex: REQUEST_CHANGES** — incomplete fix; composite bold labels `**Stench regardless of
  accompanying counsel**` (17 EC files) survived the exact-token regex; regression test had the
  same gap.
- **claude: COMMENT** — same finding, ~29 residual EC scoring uses (composite-bolded +
  unbolded "doing so is Stench"); confirmed buddhism/taoism/judaism residuals are correctly-kept
  teaching imagery.

Both right — my investigate-phase miss: I dismissed the line-wrapped probe hits as mis-paired
`**`, but `**Stench regardless of …**` are real composite labels. Addressed (not rebutted):

### Pass-2 fix (addresses REQUEST_CHANGES)
- EC: 16 composite `**Stench regardless of …**` → `**−1 regardless of …**`; `**Idle word /
  Smoke**` → `**0 / −0.5**`; 12 unbolded "is/at/are Stench" → `**−1**`. 29 replacements / 24 files.
- taoism TAO-012: `The −1 "Not the Way" outcome` → `The −1 outcome` (redundant band-name label
  on a numbered outcome — distinct from the ch.8/76 *teaching* quotes, which stay).
- Verified zero stench/smoke remain in EC; remaining band-ish words are all teaching imagery
  (EC Mt 12:36 "idle word", judaism dust/light concepts, buddhism "wholesome energy"/Dhp-54
  quotes, taoism "like water"/"hard and stiff" ch.8/76 quotes) — exactly what CMAP confirmed
  to keep.
- **Strengthened regression test**: added `test_no_scoring_only_band_terms_remain` — EC's coined
  scoring-only terms (Stench/Smoke), which have no teaching usage, must not appear at all
  (catches composite-bolded + unbolded). Kept exact-bold-token check for all names. Confirmed it
  FAILS pre-pass-2, passes post. Full suite **103 passed**; `validate-all --strict` ALL PASS.
