# Sunni Islam

The first MultiBench tradition, in the canonical file-based format (ported from JaleesBench,
github.com/iaser-ai/jaleesbench).

- **Construct:** *al-jalīs al-ṣāliḥ* (the righteous companion) — judged by the residue an
  exchange leaves on the user, in the manner of the prophetic hadith of the perfume-seller
  and the blacksmith.
- **Canonical source:** *Riyāḍ al-Ṣāliḥīn* (al-Nawawī) — see [`source.md`](source.md).
- **Guide:** the Guided-framing companionship guide is in [`guide.md`](guide.md).
- **Scenarios:** scenario folders under [`scenarios/`](scenarios/), each with `scenario.yaml`,
  `turn1.md`, `judge-guidance.md`, and `pressures.md` (one section per core pressure).

Framings (unstated / stated / guided) and the six pressures are universal core; the only
faith-specific framing inputs here are `adherent_noun` (Stated) and `guide.md` (Guided).

Validate from the repo root:

```bash
uv --project apps/tradition_validator run python -m tradition_validator validate traditions/sunni-islam
```
