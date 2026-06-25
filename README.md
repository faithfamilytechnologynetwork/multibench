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
  ([`traditions/sunni-islam/`](traditions/sunni-islam/)) and **Eastern Christianity /
  *SynodiaBench*** ([`traditions/eastern-christianity/`](traditions/eastern-christianity/)).
- [`apps/`](apps/) — applications and standalone tools (e.g. `jaleesbrowser`,
  and the `tradition_validator`).
- [`workflows/`](workflows/) — pipelines such as judging and scenario generation.

## Status

The tradition **format** is defined and documented
([`traditions/README.md`](traditions/README.md)), the **`tradition_validator`** is built
([`apps/tradition_validator/`](apps/tradition_validator/)), and **two traditions** are ported
into the canonical format and validate clean: **Sunni Islam** (140 scenarios,
[`traditions/sunni-islam/`](traditions/sunni-islam/)) and **Eastern Christianity /
*SynodiaBench*** (100 scenarios, [`traditions/eastern-christianity/`](traditions/eastern-christianity/)).
The **harness** (collection, judging, scoring) and a scenario-generation workflow are not yet
migrated in.

MultiBench generalizes [JaleesBench](https://github.com/iaser-ai/jaleesbench),
which instantiated this construct for Sunni Islam.
