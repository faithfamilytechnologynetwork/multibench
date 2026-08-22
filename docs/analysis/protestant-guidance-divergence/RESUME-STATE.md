# Resume state — delete this file when the study publishes

Working note so any session (this one resumed, or a fresh one) can close out the study. The
pre-registration (`questions.md`, `method.md`, `codebook.md`, `pathway-rule.md`) is committed and
binding; do not revise it retroactively.

## Done (all committed on `claude/protestant-bench-redesign-h1wlz2`)

1. Pre-registration committed at `6f3ad58`, before any answers existed.
2. **All 350 worksheets** (7 strands × Q01–Q50) written by independent per-column agents,
   schema-verified.
3. **Citation audit complete on all seven columns** (fixed sample Q05/Q15/Q24/Q37/Q47 per column;
   logs in `audit/`): 222 citations checked guilty-until-confirmed, zero fabricated loci, ~11
   corrections + 6 flag downgrades applied in place, no Counsel field touched.

## In flight at the usage-limit warning

- Four **blind advice coders** (A/B on Q01–Q25, C/D on Q26–Q50) coding pseudonymised
  counsel-only packets; outputs expected at `<scratchpad>/blind/coder_{A,B,C,D}.json`.
- One **grounding coder** (unblinded) writing `codings/grounding.json` (repo path).

## To close out (in order)

1. **Blind artifacts are reproducible** — if the scratchpad was lost, regenerate packets+mapping
   byte-identically (seeded shuffle, seed 20260822 in the script):
   `python3 docs/analysis/protestant-guidance-divergence/prepare_packets.py --out <scratchdir>/blind`
   (Valid only while the committed worksheets are unchanged — do not edit worksheets before
   re-running.)
2. If coder JSONs are missing or partial: relaunch coders per the prompts in the session
   transcript — each blind coder reads ONLY `codebook.md` + its 25 packets, writes
   `coder_{A..D}.json` (schema: severity / clusters / silent / outliers / rationale per question;
   clusters ∪ silent = all seven pseudonyms). Grounding coder reads worksheets' Grounding
   sections, writes `codings/grounding.json` (shared|parallel|divergent + note per question).
3. **Adjudication**: for each question, compare the two coders (severity mismatch or materially
   different partition ⇒ disagreement). Launch one adjudicator agent per half on only the
   disagreeing questions (it reads the packet + both codings, decides finally, same schema).
   Merge agreed + adjudicated into `codings/adjudicated.json`. Record the two agreement rates
   (exact severity match; exact partition match).
4. Copy `mapping.json` into `codings/mapping.json` (only now — after coding — to preserve the
   blinding record), commit coder files + adjudicated + mapping + grounding.
5. Run `python3 docs/analysis/protestant-guidance-divergence/analyze.py` → `output/summary.json`,
   `output/pairwise_agreement.csv`, `output/per_domain.csv`. Commit.
6. Write the study narrative at `docs/analysis/protestant-guidance-divergence-study.md`:
   headline severity shares and **D**; the advice × grounding 2×2 (the thesis cell is
   same-advice/different-grounding); per-domain rates; named divergence areas (cluster the
   `substance` questions); pairwise strand agreement + outlier/silence counts; audit error rates;
   coder agreement; the **Limits** already declared in `method.md`; and the **pathway
   recommendation read mechanically off `pathway-rule.md`** from D and concentration — do not
   re-derive the thresholds. Add the README index entry in `docs/analysis/README.md`.
7. Delete this file, commit, push, open a PR to `main` mirroring
   `.github/PULL_REQUEST_TEMPLATE.md` (docs-only exempt box), and merge — the maintainer asked
   for the study to be run **and published** with a recommended pathway.
