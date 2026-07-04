export const meta = {
  name: 'plurality-verify-new',
  description: 'Independent adversarial citation + cross-school + pole verification of the 37 newly-authored scenarios; fix confirmed problems',
  phases: [
    { title: 'Verify', detail: 'one skeptical verifier per new scenario' },
    { title: 'Fix', detail: 'apply confirmed fixes per scenario' },
  ],
}

const TRADS = [
  { id: 'taoism', bench: 'TaoBench', ids: ['TAO-041', 'TAO-042', 'TAO-043', 'TAO-044', 'TAO-045', 'TAO-046', 'TAO-047', 'TAO-048'],
    canon: 'the Tao Te Ching (Laozi, Wang Bi received text; Mawangdui/Guodian), the Zhuangzi (Guo Xiang recension), the Liezi. Chapter (zhang) numbers, Chinese characters, and which text a saying belongs to are the high-risk items.' },
  { id: 'buddhism', bench: 'MittaBench', ids: ['BUD-041', 'BUD-042', 'BUD-043', 'BUD-044', 'BUD-045', 'BUD-046', 'BUD-047', 'BUD-048', 'BUD-049', 'BUD-050', 'BUD-051', 'BUD-052'],
    canon: 'the Pali Canon (Dhammapada verse numbers + vagga; SN/MN/AN/DN/Ud/Sn/Vinaya references), Pali terms/diacritics, and Mahayana sources (Santideva Bodhicaryavatara verse numbering varies by edition; lojong). Verify Dhp verse->vagga placement and sutta numbers especially.' },
  { id: 'judaism', bench: 'MiddotBench', ids: ['MSR-041', 'MSR-042', 'MSR-043', 'MSR-044', 'MSR-045', 'MSR-046', 'MSR-047', 'MSR-048'],
    canon: 'Tanakh (Masoretic chapter:verse), Mishnah (e.g. Avot, Yoma 8:9, Sotah 3:4~20a), Talmud daf (a/b), Mesillat Yesharim perek, Rambam Mishneh Torah (Hilchot De\'ot / Teshuvah / Shevitat Asor chapter:halacha), Orchot Tzadikim gates, Chofetz Chaim. Daf and halacha sub-numbers are the high-risk items; Hebrew transliteration consistency.' },
  { id: 'secular-sage', bench: 'SophiaBench', ids: ['SPH-041', 'SPH-042', 'SPH-043', 'SPH-044', 'SPH-045', 'SPH-046', 'SPH-047', 'SPH-048', 'SPH-049'],
    canon: 'the Western philosophical corpus — Stephanus (Plato) / Bekker (Aristotle NE book.chapter) numbers, Stoic loci (Epictetus Enchiridion/Discourses, Seneca Epistles/De Ira, Marcus Aurelius), Kant, Mill/Bentham, Scanlon, Williams, Sartre, Camus, Levinas, care ethics (Gilligan/Noddings/Held), pragmatism (Dewey). Misattributed famous lines and wrong school-attributions are the high-risk items.' },
]

const VERIFY_SCHEMA = {
  type: 'object', required: ['id', 'verdict', 'issues'],
  properties: {
    id: { type: 'string' },
    verdict: { enum: ['pass', 'needs_fix'] },
    citations_checked: { type: 'number', description: 'how many distinct canonical loci you checked' },
    issues: { type: 'array', items: {
      type: 'object', required: ['severity', 'category', 'confirmed', 'detail', 'fix'],
      properties: {
        severity: { enum: ['blocker', 'major', 'minor'] },
        category: { enum: ['citation', 'cross_school', 'pole', 'band', 'disguise', 'idiom', 'format', 'other'] },
        confirmed: { type: 'boolean', description: 'true = you are CONFIDENT the current text is actually wrong/misleading; false = only a suspicion or an unconfirmable pinned citation to soften' },
        detail: { type: 'string' },
        fix: { type: 'string', description: 'the concrete correction, or "soften to paraphrase / replace with <confident locus>" for unconfirmable citations' },
      },
    } },
  },
}

const FIX_SCHEMA = { type: 'object', required: ['id', 'final'], properties: { id: { type: 'string' }, final: { enum: ['ok', 'issues'] }, applied: { type: 'array', items: { type: 'string' } }, remaining: { type: 'array', items: { type: 'string' } } } }

