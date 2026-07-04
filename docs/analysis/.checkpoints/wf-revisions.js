export const meta = {
  name: 'plurality-revisions',
  description: 'Apply confirmed+verified ultracode findings as surgical edit-only fixes across taoism, buddhism, judaism, secular-sage',
  phases: [
    { title: 'Plan', detail: 'per-tradition: decompose verified findings into per-file edit sets' },
    { title: 'Edit', detail: 'one editor agent per file; edit-only, numeric bands preserved' },
  ],
}

const CKPT = 'docs/analysis/.checkpoints/plurality-audit-findings.json'
// Distribution-honesty findings are handled by hand in reconciliation (need post-authoring numbers)
const EXCLUDE = ['TAO-F11', 'BUD-F08', 'MSR-F14', 'SPH-F23']

const TRADS = [
  { id: 'taoism', bench: 'TaoBench' },
  { id: 'buddhism', bench: 'MittaBench' },
  { id: 'judaism', bench: 'MiddotBench' },
  { id: 'secular-sage', bench: 'SophiaBench' },
]

const PLAN_SCHEMA = {
  type: 'object', required: ['files'],
  properties: {
    files: { type: 'array', items: {
      type: 'object', required: ['path', 'edits'],
      properties: {
        path: { type: 'string', description: 'exact repo-relative file path (resolve dir-targets and sweeps to concrete files)' },
        edits: { type: 'array', items: {
          type: 'object', required: ['finding_id', 'severity', 'fix_type', 'instruction'],
          properties: {
            finding_id: { type: 'string' },
            severity: { type: 'string' },
            fix_type: { type: 'string' },
            instruction: { type: 'string', description: 'the precise edit to make in THIS file — the corrected_fix if present else proposed_fix, narrowed to just this file\'s portion for multi-file findings; keep wording consistent with the same finding\'s other files' },
            anchor: { type: 'string', description: 'short verbatim quote of the current text to locate the edit, if known' },
          },
        } },
      },
    } },
  },
}

const EDIT_SCHEMA = {
  type: 'object', required: ['path', 'applied', 'skipped'],
  properties: {
    path: { type: 'string' },
    applied: { type: 'array', items: { type: 'object', required: ['finding_id', 'what'], properties: { finding_id: { type: 'string' }, what: { type: 'string', description: 'one line: what was changed' } } } },
    skipped: { type: 'array', items: { type: 'object', required: ['finding_id', 'why'], properties: { finding_id: { type: 'string' }, why: { type: 'string' } } } },
    notes: { type: 'string' },
  },
}

function plannerPrompt(t) {
  return `You are the edit planner for the ultracode revision of MultiBench tradition traditions/${t.id}/ (${t.bench}). Run from repo root (cwd).

STEP 1 — READ ${CKPT} (a JSON list of 4 tradition objects). Find the object with "tradition":"${t.id}". Take ONLY its findings whose "verdict" is exactly "confirmed". IGNORE any finding whose verdict is "refuted" or "uncertain" (those were killed in adversarial verification — acting on them causes regressions). Also EXCLUDE these finding ids entirely (handled separately by hand): ${JSON.stringify(EXCLUDE)}.

STEP 2 — For each remaining confirmed finding, decide the CONCRETE file(s) it edits and the precise per-file instruction:
- Each finding has: id, severity, fix_type, target_file, scenario_id, claim, current_text, proposed_fix, corrected_fix, verify_rationale.
- The AUTHORITATIVE instruction is corrected_fix when it is non-empty; otherwise proposed_fix. When corrected_fix narrows, overrides, or partially rejects the proposed_fix, FOLLOW corrected_fix (it is the adversarial verifier's ruling).
- If target_file is already a concrete file, use it.
- If target_file is a directory (e.g. traditions/${t.id}) it is a BANK-WIDE SWEEP: read the corrected_fix/proposed_fix, which enumerate the specific files, and split it into one edit per concrete file. Drop any file the corrected_fix says to drop.
- If a finding is a multi-file contract (safety/neutrality across tradition.yaml + README.md + guide.md + source.md), split it into one edit per file, each carrying only that file's portion of the wording, kept consistent across files.

STEP 3 — GROUP all resulting edits by concrete file path (so every file that needs editing appears once, with ALL its edits — including edits contributed by different findings or by a sweep). This grouping is critical: two findings may touch the same file and must be handled by one editor.

Output the files[] structure. Put the exact per-file instruction text (verbatim-quality, ready for an editor to apply) in each edit's "instruction", and a short verbatim "anchor" quote from the current file text where possible. Do NOT edit any file yourself — you are only planning. Resolve every path precisely (verify the file exists by reading the directory if unsure).`
}

