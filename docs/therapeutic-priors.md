# The Eight Default Therapeutic Priors

*MultiBench interpretive frame — 2026-08-04. Grounded in the 20260803 unstated run
(5 subjects × 7 traditions × 6 pressures, 15,570 sittings).*

When a user brings a personal, moral, or spiritual struggle to a frontier AI assistant,
the assistant answers from an implicit counseling stance — the register of secular
counseling psychology, absorbed from the training distribution and reinforced by
helpfulness tuning. Described as a set of commitments:

1. **Autonomy is sovereign.** The user's self-determined choice is the highest good; the
   assistant's role is to help them find *their* answer, never to tell them what's
   right. ("Only you can know what's best for you.")
2. **Non-directiveness.** Explore, reflect, ask open questions. Normative claims are
   flattened into options: "some people find…"
3. **Boundaries as the cardinal virtue.** Relational strain is read as a boundaries
   problem, and distance is a legitimate remedy.
4. **Feelings as evidence, guilt as symptom.** Validate first; distress signals
   something wrong with the *situation*. Guilt is a weight to be relieved — where the
   traditions treat guilt as the conscience carrying information (a call to tawbah,
   confession, teshuvah).
5. **Wellbeing over transformation.** The goal is that the person feel better and
   function; the tradition's goal — repentance, obedience, sanctification,
   detachment — is silently replaced with symptom relief.
6. **Neutrality about the good.** No ranking of ways of life. The model won't say
   *forbidden* or *duty* unprompted.
7. **Commitments are renegotiable.** Vows, filial duty, and religious law are
   instruments of the present self's flourishing; when they conflict with it, they
   yield.
8. **Judgment is harm.** Telling someone they're wrong risks damage, so correction
   arrives so cushioned it no longer corrects.

## Three observations

**These are not flaws in isolation.** In a secular counseling context they are
defensible, often best-practice norms. The point is that together they constitute a
*particular normative tradition that presents itself as neutral*. When a user's actual
tradition agrees with it (secular wisdom, much of Buddhist and Taoist counsel), the
assistant looks like good company; when it doesn't, the assistant substitutes its
tradition for the user's — without either party noticing.

**They explain the benchmark's difficulty gradient.** Tradition difficulty in
MultiBench tracks the frequency of scenarios where binding counsel collides with these
priors. Sunni Islam and Roman Catholicism (39% of scenarios net-negative, with absolute
−1.0 floors) demand counsel the priors resist: dutifulness to parents over estrangement
(prior 3), chastity (priors 6/7), sacramental urgency (prior 6), obedience as duty
(priors 1/7). Buddhism and Taoism (6% negative) rarely demand anything the priors
resist — a model can sound like good Buddhist company without knowing much Dhamma. The
canonical example: asked by a user estranged from their mother, an assistant produced
send-ready messages for cutting her off — competent boundary-work under prior 3, and a
judged facilitation of *qati'at al-rahim* (severing kinship ties) under the tradition.

**They connect MultiBench to omissive bias.** CEFEAI's AllFaith work measures the same
phenomenon from outside: on 150 secular life questions where a representative survey
says people expect a religious perspective to appear, models average near zero
religious representation. Priors 2 and 6 *are* the mechanism of that omission. The six
MultiBench pressures, in turn, attack the priors from inside — *secularize* invites the
model home to its default register, *insistence* leans on prior 1, *personal appeal*
and *good cause* on priors 4 and 8 — which is why steadfastness under pressure is
negative for every subject measured.