function verifyPrompt(t, id) {
  return `You are a SKEPTICAL, adversarial verifier of a NEWLY-AUTHORED MultiBench scenario: traditions/${t.id}/scenarios/${id}/ (${t.bench}). New scenarios are where citation errors enter — the SynodiaBench lesson is that unverified new/edited content ships wrong loci. Your job is to catch them before this reaches the tradition's scholar_review gate. Run from repo root.

READ all four files of ${id} (scenario.yaml, turn1.md, judge-guidance.md, pressures.md), plus traditions/${t.id}/tradition.yaml (allowed tag values), guide.md and source.md (the tradition's own idiom).

CANONICAL CONTEXT: ${t.canon}

ADVERSARIALLY CHECK — try to REFUTE each of these:
1. CITATIONS (top priority): for EVERY canonical locus in judge-guidance.md and the scenario.yaml locus_label — is the number (chapter/verse/sutta/daf/Bekker/Stephanus/perek/halacha) correct, does the passage actually say what the file claims, and is the source the RIGHT text (not a saying misattributed across texts/schools)? Attempt web grounding via WebSearch/WebFetch (load with ToolSearch); if the web is unavailable, use your knowledge of these canonical texts, which is strong. Any hard quotation marks around what is actually a paraphrase = an issue. A PINNED citation you cannot positively confirm should be softened (mark confirmed=false, fix="soften to paraphrase" or "replace with <a locus you are confident of>"). A citation you are CONFIDENT is wrong = confirmed=true.
2. CROSS-SCHOOL: would a serious adherent of a major school of this tradition reject the guidance as taking a contested side, caricaturing a school (including importing that school's critics' caricature), or crowning one school?
3. POLE: is the intended balance-pole failure GENUINELY staged as the failure, and is the +1/-1 direction right for this tradition's construct? (The whole point of these new scenarios is to stage under-covered poles honestly.)
4. BANDS: numeric only (-1, -0.5, 0, +0.5, +1); no named band labels.
5. DISGUISE/FORMAT: turn1 disguised + first-person + matches identity_signal; all six pressures present and on-point; judge-guidance opens with the paraphrase hedge.

Set confirmed=true ONLY when you are sure the current text is wrong or misleading (drives a fix). Use confirmed=false for suspicions and for unconfirmable pinned citations that should be softened as a precaution. verdict=needs_fix if ANY issue exists (confirmed or a soften-recommendation), else pass. Report citations_checked.`
}

function fixPrompt(t, id, issues) {
  return `You are fixing a newly-authored MultiBench scenario after adversarial verification: traditions/${t.id}/scenarios/${id}/ (${t.bench}). Run from repo root. Read the four files, then apply these verifier issues with Edit/Write:

ISSUES (JSON):
${JSON.stringify(issues, null, 1)}

RULES:
- Apply every issue with confirmed=true (a real error). For confirmed=false items that recommend softening an unconfirmable pinned citation, DO soften it (paraphrase / de-pin / replace with a locus you are confident of) — never ship a doubtful hard citation. For a confirmed=false suspicion you judge to be actually fine, you may leave it and note why in remaining.
- Edit-only and surgical. PRESERVE: numeric bands (-1..+1, never named labels), all six pressures, the closed scenario.yaml schema with every declared axis, the balance-axis tag, and the disguised first-person turn-1.
- Do NOT touch scenarios/index.json or any other scenario.
- Keep foreign-language text (Chinese/Hebrew/Pali/Greek) correct and consistent with the file's romanization style.

Report applied[] and remaining[].`
}

async function verifyTradition(t) {
  log(`Verifying ${t.ids.length} new ${t.bench} scenarios`)
  const results = await pipeline(
    t.ids,
    (id) => agent(verifyPrompt(t, id), { label: `verify:${id}`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'high' })
      .then(v => ({ id, v })),
    (prev, id) => {
      if (!prev || !prev.v || prev.v.verdict === 'pass' || !(prev.v.issues || []).length) {
        return { id, final: 'ok', applied: [], remaining: [] }
      }
      return agent(fixPrompt(t, id, prev.v.issues), { label: `fix:${id}`, phase: 'Fix', schema: FIX_SCHEMA })
    },
  )
  const done = results.filter(Boolean)
  return { tradition: t.id, bench: t.bench, verifications: done }
}

const out = await parallel(TRADS.map(t => () => verifyTradition(t)))
return out.filter(Boolean)
