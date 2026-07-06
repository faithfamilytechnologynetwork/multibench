# JaleesBench (sunni-islam) ultracode audit — working artifacts

**Status: in progress.** This directory collects every artifact of the multi-agent ("ultracode")
audit of the **sunni-islam** tradition (*JaleesBench*), run in the manner of the
[SynodiaBench](../synodiabench-ultracode-audit.md) and
[plurality](../plurality-ultracode-audit.md) audits — with one deliberate difference:
**no edits are made to `traditions/sunni-islam/`**. Everything the audit produces —
confirmed findings, proposed revisions, proposed new scenarios, judge-guidance updates —
is stored here as *proposals*, so the JaleesBench authors can adopt any part of it upstream
(github.com/iaser-ai/jaleesbench) or in the port, at their discretion.

The final catalogue will land at `docs/analysis/jaleesbench-ultracode-audit.md`, and full
proposal drafts under `proposals/`.

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

## Workflow 1 headline numbers (pre-verification — do not act on these directly)

- Triage: **85 ok / 37 minor / 16 revise / 2 serious** across 140 scenarios.
- Failure-pole distribution (audit classification, no re-tagging): laxity 98 / excess 36 /
  balanced 5 / n-a 1.
- 24 safety-register candidate scenarios; 775 citations queued for grounding.
- 182 findings total (141 verifiable + 41 notes).

**Guardrail:** none of these findings is actionable until it survives the adversarial
verification pass (Workflow 2) — the sibling audits showed the raw lens reviews would have
shipped regressions in every tradition.
