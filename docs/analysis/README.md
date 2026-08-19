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
- **[protestantbench-inside-church-parity.md](./protestantbench-inside-church-parity.md)** — the
  comparative "inside church" parity audit of **protestantism** (*ProtestantBench*), run against a
  reader's report that "almost all the scenarios are for people already in the church rather than
  life situations." A **no-edits pass** built on a full **619-scenario census of all eight
  traditions** (setting, institutional entanglement, audience reach, the person's own church role)
  plus both scored runs: ProtestantBench is 39% church-interior against a corpus median of 11%, 40%
  of its people hold a church role against 3%, and only 11% of its scenarios have no religious
  institution in the frame against 67%. It adjudicates the two offered hypotheses (**too many source
  texts** — right about the harm, wrong about the route; **hard to rationalise across sub-traditions**
  — a real mechanism but not an inevitability, since roman-catholicism runs a comparable family axis
  at 60% intrinsic without the tilt), names the three proximate causes the report did not
  (a mandatory `office` axis unique to this tradition, a declared 66%-intrinsic quota, and a
  credentialed-opener house style at 31% against ≤6% elsewhere), and shows the two separable costs:
  a **collapsed Stated axis** (the bare adherent-noun prefix recovers 0.27 of what the guide
  recovers, against a floor-regime peer mean of 0.80, because the axis discriminates on `clean`
  scenarios and this bank has eight — while the setting effect on the Unstated level does not survive
  controlling for register, so the case for de-churching the bank is a construct argument rather than
  a score argument) and a **0.461 confessional-family gradient** under the Guided framing
  (lutheran 0.79 → methodist 0.32) that replicates on both judges and in nine of ten judge × model cells, next
  to 0.158 for roman-catholicism's seven schools — with `guide.md` containing the word *Baptist*
  zero times. It also opens by stating the strongest case *against* itself — that an ecclesial bank is the
  correct instantiation of a congregational tradition — and adjudicates it; and it turns up a
  neutrality breach in the module's own `guide.md`, whose universal assurance paragraph grounds
  itself in the Canons of Dort on perseverance, which the Thirty-Nine Articles and Wesley both deny.
  Ends with parity targets (a 42/42/42 bank of 126 in three moves), a pre-registered success bar for
  the re-run, the honest limits, and the 619 census codings at
  [`data/protestantbench-census.csv`](./data/protestantbench-census.csv).
- **[protestantbench-life-parity-prompt.md](./protestantbench-life-parity-prompt.md)** — the
  executable artifact from that audit: a self-contained refinement prompt for an authoring pass,
  with the non-negotiables (the construct, the intra-Protestant non-adjudication rule, universal
  core, the overlays, *author don't re-tag*), the composition and setting targets, the two rules that
  do the work (**a scenario must be statable in one sentence with no church noun in it**; **the
  opener carries the trouble, not the credentials**), the four ways to keep a `communion` tag legible
  for someone who has not been in a pew for two years, the seed inventory for the new tranche, and
  the three structural changes — `office: none`, the `guide.md` family rebalance, and the length
  reset.
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
- **[tradition-reviewer-guide.md](./tradition-reviewer-guide.md)** — the reference guide for
  **human expert reviewers** using MultiBrowser's reviewer-workspace prototype (`/review`): who
  should review, the three steps (canonical source → companionship guide → a ten-scenario sample
  with four checks each: scenario, scoring guide, judges' verdicts, pressure points), how intake is
  retained locally and submitted (GitHub issues labeled `tradition-review`, or a downloadable
  Markdown report), and a maintainer section on aggregating reviews toward each tradition's
  `scholar_review` status.
- **[ultracode-audit-rationale.md](./ultracode-audit-rationale.md)** — a one-page rationale to share
  with collaborators: why the *SynodiaBench* revisions were necessary, why a multi-agent ("ultracode")
  audit surfaced them when a single-model max-effort pass did not, and what a rerun across all
  traditions buys us (comparability + recurring error classes).
