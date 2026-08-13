# Tradition Reviewer Guide

*Reference for the reviewer-workspace prototype (`/review` in MultiBrowser). Written for the
human expert doing the reviewing; a closing section addresses maintainers.*

---

## Why your review matters

MultiBench measures whether AI assistants, when a person of faith brings a real dilemma **and is
then pushed to compromise**, give counsel that stays faithful to that person's tradition. Every
scenario, every scoring guide, and every judge verdict in the benchmark makes a claim about what
*your* tradition actually teaches. Those claims need checking by someone with standing in the
tradition — that is the whole job of this review. You are not reviewing code, and you do not need
any technical background: everything happens in the browser, reading the same materials the
benchmark uses.

**Who should review:** an adherent with recognized formation in the tradition being reviewed — a
pastor, priest, imam, rabbi, teacher, monastic, or academic. Please review only traditions you
have real standing in, and say what that standing is in the workspace's *Background* field: the
maintainers weigh reviews by it.

## Where to work

Open the **Review** tab of MultiBrowser (`/review`). The workspace walks you through everything
below and keeps your answers **in your own browser** as you type — nothing is sent anywhere until
you explicitly submit. You can stop and come back any time on the same device/browser. (Use the
*Back up all my reviews (JSON)* button if you want to move your work between devices.)

Each item you review gets the same three-part answer:

- a verdict — **Looks right** or **Needs changes** (click again to retract);
- **Notes** — what you found, ideally with chapter/verse or section citations;
- **Suggested revision** (optional) — your replacement wording, carried verbatim into the report.

Every item also links *propose an edit on GitHub*: if you have a GitHub account, that opens the
actual file in GitHub's editor (it forks automatically) so you can submit a concrete fix directly.

## The three steps

### 1 · Review the scenario source

Each tradition draws all of its scenarios from **one canonical text** (for example, Sunni Islam
uses al-Nawawī's *Riyāḍ al-Ṣāliḥīn*), described in the tradition's `source.md`. Ask:

- Is this a **consensus-grade** source — read across the tradition's schools and regions, not the
  banner of one party in a live intra-tradition dispute?
- Is the description of the source accurate and fair (authorship, standing, what it contains)?
- Is it the *right kind* of source for judging everyday counsel on character and conduct?

### 2 · Review the guide

The tradition's `guide.md` is its **companionship guide**: a one-page description of what an AI
companion that leaves a person *better off, by this tradition's lights* looks like. It matters
twice — it states the construct being measured, and it is verbatim the system prompt models
receive in the benchmark's "Guided" condition. Ask:

- Does it reflect how your tradition understands a good influence on a person — not generic
  niceness, and not a caricature of strictness?
- Are its dos and don'ts actually the tradition's (right sources, right emphases, right tone)?
- Is anything essential missing — something the tradition would insist a good companion must do
  (or never do) that the guide fails to say?

### 3 · Review your ten scenarios

Traditions carry 48–140 scenarios; you are assigned a **sample of ten**, spread evenly across the
corpus. (You can reshuffle the sample or add specific scenarios — the workspace records which set
and, if shuffled, the seed, so your report says exactly what you looked at.) For each scenario,
work the four checks in order:

**a — Start with the scenario.** The user's opening message, anchored to a specific passage of
the canonical source (the *locus*, shown above it). Is the dilemma real — something an adherent
would actually bring? Is it well-posed (a genuine tension, not a trick)? Does it genuinely belong
to the passage it cites?

**b — Check the scoring guide.** Each scenario has a `judge-guidance` note: the **binding ground
truth** the AI judges score against — the relevant rulings, proof texts, permissible exceptions,
and what good counsel here must and must not do. This is the single most consequential thing you
will review: a wrong ruling here silently mis-scores every model. Check citations, check the
rulings, and especially check the *exceptions* (the benchmark's pressure pushes often misuse a
genuine exception — the guidance must state the real one correctly).

**c — Check the judges' verdicts.** The workspace shows real model answers with the judges'
scores and rationales interleaved — **Gemini** scores every transcript (it is the ranking judge);
**Opus** validates a sample. Pick a model, read its first answer and its post-pressure answer,
and read the verdict against the scoring guide you just reviewed. Do the scores track fidelity to
the tradition, or something else (eloquence, hedging, length)? Cite the model + framing +
pressure for any verdict you dispute. Two or three well-read cells are worth more than twenty
skimmed ones.

**d — Check the pressure points.** After the model's first answer, the user pushes back six
canonical ways — *secularize, insistence, false authority, good cause, flattery, personal
appeal* — each with scenario-specific wording. Are the pushes realistic (how a person would
actually push), fairly worded (a live temptation, not a strawman), and is the "false authority"
actually false / the "good cause" actually the misuse the guidance says it is?

## Submitting

The **Submit your review** panel turns everything you recorded into a Markdown report — reviewer,
verdicts, notes, suggested revisions, with links to the exact file versions you reviewed. Preferred
route: **Open a prefilled GitHub issue** (one click; the issue is labeled `tradition-review`). If
the report is too long for a prefilled URL, the workspace tells you — use *Copy report*, open the
blank issue, and paste. No GitHub account? *Download report (.md)* and send it to the maintainers
any way you like.

A few habits that make reviews land well:

- **Cite loci.** "JLS-054's guidance misstates the exception in bab 254" beats "some rulings seem
  off."
- **Flag school/communion differences instead of adjudicating them.** If your tradition's schools
  genuinely differ on a point, say so — the benchmark's posture is to stay on consensus ground,
  and "this point is disputed between X and Y" is exactly what the maintainers need to hear.
- **Say what's right, too.** "Looks right" verdicts with a short note are evidence, not filler —
  they tell the maintainers which parts carry scholarly sign-off.

## For maintainers

- Intake arrives as GitHub issues labeled `tradition-review` (aggregate with
  `gh issue list --label tradition-review`), or as emailed `.md` reports from reviewers without
  GitHub accounts. Reports link every reviewed file at the reviewed commit SHA and record the
  scenario sample (and shuffle seed), so coverage across reviewers is computable.
- The workspace stores reviewer state client-side under the localStorage key
  `multibench.review.v1` (schema in `apps/multibrowser/src/lib/review.ts`); the report and
  issue-URL builders live in `apps/multibrowser/src/lib/reviewReport.ts`. There is deliberately **no backend** — the
  SPA stays static; GitHub issues are the durable store. If server-side collection is ever wanted,
  the submit seam is the only thing to replace.
- Completed reviews are the natural input for a tradition's `scholar_review` block in
  `tradition.yaml` (`status`, `reviewers`) — today `none` across the corpus; this workflow exists
  to change that.
