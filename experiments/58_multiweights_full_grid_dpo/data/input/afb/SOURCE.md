# AllFaith Benchmark — Religious Representation (vendored)

Source: `github.com/CEFEAI/allfaith-religious-representation` (MIT, see `LICENSE`).
Cloned & vendored 2026-08-04 for reproducibility of experiment 48.

- `questions.jsonl` — 150 secular life questions where a US survey (n≈1,125) said
  respondents would expect a religious perspective. Fields: `id`, `question`.
- `scoring_prompt.json` — the official LLM-as-judge template, 0–4 religious-representation
  scale + JSON output contract (`{rationale, score}`). This is the headline judge of record
  and is reused verbatim by the over-application probe suite (`../../../probes/`).

We vendor only these two small MIT-licensed files, not the full repo. Judge-of-record model
for scoring is an open decision (spec §7.2: Terra or Sonnet-5 — must differ from our
gemini pipeline judge for independence).
