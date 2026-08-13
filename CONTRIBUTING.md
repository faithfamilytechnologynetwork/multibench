# Contributing to MultiBench

Most work here runs through the **Codev** builder machinery (a porch-driven worktree that
produces the spec/plan/review trail automatically). This page is for the other path: **external
or collaborator contributions made directly** — including AI-assisted sessions editing the repo
without that machinery.

## The tier rule

**Feature-scale changes must ship with three documents in the same PR.** Rough guide for
"feature-scale": **more than ~300 lines**, or **any new user-facing surface** (a page, command,
endpoint, or dataset tier).

| Document | Path | Captures |
|---|---|---|
| **Spec** | `codev/specs/<PR#>-<name>.md` | WHAT: problem, goals, success criteria, constraints, open questions |
| **Plan** | `codev/plans/<PR#>-<name>.md` | HOW: phases, files touched, test strategy (as-built is fine) |
| **Review** | `codev/reviews/<PR#>-<name>.md` | What happened: verification evidence, deviations, lessons (may start as a stub, completed after review) |

Name the files after the PR number once it exists. **Small fixes and pure docs are exempt** —
no Codev documents required.

**Retro-authoring is acceptable.** If the code landed first, write the documents afterward and
mark each **"retrospective"** at the top so readers know the spec followed the code.

## Templates to mirror

Reuse the structure of these committed examples rather than inventing your own:

- Spec — [`codev/specs/54-multibrowser-afb-before-after-.md`](codev/specs/54-multibrowser-afb-before-after-.md)
- Plan — [`codev/plans/54-multibrowser-afb-before-after-.md`](codev/plans/54-multibrowser-afb-before-after-.md)
- Review — [`codev/reviews/48-multiweights-omissive-bias.md`](codev/reviews/48-multiweights-omissive-bias.md)

The pull request template's **Codev governance docs** checklist is the reminder at PR time.
AI sessions: see the "Contributing WITHOUT the builder machinery" section of `CLAUDE.md` /
`AGENTS.md` for the same rule addressed to you.
