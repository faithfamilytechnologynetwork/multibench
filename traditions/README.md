# Traditions

MultiBench is built around one expandability axis: the **tradition**. Each
tradition is a self-contained directory here. The core harness is
tradition-agnostic and discovers traditions from this directory; adding a new
one should require **no changes to the core**.

## Adding a tradition

Create `traditions/<tradition>/` containing the following (this layout is a
*starting proposal* — expect to refine it as the harness is ported from
JaleesBench):

| File | What it holds |
|------|---------------|
| `tradition.yaml` | metadata: name, language(s), canonical source, maintainers, scholar-review status |
| `source.md` | the canonical virtue/conduct compilation used as ground truth, and why it is consensus-grade for this tradition |
| `probes.json` | disguised first-person advice scenarios, one per measurement cluster |
| `proof_texts.json` | the canonical texts each probe is judged against (the judge is anchored to these, never its own jurisprudence) |
| `guide.md` | the one-page companionship guide used in the Guided framing |
| `pressures.json` | per-probe authored pressure pushes (or inherit shared defaults) |

**The recipe** (from JaleesBench): take a tradition's canonical virtue
compilation, cluster its chapters into distinct measurements, author one
disguised first-person probe per cluster, and judge against that chapter's own
proof texts rather than the evaluator's. Each new tradition needs a comparable
canonical source and qualified reviewers for that tradition, which sets the
pace of expansion.

## Open design questions (deliberately unresolved)

- Are *pressures* and *framings* fully shared (tradition-agnostic) or partly
  authored per tradition?
- Is `tradition.yaml` or a Python registry the source of truth for discovery?
- Multilingual handling (JaleesBench ran English + Arabic per tradition).
- How scoring normalizes across traditions with different proof-text densities.

These stay open until the harness is ported and we have a second tradition to
test the abstractions against.
