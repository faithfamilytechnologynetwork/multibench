# Review — Spec 119: protestant-unified (derived 36-scenario cross-faith row)

## 1. Summary

Built the derived **`protestant-unified`** MultiBench tradition, scored it dual-judge, and published
it as the **8th cross-faith leaderboard row** for the CHI paper. The tradition is the **same-advice
common witness** of Protestantism: its 36 scenarios come from the questions where the seven strands
of the #109 guidance-divergence study give the *same* pastoral answer (study D=0.16 → Pathway B).
The 7-strand `protestantism` monolith is **operationally retired** in favour of it.

Delivered across 7 plan phases (validator field → module skeleton → pilot 6 → remaining 30 → scoring
run → superset export → cross-faith analysis → monolith retirement), each through porch's 2-way
consult. One PR at the end.

## 2. Deliverables & verification

- **Module** `traditions/protestant-unified/` — 36 scenarios (UNI-001…036), 5 taxonomies (monolith's,
  minus `communion`), `question_id` provenance field. Validates `--strict` (0 findings).
- **Validator** — optional `ScenarioMeta.question_id` field (`^Q\d{2}$`) + negative test.
- **Scoring run** (`20260904-protestant-unified`) — **12,960 judgments, uncovered 0**; both judges
  **6,480/6,480** (per-framing 2160 each); every Opus verdict batch-priced (CEFE key, `--no-fallback`).
- **Superset export** (`results/20260905/` + `results-raw/20260905/`) — 8 traditions, combined
  two-judge rule (`mean_of_judges`); the 7 record shards **byte-identical** to `results/20260803`;
  both tiers share an **equal source fingerprint** (`sha256:532e7b0f…`); frozen tiers byte-untouched
  (branch-base diff clean).
- **Analysis** (`experiments/119_protestant_unified/`, `docs/analysis/protestant-unified-round.md`) —
  the 8-row leaderboard with per-tradition bootstrap CIs, framing staircase, per-subject headline
  CIs, steadfastness, Opus-vs-Gemini agreement; figures via the canonical `emit_figures` + two local
  house-style figures. Every number reconciles with the committed tier under hard-fail assertions.
- **Retirement** — monolith README + `results/README.md` + `results-raw/README.md` notes; the monolith
  is out of the cross-faith run/export inputs but stays browsable.
- **Tests** — analysis suite **275 passed / 12 skipped**; committed-artifact guards for the
  cross-tier fingerprint (every dual-tier run), the Phase-6 reconciliation, and `paper_numbers.json`
  staleness.

**Headline result:** protestant-unified ranks **5th of 8** at **+0.4863 [+0.368, +0.590]** (combined
two-judge mean), in the lower normative-tradition band (its CI overlaps judaism and
eastern-christianity — the claim is the band, not a sharp rank). Under the hardest **unstated**
framing it is near neutral (+0.054, CI straddles 0), lifting +0.77 to +0.824 when guided — the
omissive-bias pattern the benchmark measures. Judge agreement r=0.810.

## 3. Deliberate deviations (documented + sanctioned)

- **Scope 38 → 36.** Q17 (remarriage) and Q22 (IVF) dropped at the spec gate (Waleed) as genuinely
  contested, not same-advice.
- **Ranking rule.** The spec said "Gemini ranks, Opus badge-only"; mid-project Waleed changed the
  rule to the **equal-weight mean of both judges** (#120/#121, merged separately). Phases 5–7 use the
  combined rule; the spec text is superseded by this architect-sanctioned change.
- **CEFE probe cap overage.** A pre-authorized live key-path probe (≤10 cells, **$1 cap**) cost
  **$1.23** — ~23% over the cost cap (cell count within). Recorded honestly, **ratified by the
  architect** 2026-09-05T07:08:25Z, no rework.
- **Leaderboard pin deferred (plan fallback).** The `leaderboard.test.ts` reconciliation pin requires
  Waleed's explicit acceptance of the numbers, which had not arrived at PR time. Per the plan's
  fallback and the architect's direction, the PR opens **without** the pin; it lands in a follow-up
  commit once acceptance is relayed. Never blocked the PR on the human acceptance.
- **`experiments/` directory** uses the issue number (`119_`) where spec/plan say `<PR#>`; renamed to
  the PR number at PR time.

## 4. Spend — exact accounting

**All-in Phase 4 = $338.62 usage-computed billed actual** ($328.28 run + $9.10 batch smoke + $1.24
CEFE probe), well under the $600 ceiling and below the $450 alert. Prices are the `report.py`
2026-08-03 table; two subject promos expired 2026-08-31 (before the run), so at post-promo standard
rates the all-in would be ~$356.21 — a labeled what-if for invoice reconciliation only (console
invoices authoritative). Details in `experiments/119_protestant_unified/notes.md`.

## 5. Lessons

- **Sum spend from usage data, never trust a report figure.** The probe cost was first misreported as
  $0.007 — the collection-only total from a `report.json` written *before* the judge verdicts landed.
  The real live cost ($1.23) came only from summing the judgments' own usage, and it revealed the cap
  overage. (Repo scar, re-confirmed.)
- **Verify a delegated agent's work before trusting its report.** A fork returned a plausible summary
  with **0 tool uses** — it had done nothing. Caught by checking `git status`/grep before acting on
  its claims; did the work directly.
- **Reconcile derived numbers through the canonical code, and guard it.** The per-tradition CIs reuse
  `paper_bundle`'s exact scenario-cluster bootstrap; analyze.py hard-asserts each tradition's
  bootstrap point equals the canonical mean-of-means (≤1e-9), so the CI is drawn around the ranked
  score by construction. `nan` was made to fail loud rather than slip through `abs(nan−x)>tol`.
- **A "derived" tradition is a compile, not a merge.** The common witness was compiled from the
  same-advice questions with per-column receipts; scoring it (+0.486) far above the mixed monolith
  (+0.029) is the derivation's intent showing up in the data.

## 6. Follow-ups (post-PR)

- **Leaderboard pin** — add the `results/20260905` reconciliation block to `leaderboard.test.ts` once
  Waleed accepts the numbers (architect relays). That commit touches `apps/multibrowser`, so it will
  trigger the vitest suite in the dispatcher — run `pnpm -C apps/multibrowser install` first (the
  worktree has no `node_modules`), or the check errors on missing deps.
- **Raw-tier retention** — 3 score-backed raw runs (~310 MB) now exceed the N=2 intent; a dedicated
  retirement PR is Waleed's call (documented in `results-raw/README.md`).
- **`analysis.paper_bundle._combined_rows`** now has an out-of-module consumer (`analyze.py`); promote
  it to a public API in a later analysis-maintenance pass.
- Production raw re-bake + live fingerprint verification (`railway up --no-gitignore`) are post-merge,
  architect-driven (verify phase).
