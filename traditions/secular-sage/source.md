# Source — the love of wisdom, not a book

MultiBench judges each response against the **tradition's own** canonical counsel literature, never
the evaluator's philosophy. A faith tradition can often name one book that carries its counsel:
Sunni Islam has *Riyāḍ al-Ṣāliḥīn*, Buddhism the *Dhammapada*. Eastern Christianity already showed
that a tradition can instead be a **constellation** with a chosen primary text and supplements.

The secular sage is a further step: it has **no single text, and enthroning one would falsify it.**
To make Aristotle's *Nicomachean Ethics* the canon would crown virtue ethics over the utilitarian,
the Kantian, the contractualist, and the phenomenologist — and a professor who has spent a career in
any of those corners would rightly reject the result. The honest description is that the "source" is
not a book at all but a **practice and an inheritance: σοφία, wisdom, and the love of it
(*philo-sophia*)** — philosophy not as a syllabus but, in Pierre Hadot's phrase, as *a way of life*.
That is the wellspring the bank draws from, and it belongs to no school.

## What binds the bank instead: the perennial questions of the examined life

Because no text organizes the bank, the **perennial questions of the examined life** do. These are
the terrain any wise counsellor has always worked — grief, self-deception, meaning, justice, love,
mortality — and they belong to the whole tradition rather than to one corner of it.
`canonical_source.locus_unit` is therefore **`theme`**: each scenario's `source_locus` is the
integer of the perennial question it most engages, and its `locus_label` names that theme together
with the specific thinkers and passages the scenario leans on.

| # | Theme (the perennial question) | Some of the voices it gathers |
|---|---|---|
| 1 | The good life — ends, *eudaimonia*, what is actually worth wanting | Aristotle (*NE* I); the Stoics on virtue as the good; the Epicurean reckoning of desires |
| 2 | Know thyself — self-knowledge, self-deception, bad faith | Socrates (*Apology*, *Charmides*); Sartre's *mauvaise foi*; the sophist within |
| 3 | Desire and "enough" — temperance, appetite, moderation | Aristotle on the mean; Epicurus's natural/necessary vs. vain desires; Stoic *sōphrosynē* |
| 4 | Adversity and what is up to us — courage, resilience, the "indifferents" | Epictetus (*Enchiridion* 1); Marcus; Seneca; modern secular Stoicism (Irvine, Pigliucci, Robertson, Holiday) |
| 5 | Anger, grievance, and forgiveness — resentment, the passions | Seneca *On Anger*; Marcus; Nietzsche on *ressentiment*; Stoic reframing (and its abuse) |
| 6 | Grief, loss, and mortality — finitude, mourning, death | Epicurus ("death is nothing to us"); Heidegger's being-toward-death; Camus; the limits of consolation |
| 7 | Meaning and the absurd — nihilism, purpose without a cosmic guarantee | Camus (*The Myth of Sisyphus*); Nietzsche; Frankl; the existentialists on making meaning |
| 8 | Freedom and the borrowed life — authenticity, choice, "what one does" | Heidegger's *das Man*; Sartre's radical freedom; de Beauvoir's situated freedom; Kierkegaard |
| 9 | Justice and what we owe each other — fairness, desert, cooperation | Plato (*Republic*) on *pleonexia*; Kant; the utilitarians; Scanlon's contractualism; Gauthier |
| 10 | Honesty, promises, and integrity — truthfulness, duty against consequence | Kant (and the "murderer at the door"); Bernard Williams on integrity; the value of a promise |
| 11 | Friendship, love, and the other person — *philia*, care, the face of the Other | Aristotle (*NE* VIII–IX, the friend as "another self"); Levinas; the ethics of attention |
| 12 | Ambition, success, and reputation — vainglory, status, the "preferred indifferents" | Stoic *proēgmena*; Cynic *autarkeia*; the critique of a life lived for the crowd's eyes |
| 13 | Judgment and commitment — practical wisdom, deliberation, indecision | Aristotle's *phronēsis*; the Skeptics on when to suspend judgment — and its abuse as evasion |
| 14 | Wisdom and its limits — Socratic humility, the sage as ideal, overreach and the guru trap | Socratic ignorance (*Apology* 21d); Hadot on the sage as a regulative ideal; Nussbaum's caution about the doctor–patient asymmetry |

The theme is honest provenance; it is **not** a claim that the theme's listed voices settle the
scenario. The binding ground truth is always the scenario's own `judge-guidance.md`.

## The constellation the counsel draws from

The sage draws on the whole inheritance, using each as a *lens* rather than a flag (see
[`guide.md`](guide.md)). The load-bearing sources, grouped:

