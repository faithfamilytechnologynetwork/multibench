# JaleesBench (sunni-islam) ultracode audit — data artifacts

**Status: complete (resource-truncated; see the catalogue's scope disclosures).** This directory
collects every artifact of the multi-agent ("ultracode") audit of the **sunni-islam** tradition
(*JaleesBench*), run in the manner of the [SynodiaBench](../synodiabench-ultracode-audit.md) and
[plurality](../plurality-ultracode-audit.md) audits — with one deliberate difference:
**no edits were made to `traditions/sunni-islam/`**. Everything the audit produced —
confirmed findings, proposed rewordings, structural drafts, new-scenario candidates —
is stored here as *proposals*, so the JaleesBench authors can adopt any part of it upstream
(github.com/iaser-ai/jaleesbench) or in the port, at their discretion.

**The catalogue is [`../jaleesbench-ultracode-audit.md`](../jaleesbench-ultracode-audit.md).**

## Contents

- `data/audit-brief.md` — the shared brief every audit agent worked from (hard rules,
  file contract, established structural facts).
- `data/bank-catalog.txt` — one-line-per-scenario map of the 140-probe bank
  (id | locus | label | identity signal | pillars | hearts | opening line).
- `data/audit-lenses-and-triage.json` — full Workflow 1 output: seven expert-lens reports
  (traditionalist faqīh, Salafi/Athari reader, taṣawwuf/iḥsān scholar, hadith-sciences
  citation sweeper, pastoral-safety & mufti-boundary auditor, diverse-ummah panel,
  cross-tradition consistency editor) + full 140-scenario triage (verdict, failure-pole
  classification, safety-register candidacy, citations-to-verify, findings).
- `data/all-findings.json` — the 182 findings flattened, with global ids (F001…F182).
- `data/findings-notes-only.json` — the 41 note-severity observations (catalogue-only;
  not routed through adversarial verification).
- `data/verification-verdicts.json` — the 96 adversarial-verification verdicts (47 confirmed /
  41 refined / 8 refuted), each with premise check, grounded reasoning, and (for refined)
  the corrected proposal. Serious findings were routed to an additional refutation-seeking
  verifier where the run reached them.
- `data/unverified-finding-ids.json` — the 45 verifiable findings the verification run did NOT
  reach before the pass was wrapped up (treat as plausible, not confirmed — including JLS-133,
  JLS-137, JLS-131, and most tradition-level structural findings).

## Workflow 1 headline numbers (pre-verification — do not act on these directly)

- Triage: **85 ok / 37 minor / 16 revise / 2 serious** across 140 scenarios.
- Failure-pole distribution (audit classification, no re-tagging): laxity 98 / excess 36 /
  balanced 5 / n-a 1.
- 24 safety-register candidate scenarios; 775 citations queued for grounding.
- 182 findings total (141 verifiable + 41 notes).

**Guardrail:** none of these findings is actionable until it survives the adversarial
verification pass (Workflow 2) — the sibling audits showed the raw lens reviews would have
shipped regressions in every tradition.
