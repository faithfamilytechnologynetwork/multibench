# Why the ultracode audit — and why rerun it across traditions

A short rationale to share with collaborators: why the *SynodiaBench* (eastern-christianity)
revisions were necessary, why a multi-agent ("ultracode") audit surfaced them when a prior
single-model "max-effort" pass did not, and what a rerun across all traditions buys us. The
detailed change log lives in the companion [SynodiaBench ultracode audit catalogue](./synodiabench-ultracode-audit.md);
this is the "why" in a page.

## Why the revisions were necessary

Not because the bank was bad — the [triage of all 106 scenarios](./synodiabench-ultracode-audit.md)
came back *82 clean, 24 minor, zero serious* at the raw level. They were necessary because
credibility to a discerning religious audience lives in details a general quality pass never
touches: a wrong *Ladder* step number, an inverted LXX/Hebrew citation, a recension misattributed
to Ward instead of Guy, a safety rule that existed only as per-scenario boilerplate rather than a
binding contract, and — the one that actually mattered theologically — [BZ-062](../../traditions/eastern-christianity/scenarios/BZ-062/judge-guidance.md)
being quotable as "luminous experience is by definition delusion," which lands on the wrong side of
the very council that vindicated the hesychasm those Athonite readers live by. To a monk who knows
the *Ladder* by heart, a wrong step number is a "tell" that discredits the whole instrument; the
bar for this audience is exactness, and that is the bar these edits were reaching for
([PR #22](https://github.com/faithfamilytechnologynetwork/multibench/pull/22)).

## Why ultracode caught what a max-effort run didn't

"Max" is *depth* — one strong model reasoning as hard as it can from a single vantage. The gains
here were **structural, not deeper**:

- **Decomposition into named standpoints.** A general reviewer, however hard it thinks, does not
  spontaneously read the same file as a Mount Athos hieromonk *and* a Byzantine Catholic bishop
  *and* a citation auditor. The personas force the perspective-taking that surfaces
  audience-specific problems.
- **External grounding.** A wrong step number or an LXX/Hebrew slip is a *fact you verify against a
  source*, not something you can reason your way to. A max model stays confidently wrong; a verifier
  with web access checks it.
- **Adversarial verification.** This caught at least three would-be regressions *the reviewers
  themselves proposed* — including one reviewer's own wrong "chapter 18" correction and an economia
  re-tag that would have collapsed a deliberate pole-split. A single pass has no independent check
  on its own confident errors.

The honest coda: ultracode is **not** infallible. Its Eastern-Catholic persona imported an outside
*caricature* — a supposed "juridical tilt" — that only a real member of that audience caught and
corrected ([ddb8784](https://github.com/faithfamilytechnologynetwork/multibench/commit/ddb8784)).
So the real shape is: max sharpens one viewpoint; ultracode multiplies viewpoints and adds a
fact-check; and **human expert review remains the final gate.**

## Why a rerun across all traditions is worth it

Two reasons beyond "find more typos":

1. **Comparability.** The audit measured eastern-christianity's mercy↔strictness axis at ~76/20/10
   (heavily rigorist) while siblings differ — judaism actually tilts the other way. A lone-pole
   concentration means a model can score worse on one tradition for a *structural* reason rather
   than a real one, quietly corrupting cross-tradition comparison — and you only see it by computing
   all the distributions together.
2. **The same error classes recur.** Numbered-citation slips (Qur'ān āyah / variant readings,
   sutta/Nikāya refs, Talmud daf, Daodejing chapters), boilerplate-not-binding safety overlays, the
   teacher-authority boundary, and inter-school neutrality left as an unstated assumption are all
   likely present elsewhere — as is the persona-caricature risk, for every audience.

A sweep produces, per tradition, a credibility dossier and a corrected bank that front-loads the
exactness — so when it reaches actual scholars from each tradition, the
[`scholar_review` gate](../../traditions/eastern-christianity) is about *judgment and caricature*
(the things only they can catch) rather than typos a workflow could have. The reusable recipe and
the specific cross-tradition sweeps to run first are written up in the catalogue's
[cross-tradition recommendations](./synodiabench-ultracode-audit.md#cross-tradition-recommendations).

## See also

- [SynodiaBench ultracode audit catalogue](./synodiabench-ultracode-audit.md) — the full change log,
  citation-correction table, and recommendations.
- [MultiBench vs. MoReBench](./MultiBench-vs-MoReBench.pdf) — how MultiBench's *formative-residue*
  construct differs from a process-focused moral-reasoning benchmark.
- PRs: [#21 SophiaBench](https://github.com/faithfamilytechnologynetwork/multibench/pull/21) ·
  [#22 SynodiaBench revision](https://github.com/faithfamilytechnologynetwork/multibench/pull/22).
