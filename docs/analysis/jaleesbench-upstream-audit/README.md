# JaleesBench (upstream repo) ultracode audit — data artifacts

Machine-readable artifacts of the multi-agent ("ultracode") audit of the **upstream JaleesBench
repository** ([github.com/iaser-ai/jaleesbench](https://github.com/iaser-ai/jaleesbench) — Kadous, Olsen
& Hwang), run in the manner of the [SynodiaBench](../synodiabench-ultracode-audit.md) and
[plurality](../plurality-ultracode-audit.md) audits — with the constraint that **nothing in the
JaleesBench repo, or in `traditions/sunni-islam/` (the port), was edited.** Everything here is a
*proposal* for the JaleesBench authors.

**The human-readable catalogue is
[`../jaleesbench-upstream-ultracode-audit.md`](../jaleesbench-upstream-ultracode-audit.md).** For the
earlier audit of the *ported* tradition data (not the upstream repo), see
[`../jaleesbench-ultracode-audit.md`](../jaleesbench-ultracode-audit.md) and its
[`jaleesbench-audit/`](../jaleesbench-audit/) data.

## Contents

- `data/all-findings.json` — the **88 verified findings** (`F001`…`F088`), each with severity, category,
  location, claim, premise-check, proposed fix, source lens, corroborating lenses, and its adversarial
  `verification` verdict (22 confirmed / 49 refined / 17 refuted) with grounded reasoning and sources.
- `data/verification-verdicts.json` — the 88 `{ref, category, verification}` triples on their own.
- `data/triage.json` — the full **140-probe triage**: per-probe verdict, failure-pole (wasaṭiyya axis),
  register candidacy, identity-signal check, and citations-to-verify, plus the tallies (115 ok / 24 minor
  / 1 serious; failure-pole 101 laxity / 30 excess / 8 balanced / 1 n-a; 26 register candidates).
- `data/unverified-findings.json` — the **48** findings the verification pass did not reach before the
  run was wrapped up (marked `status: "plausible-not-confirmed"`).
- `data/cross-tradition-comparison.md` — the cross-tradition dossier: the seven-tradition comparison
  table, the sibling templates to copy (in Islamic idiom), the new-scenario priority list, and the
  comparability note.
- `data/proposed-scenarios.json` — the **proposed authoring set**: candidate probes staging the
  under-covered against-excess (ghuluww / *wasaṭiyya*) pole and the missing safety/register seam, in
  JaleesBench's exact probe format (verbatim Riyāḍ anchors, all six pressures, a fiqh-neutral corrective),
  each adversarially citation- and neutrality-verified. **Proposals only — added to no bank.**
- `data/lenses/` — the 13 expert-lens reports (traditionalist faqīh, Salafi/Athari, taṣawwuf/iḥsān,
  hadith-citation sweeper, paper methodologist, statistics auditor, harness code reviewer,
  taxonomy-coverage, docs-consistency, safety & mufti-boundary, diverse-ummah, Arabic-replication,
  cross-tradition).

## Guardrail

No finding here was catalogued as confirmed until it survived an adversarial verification pass that first
checked the premise against the actual repo text and then web-grounded any theology/citation claim — the
sibling audits showed the raw lens reviews would have shipped regressions in every tradition, and this
pass refuted **17** would-be defects (see the catalogue's "What verification refuted").
