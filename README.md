# MultiBench

**MultiBench** measures whether an AI assistant is *good spiritual company* —
judged not by what it *knows* or *professes*, but by the formative effect its
counsel leaves on the person who receives it.

## How it works

MultiBench probes companionship through disguised first-person advice scenarios,
adversarial *pressures*, and *framings* that vary what the agent knows about the
user — judging each response against the tradition's **own** canonical proof
texts rather than the evaluator's. It is built from the start to host **many
traditions**, not one.

## Expandability is the core design

Each religious tradition is a self-contained, pluggable module under
[`traditions/`](traditions/). The harness (collection, judging, scoring) is
tradition-agnostic; a tradition supplies its own canonical source, probe bank,
proof texts, and companionship guide. **Adding a tradition means adding a
directory, not changing the core.** See
[`traditions/README.md`](traditions/README.md) for the per-tradition layout.

## Repository layout

- [`traditions/`](traditions/) — pluggable per-tradition modules; Sunni Islam is
  the first ([`traditions/sunni-islam/`](traditions/sunni-islam/)).
- [`apps/`](apps/) — applications and standalone tools (e.g. `jaleesbrowser`,
  and the `tradition_validator`).
- [`workflows/`](workflows/) — pipelines such as judging and probe generation.

## Status

Bootstrap. This repo currently holds the Codev project setup and the expandable
directory structure; the harness and the Sunni Islam port are not yet migrated in.

MultiBench generalizes [JaleesBench](https://github.com/iaser-ai/jaleesbench),
which instantiated this construct for Islam.
