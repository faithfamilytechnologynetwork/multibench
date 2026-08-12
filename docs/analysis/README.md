# Analysis

Standalone analysis artifacts for MultiBench.

- **[protestantbench-construction.md](./protestantbench-construction.md)** — sources and construction
  of the **protestantism** tradition (*ProtestantBench*, 100 scenarios): why a pan-Protestant bench
  must take **Scripture as the primary source with the confessional standards as a constellation**
  (Book of Concord, Westminster Standards, Three Forms of Unity with Belhar, Thirty-Nine Articles
  and the Prayer Book, the Methodist Articles with Wesley's Standard Sermons and the EUB Confession,
  the Baptist Faith & Message, Barmen held in common, Kuyper as non-binding background) rather than
  elevating one confession; the six taxonomy axes, including `communion`, which makes the
  **intra-Protestant non-adjudication rule mechanically checkable**, and `office`, which encodes the
  judge's paradigm — *would a faithful pastor, elder, or deacon of this person's own church
  recognise this as the mutual conversation and consolation of the brethren?*; the five-stage
  construction pipeline (corpus research → locked grid → authoring → adversarial citation audit +
  per-family insider review → validator); and what that pipeline caught, including a manifest no
  YAML parser could read and three confessional-status hazards (Belhar's varying binding force,
  Kuyper's non-confessional status, the Westminster American revision).
- **[positioning-companion-not-director.md](./positioning-companion-not-director.md)** — a positioning
  analysis for a future paper, answering the objection that a "tradition-ified" LLM cannot replace an
  actual spiritual director in each tradition. It separates the measurement instrument from a deployed
  product from the human director; shows that deference to living human authority is already
  MultiBench's *scored* axis (the companion construct, the "none of the authority, all of the care"
  guides, the safety overlay); concedes the critique's irreducible residue; gives per-tradition
  recommendations and deployment patterns that route users to their human directors; and closes with a
  **runnable proposal** (a `Workflow` pipeline) that generates the paper from benchmark data,
  pre-registers a holistic recommended-practices catalogue, and concludes with a human-subjects study
  and an open invitation to extend the corpus to every willing tradition.
- **[multibench-cross-tradition-report-2026-07-02.pdf](./multibench-cross-tradition-report-2026-07-02.pdf)**
  — the first cross-tradition measurement run (five traditions, 900 sittings, 2,700 judgments, Opus 4.8
  and Sonnet 4.6 as subjects), used as the empirical grounding for the positioning analysis: the
  tradition gradient, the recognition-dominates result, the allegiance-switch under pressure (MSR-004),
  the floor-shaped failure distribution, and the universal gradualism gap.
- **[MultiBench-vs-MoReBench.pdf](./MultiBench-vs-MoReBench.pdf)** — a comparison of
  MultiBench's tradition-grounded companionship scenarios against
  [MoReBench](https://morebench.github.io/), a process-focused moral-reasoning benchmark.
  Includes worked scenario examples per tradition and an evidence-anchored extrapolation
  (anchored to the measured JaleesBench / `sunni-islam` run) of the result differences we'd
  expect between the two benchmarks. MoReBench figures are from its public abstract/site;
  cross-benchmark projections are reasoned hypotheses, not measured cross-benchmark results.
- **[jaleesbench-ultracode-audit.md](./jaleesbench-ultracode-audit.md)** — the catalogue of the
  multi-agent ("ultracode") audit of the **sunni-islam** tradition (*JaleesBench*, the original
  bench the repo generalized from) — a **no-edits pass**: seven expert lenses + full 140-scenario
  triage + adversarial verification, with every confirmed finding, proposed rewording, structural
  draft (safety overlay, symmetric mufti boundary, neutrality contract, wasaṭiyya axis), and
  new-scenario candidate stored as *proposals* for the JaleesBench authors rather than applied.
  Machine-readable artifacts in [`jaleesbench-audit/`](./jaleesbench-audit/).
- **[jaleesbench-upstream-ultracode-audit.md](./jaleesbench-upstream-ultracode-audit.md)** — the same
  ultracode treatment applied to the **actual upstream JaleesBench repository**
  ([github.com/iaser-ai/jaleesbench](https://github.com/iaser-ai/jaleesbench)), not just the ported
  tradition data: it audits the **paper, the evaluation harness, the design/authoring docs, the Arabic
  replication, and the results narrative** the port never contained. A **no-edits pass** (13 expert
  lenses + full 140-probe triage + adversarial verification + a cross-tradition comparison + a proposed
  authoring pass): 88 verified findings (22 confirmed / 49 refined / 17 refuted) spanning fiqh-neutrality
  correctives, RS-as-collection-number citations, paper/code/statistics drift (the 140-vs-143
  arithmetic, the agreement-overlay, the COI omission, an un-wired citation-CLI flag), taxonomy fidelity,
  and the missing safety-register / *wasaṭiyya* / neutrality contract — with proposed against-excess and
  safety scenarios stored as *proposals*. Machine-readable artifacts in
  [`jaleesbench-upstream-audit/`](./jaleesbench-upstream-audit/).
- **[plurality-ultracode-audit.md](./plurality-ultracode-audit.md)** — the catalogue of the
  multi-agent ("ultracode") audit, revision, and expansion of the **taoism** (*TaoBench*),
  **buddhism** (*MittaBench*), **judaism** (*MiddotBench*), and **secular-sage** (*SophiaBench*)
  traditions — the rerun the SynodiaBench catalogue recommended. Covers the per-audience assessment,
  the confirmed changes (safety/neutrality contracts, teacher-authority symmetry, citation
  corrections), the balance-axis rebalancing by authoring 37 new scenarios, and what adversarial
  verification refuted. Sunni Islam and eastern-christianity were not touched.
- **[synodiabench-ultracode-audit.md](./synodiabench-ultracode-audit.md)** — the catalogue of the
  multi-agent ("ultracode") audit and revision of the **eastern-christianity** tradition
  (*SynodiaBench*) for credibility to Orthodox elders, Athonite monks, and Eastern-Rite Catholic
  bishops at once: how it was run, the assessment, the tradition- and scenario-level changes
  applied, the confirmed citation corrections, and **recommendations for the other traditions and
  future ultracode runs.**
- **[ultracode-audit-rationale.md](./ultracode-audit-rationale.md)** — a one-page rationale to share
  with collaborators: why the *SynodiaBench* revisions were necessary, why a multi-agent ("ultracode")
  audit surfaced them when a single-model max-effort pass did not, and what a rerun across all
  traditions buys us (comparability + recurring error classes).
