# Sunni Islam

The first MultiBench tradition, ported from **JaleesBench**
(github.com/iaser-ai/jaleesbench). The id is `sunni-islam` because the canonical
source — *Riyāḍ al-Ṣāliḥīn* (al-Nawawī) — is a Sunni compilation.

- **Construct:** *al-jalīs al-ṣāliḥ* (the righteous companion), judged in the
  manner of the prophetic hadith of the perfume-seller and the blacksmith — by
  the residue an exchange leaves on the user.
- **Canonical source:** *Riyāḍ al-Ṣāliḥīn* (al-Nawawī) — 372 chapters, each
  shipping its own Qurʾān-and-hadith proof texts.

## To port from JaleesBench

The canonical layout is defined in [`../README.md`](../README.md) and Spec 1
(`codev/specs/1-traditions-folder-layout-spec-.md`) — file-based: prose in
Markdown, metadata in small YAML, one folder per probe.

- [ ] `tradition.yaml` metadata (id, display_name, construct, canonical_source,
      `adherent_noun`, maintainers, scholar_review, taxonomies, probe_id_pattern)
- [ ] `source.md` — *Riyāḍ al-Ṣāliḥīn* and why it is consensus-grade
- [ ] `guide.md` — the one-page companionship guide (Guided framing)
- [ ] `probes/` — 140 probe folders (`JLS-001/` …), each with `probe.yaml`,
      `scenario.md`, `judge-guidance.md`, `pressures.md`; plus `probes/index.json`

Framings (unstated / stated / guided) and the six pressures are **universal core**,
not per-tradition. The only faith-specific framing input here is `adherent_noun`
(for the Stated framing) and `guide.md` (for the Guided framing).

Not yet migrated.
