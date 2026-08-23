# Codebook — comparing the columns (pre-registered)

Committed before any answers were generated. The unit of coding is **one question**: the seven
columns' `## Counsel` fields for that question, pseudonymised R1–R7 and order-shuffled, with
`silence: true` responses shown as `SILENT` (excluded from clustering, recorded).

## Primary outcome — advice similarity (coded blind, double-coded)

For each question the coder produces:

1. **`clusters`** — a partition of the non-silent responses into groups whose *concrete advice is
   practically interchangeable*: a person following any response in the group would do
   substantially the same things. Test: actions recommended, actions warned against, and what the
   person is told to seek or stop. Wording, warmth, and vocabulary differences do NOT split a
   cluster; a different recommended action, permission vs prohibition, or a materially different
   priority order DOES.
2. **`severity`** — the relationship between clusters when there is more than one:
   - `same` — one cluster: all non-silent counsel practically interchangeable.
   - `emphasis` — clusters differ in weight, sequence, or pastoral accent, but no response
     permits what another forbids and a person could follow any of them without disobeying the
     rest.
   - `substance` — at least one response recommends or permits an action another forbids or
     materially warns against, or gives concretely different instructions for what to do.
3. **`outliers`** — for `emphasis`/`substance`: which pseudonyms sit outside the largest cluster.
4. **`silent`** — the pseudonyms marked SILENT.
5. **`rationale`** — one or two sentences naming the concrete difference (or the shared core).

**Decision rules.** Code the *advice*, not the reasoning — a response that reaches the same
"tell your husband this week, with help lined up" through covenant theology and another through
discipleship language are the SAME cluster. Conditional advice ("if X then A, else B") clusters
with responses sharing the same dominant branch; note the conditional in the rationale. When
genuinely torn between `emphasis` and `substance`, ask: *could one pastor give both counsels to
the same person without retracting either?* Yes → `emphasis`. No → `substance`.

Each question is coded by two independent coders; disagreements (any difference in `severity`,
or a materially different partition) go to a third adjudicator whose coding is final.
**Agreement reported** as: exact severity match rate, and exact partition match rate.

## Secondary outcome — grounding similarity (coded unblinded, after primary)

Per question, across the columns: `grounding` ∈

- `shared` — the columns ground counsel in substantially the same places (the same Scripture
  and/or doctrinally equivalent loci: e.g. each strand's own Decalogue exposition of the same
  commandment).
- `parallel` — different strand-specific loci doing the same doctrinal work.
- `divergent` — the groundings themselves make different doctrinal claims relevant to the case.

The study's central cell is **advice `same`/`emphasis` × grounding `parallel`/`divergent`** —
same guidance from different theology.

## Derived quantities (computed by `analyze.py`, not coded)

- Headline: share of questions at each severity (of adjudicated codings).
- **D** — the substantive-divergence share: `substance` questions / all questions. This is the
  quantity `pathway-rule.md` binds.
- Per-domain severity rates.
- Pairwise strand agreement matrix: for each pair, share of questions (both non-silent) where the
  pair share a cluster.
- Per-strand outlier and silence counts.
- The 2×2 of advice × grounding.
