# task-rBCd — MultiWeights paragraph refresh (docs-only)

## Task
Update the stale `\textbf{MultiWeights.}` Future-Work paragraph in
`docs/paper/multibench-paper.tex` (~line 575). It still said "in progress" with a
TODO about unconfirmed samplability claims. MultiWeights is COMPLETE — there is a
companion paper `docs/paper/multiweights-paper.tex` in the same dir.

## What I did
- Rewrote the paragraph (4 sentences, Future-Work scale) to state the completed
  result and cite the companion paper `\citep{multiweights2026}`.
- Deleted the TODO comment block.
- Added a `@misc{multiweights2026}` entry to `references.bib` (companion paper,
  draft, author list forthcoming — `key = {MultiWeights}` so the inline cite reads
  `[MultiWeights]` rather than an ugly no-author `[mul, 2026]`).
- Left `\author{}` in the main paper untouched (stays empty pending Waleed).
- Rebuilt PDF via `latexmk -xelatex -cd` (fontspec needs xelatex). Forced a bibtex
  rerun so the new citation resolves; 0 undefined-citation warnings. Verified the
  rendered paragraph by reading the PDF page.

## Numbers — all verified verbatim against multiweights-paper.tex before writing
- AFB / AllFaith cold meaningful representation: 1% → 27% (SFT) → 30% (DPO),
  mean 0.113 → 1.147. (abstract L61-62, L392)
- Deployment-mode capability flat ~83 chat-template MMLU. (abstract L67-69)
- Companion 50/50 retrain, held-out **scenarios**: +0.78 (SFT) / +0.90 (SFT+DPO),
  every tradition's held-out CI > 0. (§3.4 L326-336, fig:transfer)

## Wording discipline (critical)
- Transfer is to **held-out scenarios**, scenario-level within each tradition —
  NOT "cross-tradition transfer" (leave-one-tradition-out is untested). This exact
  overclaim was corrected in PR #69; approved language is multiweights-paper.tex
  §3.4 L340-347. Paragraph ends with the leave-one-tradition-out caveat.

## PR #71 review (architect, 2026-08-07)
One required fix: opening "The distillation experiment this paragraph once
anticipated is complete" was journey-narrative (paper must present final analysis,
not the document's own history — standing Waleed rule). Replaced with a direct
claim: "A companion experiment answers whether recognition can be internalized
rather than prompted [MultiWeights]: ...". Rest of paragraph unchanged. Rebuilt
PDF (xelatex, 0 undefined cites), pushed. Approved pending this fix.

## Status
Docs-only change on `builder/task-rBCd` (branched at origin/main). PR opened,
merge-commit convention. NOT merging until architect approves on the PR.
