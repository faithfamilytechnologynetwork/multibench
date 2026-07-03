"""Self-contained cross-tradition HTML report (spec §4.5, Phase 4).

Regenerates the hand-built ``crosstrad-report.html`` figures **from data**, reframed
to the tradition axis, and adds the bootstrap CIs the pilot lacked. The document is
fully self-contained: inline CSS (light/dark via ``@media``), **static inline SVG**
charts computed in Python (no JavaScript, no external assets), and a ``<details>``
"Table view" twin per figure for accessibility.

Security (spec §3.3 / M9): **all** artifact-derived text — tradition / subject /
judge / scenario ids — is routed through ``esc`` before it enters any HTML or SVG
text/attribute context. There is no ``<script>`` context anywhere, so untrusted text
can never reach one. Numbers are formatted by our own code, never interpolated from
raw artifact strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

from analysis.aggregate import TECHNIQUE_IDS, TraditionAggregate
from analysis.colors import MINOR_REFS, heatmap_color, on_color, score_color
from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.stats import TraditionStats

_SCALE_NOTE = "Score −1…+1 (0 = neutral); five values −1, −0.5, 0, +0.5, +1."


def esc(value: object) -> str:
    """HTML/SVG-escape any (untrusted) value. The single escaping chokepoint (M9)."""
    return escape(str(value), quote=True)


def _fnum(x: float | None, digits: int = 2) -> str:
    return "—" if x is None else f"{x:+.{digits}f}"


def _fpct(x: float | None) -> str:
    return "—" if x is None else f"{x:.0%}"


def _fci(ci: list | None) -> str:
    if ci is None:
        return "—"
    return f"{ci[0]:+.2f} [{ci[1]:+.2f}, {ci[2]:+.2f}]"


@dataclass(frozen=True)
class Totals:
    traditions: int
    subjects: list[str]
    judges: list[str]
    sittings: int
    judgments: int
    expected_cells: int
    uncovered: int
    total_usd: float
    fully_priced: bool

    @property
    def coverage(self) -> float | None:
        if self.expected_cells <= 0:
            return None
        return (self.expected_cells - self.uncovered) / self.expected_cells


def compute_totals(aggregates: list[TraditionAggregate]) -> Totals:
    subjects: list[str] = []
    judges: list[str] = []
    sittings = judgments = expected = uncovered = 0
    total_usd = 0.0
    fully_priced = True
    for agg in aggregates:
        rep = agg.report
        c = rep["counts"]
        sittings += c.get("sittings", 0)
        judgments += c.get("judgments", 0)
        expected += c.get("expected_cells", 0)
        uncovered += c.get("uncovered", 0)
        cost = rep.get("cost", {})
        total_usd += cost.get("total_usd", 0.0) or 0.0
        fully_priced = fully_priced and bool(cost.get("fully_priced", True))
        for s in agg.subjects:
            if s not in subjects:
                subjects.append(s)
        for j in agg.judges:
            if j not in judges:
                judges.append(j)
    return Totals(
        traditions=len(aggregates),
        subjects=subjects,
        judges=judges,
        sittings=sittings,
        judgments=judgments,
        expected_cells=expected,
        uncovered=uncovered,
        total_usd=total_usd,
        fully_priced=fully_priced,
    )


# --- numeric −1…+1 axis geometry ---------------------------------------------

_PLOT_W = 560.0
_LABEL_W = 170.0
_RIGHT = 28.0


def _x(score: float) -> float:
    return _LABEL_W + (score + 1.0) / 2.0 * _PLOT_W


def _axis_svg(top: float, bottom: float) -> str:
    """Vertical reference lines (dashed ±0.5, solid 0) + numeric ticks."""
    parts: list[str] = []
    for ref in MINOR_REFS:
        parts.append(
            f'<line x1="{_x(ref):.1f}" y1="{top:.1f}" x2="{_x(ref):.1f}" y2="{bottom:.1f}" '
            f'class="ref-minor"/>'
        )
    parts.append(
        f'<line x1="{_x(0):.1f}" y1="{top:.1f}" x2="{_x(0):.1f}" y2="{bottom:.1f}" class="ref-zero"/>'
    )
    for t in (-1.0, -0.5, 0.0, 0.5, 1.0):
        parts.append(
            f'<text x="{_x(t):.1f}" y="{bottom + 15:.1f}" class="tick">{t:+.1f}</text>'
        )
    return "".join(parts)


# --- figures ------------------------------------------------------------------

def _marker(subject: str, subjects: list[str]) -> str:
    return "circle" if subjects.index(subject) == 0 else "diamond"


def _mark_svg(cx: float, cy: float, shape: str, fill: str, tip: str) -> str:
    t = f"<title>{esc(tip)}</title>"
    if shape == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6.5" fill="{fill}" class="mark">{t}</circle>'
    r = 6.5
    pts = f"{cx:.1f},{cy - r:.1f} {cx + r:.1f},{cy:.1f} {cx:.1f},{cy + r:.1f} {cx - r:.1f},{cy:.1f}"
    return f'<polygon points="{pts}" fill="{fill}" class="mark">{t}</polygon>'


def _scorecard_svg(pairs: list[tuple[TraditionAggregate, TraditionStats]], subjects: list[str]) -> str:
    row_h = 46.0
    top = 20.0
    height = top + row_h * len(pairs) + 44.0
    width = _LABEL_W + _PLOT_W + _RIGHT
    bottom = top + row_h * len(pairs)
    body: list[str] = [_axis_svg(top, bottom)]
    for i, (agg, st) in enumerate(pairs):
        cy0 = top + row_h * i + row_h / 2.0
        body.append(
            f'<text x="{_LABEL_W - 12:.1f}" y="{cy0 + 4:.1f}" class="rowlabel">{esc(agg.tradition)}</text>'
        )
        for k, s in enumerate(agg.subjects):
            ci = st.per_subject[s].headline
            if ci is None:
                continue
            cy = cy0 + (k - (len(agg.subjects) - 1) / 2.0) * 16.0
            p, lo, hi = ci
            body.append(
                f'<line x1="{_x(lo):.1f}" y1="{cy:.1f}" x2="{_x(hi):.1f}" y2="{cy:.1f}" class="whisker"/>'
            )
            tip = f"{agg.tradition} · {s}: {p:+.2f} (95% CI {lo:+.2f}…{hi:+.2f})"
            body.append(_mark_svg(_x(p), cy, _marker(s, subjects), score_color(p), tip))
    return (
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" class="chart" '
        f'role="img" aria-label="Cross-tradition headline scorecard with 95% CIs">'
        f'{"".join(body)}</svg>'
    )


def _staircase_svg(agg: TraditionAggregate, subjects: list[str]) -> str:
    w, h = 250.0, 150.0
    ml, mr, mt, mb = 24.0, 12.0, 22.0, 26.0
    pw, ph = w - ml - mr, h - mt - mb
    xs = {fr: ml + i / (len(FRAMINGS) - 1) * pw for i, fr in enumerate(FRAMINGS)}

    def y(score: float) -> float:
        return mt + (1.0 - (score + 1.0) / 2.0) * ph

    body: list[str] = [f'<text x="{w / 2:.0f}" y="14" class="sm-title">{esc(agg.tradition)}</text>']
    body.append(f'<line x1="{ml:.0f}" y1="{y(0):.1f}" x2="{w - mr:.0f}" y2="{y(0):.1f}" class="ref-zero"/>')
    for fr in FRAMINGS:
        body.append(f'<text x="{xs[fr]:.1f}" y="{h - 8:.0f}" class="sm-tick">{esc(fr[:3])}</text>')
    for s in agg.subjects:
        bf = agg.scorecard[s]["by_framing"]
        pts = [(xs[fr], bf.get(fr)) for fr in FRAMINGS if bf.get(fr) is not None]
        if len(pts) >= 2:
            poly = " ".join(f"{x:.1f},{y(v):.1f}" for x, v in pts)
            cls = "sm-line-0" if agg.subjects.index(s) == 0 else "sm-line-1"
            body.append(f'<polyline points="{poly}" class="{cls}"/>')
        for x, v in pts:
            body.append(_mark_svg(x, y(v), _marker(s, subjects), score_color(v),
                                  f"{agg.tradition} · {s}: {v:+.2f}"))
    return f'<svg viewBox="0 0 {w:.0f} {h:.0f}" class="sm" role="img" aria-label="Framing staircase {esc(agg.tradition)}">{"".join(body)}</svg>'


def _steadfastness_ci(st: TraditionStats, subject: str, col: str) -> list | None:
    ss = st.per_subject[subject]
    return ss.steadfastness if col == "pooled" else ss.steadfastness_by_pressure.get(col)


def _heatmap_svg(pairs: list[tuple[TraditionAggregate, TraditionStats]]) -> str:
    cols = list(PRESSURES) + ["pooled"]
    # (tradition, subject, point-by-col dict, stats) — points drive the color, CIs the tooltip.
    rows: list[tuple[str, str, dict, float | None, TraditionStats]] = []
    for agg, st in pairs:
        for s in agg.subjects:
            sc = agg.scorecard[s]
            rows.append((agg.tradition, s, sc["steadfastness_by_pressure"], sc["steadfastness"], st))
    values = [v for _, _, bp, pooled, _ in rows for v in list(bp.values()) + [pooled] if v is not None]
    vmax = max((abs(v) for v in values), default=1.0) or 1.0

    cell_w, cell_h = 74.0, 30.0
    label_w, head_h = 210.0, 40.0
    width = label_w + cell_w * len(cols)
    height = head_h + cell_h * len(rows) + 8.0
    body: list[str] = []
    for c, col in enumerate(cols):
        cx = label_w + cell_w * c + cell_w / 2.0
        body.append(f'<text x="{cx:.1f}" y="{head_h - 14:.1f}" class="hm-col">{esc(col[:9])}</text>')
    for r, (trad, subj, bp, pooled, st) in enumerate(rows):
        ry = head_h + cell_h * r
        body.append(f'<text x="{label_w - 8:.1f}" y="{ry + cell_h / 2 + 4:.1f}" class="hm-row">{esc(trad)} · {esc(subj)}</text>')
        for c, col in enumerate(cols):
            v = pooled if col == "pooled" else bp.get(col)
            cx = label_w + cell_w * c
            fill = "var(--empty)" if v is None else heatmap_color(v, vmax)
            ci = _steadfastness_ci(st, subj, col)
            tip = f"{trad} · {subj} · {col}: {_fci(ci)}"
            body.append(
                f'<rect x="{cx:.1f}" y="{ry:.1f}" width="{cell_w - 2:.1f}" height="{cell_h - 2:.1f}" '
                f'fill="{fill}"><title>{esc(tip)}</title></rect>'
            )
            if v is not None:
                txt = on_color(v, vmax)
                body.append(f'<text x="{cx + cell_w / 2:.1f}" y="{ry + cell_h / 2 + 4:.1f}" class="hm-val" fill="{txt}">{v:+.2f}</text>')
    return f'<svg viewBox="0 0 {width:.0f} {height:.0f}" class="chart" role="img" aria-label="Steadfastness heatmap">{"".join(body)}</svg>'


def _distribution_svg(pairs: list[tuple[TraditionAggregate, TraditionStats]]) -> str:
    order = ["-1.0", "-0.5", "0.0", "0.5", "1.0"]
    rows: list[tuple[str, str, dict]] = []
    for agg, _ in pairs:
        for s in agg.subjects:
            rows.append((agg.tradition, s, agg.score_distribution[s]))
    label_w, bar_w, row_h, top = 210.0, 460.0, 26.0, 24.0
    width = label_w + bar_w + 30.0
    height = top + row_h * len(rows) + 10.0
    body: list[str] = []
    for r, (trad, subj, dist) in enumerate(rows):
        ry = top + row_h * r
        total = sum(dist.get(k, 0) for k in order) or 1
        x = label_w
        body.append(f'<text x="{label_w - 8:.1f}" y="{ry + row_h / 2 + 4:.1f}" class="hm-row">{esc(trad)} · {esc(subj)}</text>')
        for k in order:
            n = dist.get(k, 0)
            seg = bar_w * n / total
            body.append(
                f'<rect x="{x:.1f}" y="{ry + 3:.1f}" width="{seg:.1f}" height="{row_h - 8:.1f}" '
                f'fill="{score_color(float(k))}"><title>{esc(k)}: {n}</title></rect>'
            )
            x += seg
    return f'<svg viewBox="0 0 {width:.0f} {height:.0f}" class="chart" role="img" aria-label="Score distributions">{"".join(body)}</svg>'


# --- table twins --------------------------------------------------------------

def _details(summary: str, table_html: str) -> str:
    return f'<details class="tablev"><summary>{esc(summary)}</summary>{table_html}</details>'


def _scorecard_table(pairs, subjects) -> str:
    # Header and body iterate the SAME global subject list (columns stay aligned even if a
    # tradition is missing a subject — "—" fills the gap).
    head = "".join(f"<th>{esc(s)}</th>" for s in subjects)
    body = []
    for agg, st in pairs:
        cells = "".join(
            f"<td>{_fci(st.per_subject[s].headline) if s in st.per_subject else '—'}</td>"
            for s in subjects
        )
        body.append(f"<tr><th>{esc(agg.tradition)}</th>{cells}</tr>")
    return f'<table><thead><tr><th>tradition</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def _staircase_table(pairs) -> str:
    body = []
    for agg, st in pairs:
        for s in agg.subjects:
            bf = agg.scorecard[s]["by_framing"]
            ss = st.per_subject[s]
            body.append(
                f"<tr><th>{esc(agg.tradition)}</th><td>{esc(s)}</td>"
                f"<td>{_fnum(bf.get('unstated'))}</td><td>{_fnum(bf.get('stated'))}</td>"
                f"<td>{_fnum(bf.get('guided'))}</td><td>{_fci(ss.recognition_gap)}</td>"
                f"<td>{_fci(ss.instruction_gap)}</td></tr>"
            )
    return (
        "<table><thead><tr><th>tradition</th><th>subject</th><th>unstated</th>"
        "<th>stated</th><th>guided</th><th>recognition (S−U)</th><th>instruction (G−S)</th>"
        f"</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def _heatmap_table(pairs) -> str:
    # Table twin carries the steadfastness bootstrap CIs (M4): point [lo, hi] per cell.
    cols = list(PRESSURES) + ["pooled"]
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = []
    for agg, st in pairs:
        for s in agg.subjects:
            cells = "".join(f"<td>{_fci(_steadfastness_ci(st, s, c))}</td>" for c in cols)
            body.append(f"<tr><th>{esc(agg.tradition)}</th><td>{esc(s)}</td>{cells}</tr>")
    return (
        '<table><thead><tr><th>tradition</th><th>subject</th>' + head
        + "</tr></thead><tbody>" + "".join(body)
        + "</tbody></table>"
    )


def _distribution_table(pairs) -> str:
    order = ["-1.0", "-0.5", "0.0", "0.5", "1.0"]
    head = "".join(f"<th>{k}</th>" for k in order)
    body = []
    for agg, _ in pairs:
        for s in agg.subjects:
            d = agg.score_distribution[s]
            cells = "".join(f"<td>{d.get(k, 0)}</td>" for k in order)
            body.append(f"<tr><th>{esc(agg.tradition)}</th><td>{esc(s)}</td>{cells}</tr>")
    return f'<table><thead><tr><th>tradition</th><th>subject</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def _technique_html(pairs, subjects) -> str:
    # Pooled per-subject rate across traditions (mean of per-tradition rates).
    agg_rates: dict[str, dict[str, list[float]]] = {s: {t: [] for t in TECHNIQUE_IDS} for s in subjects}
    for agg, _ in pairs:
        for s in agg.subjects:
            for t in TECHNIQUE_IDS:
                v = agg.techniques[s].get(t)
                if v is not None:
                    agg_rates[s][t].append(v)
    rows = []
    for t in TECHNIQUE_IDS:
        cells = []
        for s in subjects:
            vals = agg_rates[s][t]
            rate = sum(vals) / len(vals) if vals else None
            pct = 0 if rate is None else round(rate * 100)
            bar = (
                f'<div class="meter"><div class="meter-fill" style="width:{pct}%"></div></div>'
                f'<span class="meter-num">{_fpct(rate)}</span>'
            )
            cells.append(f"<td>{bar}</td>")
        rows.append(f"<tr><th>{esc(t)}</th>{''.join(cells)}</tr>")
    head = "".join(f"<th>{esc(s)}</th>" for s in subjects)
    return f'<table class="tech"><thead><tr><th>technique</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def _agreement_table(pairs) -> str:
    body = []
    for agg, _ in pairs:
        a = agg.report["agreement"]
        body.append(
            f"<tr><th>{esc(agg.tradition)}</th><td>{_fpct(a.get('exact_pct'))}</td>"
            f"<td>{_fpct(a.get('within_one_pct'))}</td>"
            f"<td>{esc(a.get('worst_scenario') or '—')} ({_fpct(a.get('worst_scenario_exact_pct'))})</td></tr>"
        )
    return (
        "<table><thead><tr><th>tradition</th><th>exact</th><th>within one step</th>"
        f"<th>lowest-agreement scenario</th></tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def _spotlight_table(pairs, subjects) -> str:
    head = "".join(f"<th>{esc(s)}</th>" for s in subjects)
    body = []
    for agg, _ in pairs:
        for sid in agg.scenario_ids:
            cells = "".join(f"<td>{_fnum(agg.by_scenario[sid].get(s))}</td>" for s in subjects)
            body.append(f"<tr><th>{esc(agg.tradition)}</th><td>{esc(sid)}</td>{cells}</tr>")
    return f'<table><thead><tr><th>tradition</th><th>scenario</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def _cost_table(pairs, totals: Totals) -> str:
    body = []
    for agg, _ in pairs:
        cost = agg.report.get("cost", {})
        usd = cost.get("total_usd")
        body.append(f"<tr><th>{esc(agg.tradition)}</th><td>${usd:.2f}</td></tr>" if usd is not None
                    else f"<tr><th>{esc(agg.tradition)}</th><td>—</td></tr>")
    note = "" if totals.fully_priced else " (partial — unpriced model present)"
    body.append(f'<tr class="total"><th>total</th><td>${totals.total_usd:.2f}{esc(note)}</td></tr>')
    return f'<table><thead><tr><th>tradition</th><th>cost</th></tr></thead><tbody>{"".join(body)}</tbody></table>'


# --- document assembly --------------------------------------------------------

def render_report(
    aggregates: list[TraditionAggregate],
    stats: list[TraditionStats],
    *,
    title: str = "MultiBench — cross-tradition analysis",
) -> str:
    """Assemble the full self-contained HTML document from aggregates + bootstrap CIs."""
    pairs = list(zip(aggregates, stats))
    totals = compute_totals(aggregates)
    subjects = totals.subjects

    cov = "—" if totals.coverage is None else f"{totals.coverage:.0%}"
    stat_tiles = "".join(
        f'<div class="tile"><div class="tile-n">{n}</div><div class="tile-l">{esc(label)}</div></div>'
        for n, label in [
            (totals.traditions, "traditions"),
            (f"{totals.sittings:,}", "sittings"),
            (f"{totals.judgments:,}", "judgments"),
            (cov, "coverage"),
            (f"${totals.total_usd:,.0f}", "run cost"),
        ]
    )

    def section(num, name, lead, figure, table):
        return (
            f'<section><h2><span class="num">{num}</span> {esc(name)}</h2>'
            f'<p class="lead">{esc(lead)}</p><figure>{figure}{table}</figure></section>'
        )

    parts: list[str] = [
        f'<main class="sheet">',
        f'<header><div class="eyebrow">MultiBench</div><h1>{esc(title)}</h1>',
        f'<p class="dek">Cross-tradition analysis of a judging run — subjects '
        f'{esc(", ".join(subjects))}; judges {esc(", ".join(totals.judges))}. {esc(_SCALE_NOTE)}</p>',
        f'<div class="stats">{stat_tiles}</div></header>',
        section("1", "The tradition gradient (headline, with 95% CIs)",
                "Headline = mean score at unstated framing, after pressure. Whiskers are "
                "scenario-cluster bootstrap 95% CIs; a wide interval means the five scenarios disagree.",
                _scorecard_svg(pairs, subjects),
                _details("Table view — headline [95% CI]", _scorecard_table(pairs, subjects))),
        section("2", "Recognition vs instruction (framing staircase)",
                "Each panel walks unstated → stated → guided for both subjects. Recognition (S−U) "
                "and instruction (G−S) gaps carry bootstrap CIs in the table.",
                '<div class="smallmults">' + "".join(_staircase_svg(a, subjects) for a, _ in pairs) + "</div>",
                _details("Table view — framing + gap CIs", _staircase_table(pairs))),
        section("3", "Steadfastness by pressure",
                "Change from first response to after-pressure (unstated). Red = degraded, green = "
                "held or improved; the pooled column is the overall steadfastness. Bootstrap 95% "
                "CIs are in the table view (and on cell hover).",
                _heatmap_svg(pairs),
                _details("Table view — steadfastness point [95% CI]", _heatmap_table(pairs))),
        section("4", "Score distributions",
                "How each subject's per-judge verdicts spread across the five values.",
                _distribution_svg(pairs),
                _details("Table view — verdict counts", _distribution_table(pairs))),
        section("5", "Scenario spotlights",
                "Per-scenario headline (unstated, after pressure) — where a tradition's gradient comes from.",
                "", _spotlight_table(pairs, subjects)),
        section("6", "Technique profile",
                "Share of a subject's judgments citing each counseling technique, pooled across traditions.",
                _technique_html(pairs, subjects), ""),
        section("7", "Judge agreement",
                "Inter-judge exact / within-one-step agreement and the lowest-agreement scenario per tradition.",
                "", _agreement_table(pairs)),
        section("8", "Cost", "Total spend across the run.", "", _cost_table(pairs, totals)),
        '<section><h2><span class="num">9</span> Read this as a pilot</h2><ul class="caveats">'
        '<li><b>Five scenarios per tradition.</b> Every CI here is a bootstrap over just five '
        'scenario clusters, so intervals are wide and routinely cross zero — treat each value as '
        'directional, not settled.</li>'
        '<li><b>Judge asymmetry.</b> A judge never scores its own subject, so one subject may be '
        'scored by a single judge and another by two.</li>'
        '<li><b>Scenario mix.</b> Each tradition\'s five scenarios differ, so part of a cross-tradition '
        'gap can be scenario mix rather than the subject.</li></ul></section>',
        f'<footer>{esc(_SCALE_NOTE)} · Generated from judging run artifacts; numbers reproduce each '
        f'tradition\'s report.json.</footer>',
        "</main>",
    ]
    body = "".join(parts)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f"<title>{esc(title)}</title>\n{_CSS}\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


_CSS = """<style>
:root{--bg:#fbfaf7;--sheet:#ffffff;--ink:#1a1a1a;--muted:#666;--rule:#e6e2d8;--accent:#1a6840;
--empty:#eceae4;--tile:#f4f1ea;}
@media (prefers-color-scheme:dark){:root{--bg:#14150f;--sheet:#1c1d17;--ink:#eceae2;--muted:#9a978c;
--rule:#33342b;--accent:#7bbf9a;--empty:#2a2b23;--tile:#23241c;}}
:root[data-theme=light]{--bg:#fbfaf7;--sheet:#ffffff;--ink:#1a1a1a;--muted:#666;--rule:#e6e2d8;
--accent:#1a6840;--empty:#eceae4;--tile:#f4f1ea;}
:root[data-theme=dark]{--bg:#14150f;--sheet:#1c1d17;--ink:#eceae2;--muted:#9a978c;--rule:#33342b;
--accent:#7bbf9a;--empty:#2a2b23;--tile:#23241c;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:Georgia,'Times New Roman',serif;line-height:1.5}
.sheet{max-width:880px;margin:0 auto;padding:32px 24px 64px;background:var(--sheet)}
.eyebrow{letter-spacing:.18em;text-transform:uppercase;font-size:12px;color:var(--accent);font-family:system-ui,sans-serif}
h1{font-size:34px;margin:.15em 0 .25em}.dek{color:var(--muted);margin:.2em 0 1em}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 8px}
.tile{flex:1 1 110px;background:var(--tile);border-radius:8px;padding:12px 14px;text-align:center}
.tile-n{font-size:22px;font-weight:bold}.tile-l{font-size:12px;color:var(--muted);font-family:system-ui,sans-serif}
h2{font-size:21px;border-bottom:2px solid var(--rule);padding-bottom:.2em;margin:2em 0 .3em;color:var(--accent)}
h2 .num{display:inline-block;min-width:1.4em;color:var(--muted)}
.lead{color:var(--muted);margin:.2em 0 1em;font-size:15px}
figure{margin:0}svg.chart{max-width:100%;height:auto}
.smallmults{display:flex;flex-wrap:wrap;gap:8px}svg.sm{width:250px;max-width:100%;height:auto}
.rowlabel,.hm-row{text-anchor:end;font-size:12px;fill:var(--ink);font-family:system-ui,sans-serif}
.tick,.hm-col,.sm-tick{text-anchor:middle;font-size:11px;fill:var(--muted);font-family:system-ui,sans-serif}
.sm-title{text-anchor:middle;font-size:12px;fill:var(--ink);font-family:system-ui,sans-serif}
.hm-val{text-anchor:middle;font-size:11px;font-family:system-ui,sans-serif}
.whisker{stroke:var(--muted);stroke-width:2}
.ref-minor{stroke:var(--rule);stroke-width:1;stroke-dasharray:3 3}
.ref-zero{stroke:var(--muted);stroke-width:1.2}
.mark{stroke:var(--sheet);stroke-width:1.2}
.sm-line-0{fill:none;stroke:var(--accent);stroke-width:2}
.sm-line-1{fill:none;stroke:#2C7FB8;stroke-width:2}
table{border-collapse:collapse;width:100%;font-size:13px;font-family:system-ui,sans-serif;margin-top:6px}
th,td{border:1px solid var(--rule);padding:5px 8px;text-align:center}
thead th,tbody th{background:var(--tile)}tbody th{text-align:left}
tr.total th,tr.total td{font-weight:bold}
.tablev{margin-top:8px}.tablev summary{cursor:pointer;color:var(--accent);font-family:system-ui,sans-serif;font-size:13px}
.tablev>table{overflow-x:auto;display:block}
.meter{display:inline-block;width:120px;height:9px;background:var(--empty);border-radius:5px;vertical-align:middle;overflow:hidden}
.meter-fill{height:100%;background:var(--accent)}.meter-num{margin-left:6px;font-size:12px}
.caveats{color:var(--ink);font-size:15px}.caveats li{margin:.35em 0}
footer{margin-top:2.5em;padding-top:1em;border-top:1px solid var(--rule);color:var(--muted);font-size:12px}
</style>"""
