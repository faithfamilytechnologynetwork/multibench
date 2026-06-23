# MultiBench

**MultiBench** measures whether an AI assistant is *good spiritual company* —
judged not by what it *knows* or *professes*, but by the formative effect its
counsel leaves on the person who receives it.

## Derived from JaleesBench

MultiBench is the cross-tradition generalization of **JaleesBench**
(github.com/iaser-ai/jaleesbench), which instantiated this construct for Islam
(Arabic *al-jalīs al-ṣāliḥ*, "the righteous companion"). It keeps JaleesBench's
method — disguised first-person advice scenarios, adversarial *pressures*,
*framings* that vary what the agent knows about the user, and judging anchored
to each tradition's **own** canonical proof texts — but is built from the start
to host **many traditions**, not one.

## Expandability is the core design

Each religious tradition is a self-contained, pluggable module under
[`traditions/`](traditions/). The harness (collection, judging, scoring) is
tradition-agnostic; a tradition supplies its own canonical source, probe bank,
proof texts, and companionship guide. **Adding a tradition means adding a
directory, not changing the core.** See
[`traditions/README.md`](traditions/README.md) for the per-tradition layout.

- The tradition-agnostic harness will live in a `multibench/` package (to be
  ported from JaleesBench).
- Islam is the first instance: [`traditions/islam/`](traditions/islam/).

## Status

Bootstrap. This repo currently holds the Codev project setup and the expandable
directory structure; the harness and the Islam port are not yet migrated in.
