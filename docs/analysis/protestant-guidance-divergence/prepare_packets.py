#!/usr/bin/env python3
"""Build blind coding packets from the strand worksheets.

Per question: extract each strand's `## Counsel` section, pseudonymise strands as
R1..R7 with a per-question seeded shuffle, and write one packet file per question.
The pseudonym->strand mapping is written to the output dir (which should be OUTSIDE
the repo until coding is complete) so coders cannot trivially unblind.

Usage: python3 prepare_packets.py --out /path/outside/repo
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRANDS = [
    "lutheran",
    "reformed-presbyterian",
    "anglican",
    "baptist",
    "methodist-wesleyan",
    "pentecostal",
    "anabaptist",
]
SEED = 20260822
QUESTIONS = [f"Q{i:02d}" for i in range(1, 51)]


def parse_worksheet(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\s*---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return None, f"no frontmatter: {path}"
    front, body = m.groups()
    silence = bool(re.search(r"^silence:\s*true\s*$", front, re.M))
    cm = re.search(r"##\s*Counsel\s*\n(.*?)(?=\n##\s|\Z)", body, re.S)
    counsel = cm.group(1).strip() if cm else ""
    if not silence and not counsel:
        return None, f"empty counsel: {path}"
    return {"silence": silence, "counsel": counsel}, None


def question_texts():
    qfile = (HERE / "questions.md").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"\*\*(Q\d{2})\*\*\s*—\s*(.*?)(?=\n- \*\*Q|\n###|\Z)", qfile, re.S):
        out[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "packets").mkdir(parents=True, exist_ok=True)

    qtexts = question_texts()
    missing_q = [q for q in QUESTIONS if q not in qtexts]
    if missing_q:
        sys.exit(f"questions.md parse missed: {missing_q}")

    rng = random.Random(SEED)
    mapping, problems = {}, []
    for q in QUESTIONS:
        order = STRANDS[:]
        rng.shuffle(order)
        mapping[q] = {f"R{i+1}": s for i, s in enumerate(order)}
        lines = [f"# {q}", "", f"> {qtexts[q]}", ""]
        for i, strand in enumerate(order):
            ws, err = parse_worksheet(HERE / "worksheets" / strand / f"{q}.md")
            tag = f"R{i+1}"
            if err:
                problems.append(err)
                lines += [f"## {tag}", "", "MISSING", ""]
            elif ws["silence"]:
                lines += [f"## {tag}", "", "SILENT", ""]
            else:
                lines += [f"## {tag}", "", ws["counsel"], ""]
        (out / "packets" / f"{q}.md").write_text("\n".join(lines), encoding="utf-8")

    (out / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"packets: {len(QUESTIONS)} -> {out/'packets'}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(" -", p)
        sys.exit(1)


if __name__ == "__main__":
    main()
