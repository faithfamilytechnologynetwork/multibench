# Spec 1 — Rebuttal to iteration-2 3-way review (restructured spec)

**Reviews:** Gemini **APPROVE**, Claude **APPROVE**, Codex **REQUEST_CHANGES** — all HIGH.

**Disposition:** every Codex point and every minor suggestion from the two approvers was
**ACCEPTED and incorporated**. No disagreements. The full mapping is in the spec's §10
Consultation Log; this file is the porch-facing record.

## Codex REQUEST_CHANGES (5)
1. **Unknown-keys policy unstated** → declared **closed schemas**: unknown keys in
   `tradition.yaml`/`probe.yaml`/`index.json` are errors (§5.2 "Schema strictness",
   §8.2 checks 2/4/5; test T16).
2. **`pressures.md` heading normalization underspecified** → defined the exact rule
   (strip → lowercase → spaces/hyphens → `_`, must equal a canonical pressure id) (§5.6).
3. **Per-probe `tags` contract loose** → tightened from `⊆` to `==` declared axes, each
   list non-empty, no intra-axis duplicates. Verified safe against the real 140-probe
   bank (all have non-empty pillars 1–3 and hearts 2–5) (§5.4, §8.2 check 5; tests
   T2/T18).
4. **Port completeness not required** → M2 now requires the **complete 140-probe** port;
   a partial port does not satisfy.
5. **Security behaviors untested** → added negative tests T14 (symlink escape) and T15
   (oversized/truncated input) for the N4 requirements.

## Approver minor suggestions (Gemini / Claude) — also incorporated
- **YAML bool coercion** (both) → strict typing; bare `no`→false is a type error
  (§5.2, §8.2 check 8; test T19).
- **Ignore system files / warn on typos** (Gemini) → dotfiles ignored; unexpected
  non-dot files warned (§8.2 checks 4–5).
- **`--format json` shape** (Gemini) → defined `{tradition, ok, findings:[{severity,
  file, path, message}]}` (§8.3).
- **UTF-8 encoding** (Claude) → stated; decode failure = located error (§5.2, §8.2).
- **Empty `tradition.yaml` (null) + missing-axis tests** (Claude) → T16–T18.
- **`index.json` `schema_version` starts at 1** (Claude) → confirmed (§5.1).
- **Preamble before first `##` in `pressures.md`** (Claude) → allowed, ignored (§5.6).

## Acknowledged strengths (kept)
Both approvers endorsed the file-based structure, the universal-core framings/pressures
decision, the strengthened judge seam (§5.5 — `judge-guidance.md` eliminates corpus drift
by construction), the worked example (§5.8), and the port delta table (§6). No changes.
