# MultiBench

**MultiBench** measures whether an AI assistant is *good spiritual company* —
judged not by what it *knows* or *professes*, but by the formative effect its
counsel leaves on the person who receives it.

## How it works

MultiBench tests companionship through disguised first-person advice scenarios,
adversarial *pressures*, and *framings* that vary what the agent knows about the
user — judging each response against the tradition's **own** canonical proof
texts rather than the evaluator's. It is built from the start to host **many
traditions**, not one.

## Expandability is the core design

Each religious tradition is a self-contained, pluggable module under
[`traditions/`](traditions/). The harness (collection, judging, scoring) is
tradition-agnostic; a tradition supplies its own canonical source, scenario bank,
proof texts, and companionship guide. **Adding a tradition means adding a
directory, not changing the core.** See
[`traditions/README.md`](traditions/README.md) for the per-tradition layout.

## Repository layout

- [`traditions/`](traditions/) — pluggable per-tradition modules: **Sunni Islam**
  ([`sunni-islam/`](traditions/sunni-islam/)), **Eastern Christianity / *SynodiaBench***
  ([`eastern-christianity/`](traditions/eastern-christianity/)), **Taoism / *TaoBench***
  ([`taoism/`](traditions/taoism/)), **Buddhism / *MittaBench*** ([`buddhism/`](traditions/buddhism/)),
  **Judaism / *MiddotBench*** ([`judaism/`](traditions/judaism/)), and **Secular Sage /
  *SophiaBench*** ([`secular-sage/`](traditions/secular-sage/)).
- [`apps/`](apps/) — applications and standalone tools (e.g. `jaleesbrowser`,
  and the `tradition_validator`).
- [`workflows/`](workflows/) — pipelines such as judging and scenario generation.

## Status

The tradition **format** is defined and documented
([`traditions/README.md`](traditions/README.md)), the **`tradition_validator`** is built
([`apps/tradition_validator/`](apps/tradition_validator/)), and **six traditions** are in
the canonical format and validate clean: **Sunni Islam** (140 scenarios), **Eastern Christianity /
*SynodiaBench*** (106), **Taoism / *TaoBench*** (48), **Buddhism / *MittaBench*** (52), **Judaism /
*MiddotBench*** (48), and **Secular Sage / *SophiaBench*** (49) — 443 scenarios in all. Four of the
six were revised and expanded in a multi-agent
[plurality ultracode audit](docs/analysis/plurality-ultracode-audit.md); all remain
`scholar_review: none` pending review by scholars of each tradition. The **harness** (collection,
judging, scoring) and a scenario-generation workflow are not yet migrated in.

MultiBench generalizes [JaleesBench](https://github.com/iaser-ai/jaleesbench),
which instantiated this construct for Sunni Islam.
