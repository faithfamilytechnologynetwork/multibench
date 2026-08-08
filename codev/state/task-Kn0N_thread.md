# task-Kn0N — raw item page reading-order fix

## Task
Fix reading order on `/results/$runId/$groupId/$itemId` (multibrowser raw item page).
Required order: **question → judge-guidance Context → model responses**. Previously
CorpusContext (the "Context — what good counsel looks like" collapsible) rendered
*above* the whole comparison, so readers saw the guidance before the question it
refers to (Waleed's live complaint).

## Approach (soft mode, AIR-shaped — code-only, no data changes)
Gave `RawComparison` a GENERIC optional slot prop `contextSlot?: ReactNode`, rendered
**full-width after the first user turn (the question) and before the first assistant
response**. `RawResultsPage` now passes `<CorpusContext .../>` into that slot instead
of rendering it above the comparison.

Key design points:
- Slot is an opaque `ReactNode` — `RawComparison`/`rawModel` learn NO MB vocabulary.
  `CorpusContext` stays the ONE sanctioned corpus-coupled child (the #54 static guard
  in `rawData.test.ts` stays green untouched — RawComparison added no forbidden literal).
- Rendered via a `<Fragment>` (not a wrapping `<div>`) so a slot that renders nothing
  (non-corpus / AFB catalog → CorpusContext returns null) injects **no DOM → no gap**.
- `defaultOpen` on the collapsible preserved; the pressure push (second user turn)
  stays where it was.
- Note: guidance is now coupled to the conversation rendering — when the shard is
  unavailable (no conversation), the guidance no longer shows. Acceptable per the task
  design (there's no question to anchor context after). The "unavailable" test is green.

## Tests
- `RawComparison.test.tsx`: +2 unit tests — (1) slot renders after question, before
  first response; (2) a null-rendering slot injects no element (degrade → no gap).
- `rawResults.test.tsx`: +1 integration test asserting DOM order question → guidance →
  first response on the real page.
- `pnpm -C apps/multibrowser test` → 295 passed. `check-types` clean.

## Status
Implementation complete. Opening PR (do NOT merge — architect reviews).