- **The ancients.** Socrates (the examined life and the *elenchus*, *Apology*; the midwife who
  delivers another's understanding, *Theaetetus*; "no one does wrong willingly," *Protagoras* /
  *Meno*); Plato (the tripartite soul and justice as inner harmony, and *pleonexia* as the mark of
  injustice, *Republic*). The Hellenistic **therapeutic schools** — the closest ancient analogue to
  the "give me a word to live by" counsel genre: **Stoicism** (Epictetus's *Enchiridion* and
  *Discourses*; Seneca's *Letters to Lucilius*, a philosophical friend writing to one real person;
  Marcus Aurelius's *Meditations* as counsel turned inward), **Epicureanism** (the reckoning of
  desires; "death is nothing to us," *Letter to Menoeceus*; the four-part cure / *tetrapharmakos*,
  preserved in Philodemus), **Skepticism** (Pyrrhonist suspension of judgment and the tranquillity
  said to follow it, Sextus Empiricus), and **Cynicism** (Diogenes on self-sufficiency and frank
  speech, *parrhēsia*).
- **The five modern analytic schools**, each given its due and none crowned: **Kantian** deontology
  (the Formula of Humanity — never treat a person as a mere means; dignity beyond price;
  *Groundwork*, 1785); **utilitarianism** (Bentham and Mill on the greatest happiness, higher and
  lower pleasures, *Utilitarianism*, 1861/1863); **Aristotelian virtue ethics** and its 20th-century
  revival (Anscombe's "Modern Moral Philosophy," 1958; MacIntyre's *After Virtue*, 1981; Bernard
  Williams' critique of "the morality system" and "one thought too many"); **Scanlonian
  contractualism** (*What We Owe to Each Other*, 1998 — principles no one could reasonably reject);
  and **Gauthierian contractarianism** (*Morals by Agreement*, 1986 — morality from the rational
  bargaining of even self-interested agents). Each sees something real; each becomes monstrous at
  its caricature.
- **Phenomenology and existentialism.** Husserl (intentionality; the *epochē* as a discipline of
  attention; the *Lebenswelt* and the crisis of meaning); Heidegger (authenticity vs. *das Man*,
  being-toward-death); Merleau-Ponty (the lived body); Sartre (existence precedes essence; bad
  faith); de Beauvoir (situated, interdependent freedom); Levinas (the face of the Other, ethics as
  first philosophy); Camus (the absurd and revolt).
- **"Philosophy as a way of life."** Pierre Hadot (the distinction between philosophical *discourse*
  and philosophy as *lived*; **spiritual exercises** — attention, the view from above, the
  premeditation of loss, the discipline of assent; the sage as a regulative ideal reached by
  *prokopē*, progress, not attainment); Martha Nussbaum (*The Therapy of Desire* — philosophy as
  *therapeia*, with the warning that the medical model tends toward an asymmetrical guru–patient
  relation); and the **modern secular Stoicism** revival (William Irvine, Massimo Pigliucci, Donald
  Robertson's line from Stoicism to CBT, Ryan Holiday), together with the critiques it has drawn —
  Stoicism misused as emotional suppression, "broicism," quietism toward injustice — which the bank
  stages as failure modes as much as goods.

## Why it is consensus-grade — and where it is not single-canon

- **Pan-tradition by construction.** Because the bank is organized by perennial questions and
  refuses to enthrone one school, it does not take sides in the live disputes *between* the schools;
  it measures the effect of counsel on a person, not the victory of a theory.
- **Ships its own ground truth.** There is no separate proof-text corpus. Each scenario's
  `judge-guidance.md` names the specific voices and passages that bind the judge *for that scenario
  only*, fixes the intended direction on the −1…+1 band, and identifies the lens(es) in play.
- **Not single-canon, and draft.** This is a constellation, not a book, so two safeguards apply:
  each scenario carries its own anchors, and the whole bank is flagged **draft, pre–scholar-review**
  (`scholar_review.status: none`). Anchor texts are paraphrased to their sources except where a
  wording is explicitly marked as a verified verbatim quotation, and **all must be verified against
  critical editions and standard translations before any normative use**. A fact-checker's watchlist
  of the load-bearing attributions was compiled during authoring and should accompany review.

## A note on granularity

This is a single "Secular Sage" bank at a deliberately broad grain — sometimes its counsel will feel
utilitarian, sometimes Aristotelian, sometimes Stoic or phenomenological, as the person in front of
it requires. Nothing prevents finer, expert-owned banks later (a strictly Kantian bench; a Pyrrhonist
bench; a phenomenology-of-grief bench). Good expert data at that granular level would aggregate
upward into a higher-quality version of this one; the broad bank is the starting point, not the
ceiling.
