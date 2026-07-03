# workflows

Pipelines that operate over traditions to produce or consume MultiBench data.

- **[judging](judging/)** — scores agent responses against each scenario's
  `judge-guidance.md` (anchored to the tradition's `guide.md`), on the canonical
  −1…+1 scale.
- **[analysis](analysis/)** — consumes judging output (N `--results-dir`s, one per
  tradition) into a self-contained cross-tradition HTML report + scenario-cluster
  bootstrap 95% CIs + optional matplotlib figures (port of JaleesBench's
  report/figure/stats tooling).
- **scenario generation** — authors disguised first-person scenarios from a
  tradition's canonical source.
