# Spec 1 — Rebuttal to iteration-1 3-way review

**Reviews:** gemini (REQUEST_CHANGES), codex (REQUEST_CHANGES), claude (REQUEST_CHANGES) —
all HIGH confidence.

**Disposition:** every point **ACCEPTED and incorporated** into the spec (commit
`[Spec 1] Specification with multi-agent review`). No disagreements. The findings were
unanimous and all WHAT-level (format-contract) gaps that correctly belong in the spec.
The full point→change mapping also lives in the spec's §10 Consultation Log; this file is
the porch-facing record.

---

## Blocking issues (KEY_ISSUES)

### 1. `probe_id_pattern` missing from the manifest *(gemini, codex, claude)*
**Accepted.** The spec required the validator to check probe ids against a tradition's
pattern "without hardcoding" (§8.2, S3) but defined no field to read it from.
**Changed:** added required `probe_id_pattern` (regex) to the `tradition.yaml` schema
(§5.2). §5.4's probe `id` row and §8.2 check 4 now reference it; §8.2 check 2 validates
it compiles. Islam declares `^JLS-\d{3}$`.

### 2. `stated_framing_sentence` had no home; "resolvable" too vague *(gemini, codex, claude)*
**Accepted.** §5.6 said a stated sentence "must be resolvable" without saying from where.
**Changed:** added `stated_framing_sentence` to the manifest (§5.2), **conditionally
required** when `stated` ∈ `framings`, overridable by `pressures.json` (§5.6.1).
Deliberately **rejected Gemini's suggested templated default** (synthesizing from
`display_name`): repo policy is fail-fast / no fallbacks, so an absent-but-required
sentence is a hard error, not a silently-templated guess. (This is the one place I
diverged from a *specific recommendation*, while still satisfying the underlying issue —
giving the sentence a single defined home.)

### 3. `pressures.json` schema undefined *(gemini, codex, claude)*
**Accepted.** **Changed:** added §5.6.1 defining the file's schema
(`{pressures: {<name>: {description}}, stated_framing_sentence?}`) and a precise
**resolved-pressure-set precedence**: `pressures.json` keys → else manifest list → else
shared defaults; probe `pressure_turns` keys and `probes.json` top-level `pressures` are
validated against that resolved set.

### 4. `guide.md` REQUIRED vs conditionally required *(gemini, codex, claude)*
**Accepted.** **Changed:** §5.1 now marks `guide.md` **CONDITIONALLY REQUIRED** (iff
`guided` ∈ `framings`), matching §5.6 and §8.2 check 6.

### 5. `source_map.json` checked for integrity but unspecified *(codex, claude)*
**Accepted.** **Changed:** added §5.8 defining its schema (`{source, loci:[{id, label,
…}]}`). §6's port row changed from "carry as-is" to a light reshape
(`chapters[].bab`→`loci[].id`, `english`→`label`). §8.2 check 8 checks
`source_locus ∈ {loci[].id}` only when the file is present.

---

## Additional issues raised in detailed feedback

### 6. `probes.<lang>.json` sparse-vs-full ambiguity *(gemini, claude)*
**Accepted** (both recommended sparse). **Changed:** §5.9 defines the **sparse** schema —
only `{schema_version, probes:[{id, turn1, pressure_turns}]}`; non-translatable fields are
omitted and `probes.json` is authoritative. Validator checks `<lang>` ∈
`languages.others`, id-parity, and `pressure_turns` key-parity.

### 7. `components` manifest field shape undefined *(claude)*
**Accepted.** **Changed:** §5.2 defines `components: {source_map: bool, pressures: bool,
language_variants: [<code>]}`; §8.2 check 1 cross-checks declarations vs disk (drift =
warning, error under `--strict`).

### 8. `name` vs `id` redundancy *(claude)*
**Accepted** (drop `name`). **Changed:** removed `name` from the manifest; `id` (machine,
= dirname) + `display_name` (human) cover both. Examples updated (§5.2, §5.7).

### 9. `--format text|json` vs `--json` inconsistency *(claude)*
**Accepted** (favor `--format`). **Changed:** S2 now reads `--format json` to match §8.1.

### 10. JaleesBench data unreachable in a sandboxed build *(gemini, codex, claude)*
**Accepted** — real feasibility risk for Plan/Implement. **Changed:** added §3.3b
"Build prerequisite": the Plan's first phase fetches the source via `gh api` raw reads
(verified working during this spec's research) into gitignored `tmp/jaleesbench-source/`;
fallback is architect-staging the same path if a run is network-restricted. The plan owns
the mechanics.

### 11. Security/robustness *(codex)*
**Accepted.** **Changed:** added §8.2 check 10 and NFR N4 — YAML **safe-load only**,
never execute/import a tradition file, reject symlink/path-traversal escapes from the
tradition dir, and emit located errors (not tracebacks) on malformed/oversized inputs.

### 12. More test cases *(codex, claude)*
**Accepted.** **Changed:** added T9–T13 — invalid YAML/JSON syntax, duplicate taxonomy
values, `components` drift, undeclared language code, and missing stated sentence.

### 13. Two `schema_version`s unexplained *(claude)*
**Accepted.** **Changed:** clarified that the manifest's `schema_version` is the
module-format version and `probes.json`'s is the bank-schema version, independently
evolvable (§5.2, §5.4).

### 14. `applies_to` semantics unstated *(claude)*
**Accepted.** **Changed:** §5.3 now explains `scenario` vs `response` and notes the
validator only checks the value ∈ {scenario, response}; the distinction is informational
provenance for downstream tooling.

---

## Reviewer-acknowledged strengths (kept as-is)
The §5.5 **proof-text seam** (judge anchors to each probe's embedded `proof_texts`
string, not a corpus lookup; evidenced by JLS bab 261 absent from `proof_texts.json` yet
valid) was independently called the standout by Claude and "particularly good … materially
reduces risk of a wrong validator" by Codex. The generic-names principle, Approach-C
selection, §6 porting deltas, and §8.3 error-message contract were endorsed. No changes.