function editorPrompt(t, path, edits) {
  return `You are a surgical, edit-only reviser for the ultracode revision of MultiBench tradition traditions/${t.id}/ (${t.bench}). Run from repo root.

EDIT EXACTLY ONE FILE: ${path}

Apply ONLY these confirmed, adversarially-verified edits to that file. READ the file first, then make each edit with the Edit tool.

EDITS (JSON):
${JSON.stringify(edits, null, 1)}

HARD RULES (from the SynodiaBench precedent — violating these is worse than skipping):
- EDIT-ONLY and SURGICAL: change the minimum span needed. Preserve the file's structure, voice, and all content not named in an edit.
- NEVER change numeric scoring bands; the scale is -1, -0.5, 0, +0.5, +1 everywhere. Never introduce named band labels (regression-tested).
- NEVER alter a scenario's BALANCE-axis tag (taoism pivot / buddhism middle_way / judaism middle_path / secular-sage mean). Re-tags are permitted ONLY for register / vices / identity_signal / domain axes and ONLY when the edit's fix_type is "re_tag" and explicitly says so. If a re_tag says replace 'standard' with an overlay, REPLACE it (the bank's convention is that 'standard' never coexists with a flagged overlay).
- Follow the instruction text exactly; it already reflects the adversarial verifier's corrected ruling.
- If you cannot confidently locate the target text (anchor doesn't match, or the file already reads as the instruction wants), DO NOT force it — record it in skipped[] with the reason. A skipped edit I can fix by hand; a corrupted file I cannot.
- Do NOT touch scenarios/index.json, do NOT create or delete files, do NOT reformat unrelated lines.
- Keep any Chinese/Hebrew/Pali/Greek text correct; match the file's existing romanization/diacritic style.

Report every edit as applied[] or skipped[].`
}

async function planTradition(t) {
  log(`Planning edits for ${t.bench} (${t.id})`)
  const plan = await agent(plannerPrompt(t), { label: `plan:${t.id}`, phase: 'Plan', schema: PLAN_SCHEMA, effort: 'high' })
  if (!plan) { log(`${t.id}: planner failed`); return null }
  log(`${t.id}: ${plan.files.length} files to edit (${plan.files.reduce((n, f) => n + f.edits.length, 0)} edits)`)
  return { t, plan }
}

async function editTradition(planned) {
  if (!planned) return null
  const { t, plan } = planned
  const results = await parallel(plan.files.map(f => () =>
    agent(editorPrompt(t, f.path, f.edits), { label: `edit:${t.id}:${f.path.split('/').slice(-2).join('/')}`, phase: 'Edit', schema: EDIT_SCHEMA })
  ))
  const ok = results.filter(Boolean)
  const applied = ok.reduce((n, r) => n + (r.applied || []).length, 0)
  const skipped = ok.reduce((n, r) => n + (r.skipped || []).length, 0)
  log(`${t.id}: applied ${applied}, skipped ${skipped} across ${ok.length}/${plan.files.length} files`)
  return { tradition: t.id, bench: t.bench, fileResults: ok, plannedFiles: plan.files.length }
}

const results = await pipeline(TRADS, planTradition, editTradition)
return results.filter(Boolean)
