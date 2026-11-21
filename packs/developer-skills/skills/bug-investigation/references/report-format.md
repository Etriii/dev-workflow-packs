# Report rules

Present findings directly in plain Markdown. Use hyphens for lists and separators. No stock introduction, conclusion, promotional wording, AI references, audience labels, machine-specific absolute paths, or internal task IDs beyond useful BUG IDs. Use actual route, page, and button names where known. Do not hide uncertainty. Keep one primary category for a shared issue and reference it from other roles or pages. Use separate project sections for unrelated repositories, and repository names above source tables when several contribute. Never add a Project column.

## Brief

One short category label per role or page, followed by issue bullets stating problem, supported cause or uncertainty, proposed or implemented correction, and material limits. Omit file tables, line numbers, hashes, routine metadata, and bug IDs unless needed to distinguish or cross-reference issues. Investigation-only wording must not claim a fix. Include a concise Verification section when checks or remaining proof matter. Omit empty sections.

## Detailed

Within each applicable category, use this order. Omit sections without useful content; never fill them with None, N/A, or boilerplate.

1. **Reported problem:** Symptom, expected result, route, role and conditions when known. Label user reports separately from independent reproduction.
2. **Findings:** Established facts and effects. For several bugs, use `Issue | Finding | Effect`. Cite useful source locations; distinguish code inspection from runtime observation.
3. **Confirmed cause:** Supported causal mechanism, including shared BUG IDs. If unresolved, replace heading with **Cause not yet confirmed** and name the missing evidence.
4. **Corrections:** Only when a prior diagnosis or statement was wrong; explain new evidence. Never use this for ordinary code fixes.
5. **Expected behavior and fixes:** Connect each expected result to an implemented correction, using `Issue | Expected behavior | Fix` for several. For investigation-only work, use **Expected behavior and proposed fixes**. Label incomplete work.
6. **Implementation locations:** Use source tables below. For diagnosis-only work, distinguish inspected locations from proposed edit locations.
7. **Data and access:** Only relevant persisted data, migration, normalization, permissions, tenancy or role constraints. State migration need only when established.
8. **Verification:** Checks executed now and exact outcomes; separate earlier reported results. Distinguish source inspection, automated tests, browser and deployed proof. Map checks to BUG IDs when coverage differs. States: Passed, Failed, Not run, Blocked, Reported previously; not rerun. A test file's existence is not a pass; a local suite cannot prove production behavior.
9. **Remaining checks:** Concrete conditions and expected outcomes not yet verified; no completed checks or generic lists.

With `--history` or an explicit request, add **Origin** after Findings or Confirmed cause. Explain supported evidence and uncertainty, including the difference between incompatible data arriving and code beginning to reject it. Hide hashes unless requested. Add **Recommendations** after Remaining checks only for supported follow-up beyond the immediate fix; do not implement automatically. Shared verification or setup belongs in a clearly scoped shared section instead of duplicated category text.

## Source tables

Actual changes:

| File | Lines | Status | Type | Change |
|---|---|---|---|---|
| `relative/path` | `12-16` | Modified | Fix | Specific correction |

Status is Added, Modified, Renamed, or Deleted. Type is New, Improvement, Fix, Refactor, Removal, or Unclear. They answer different questions. A regression test file can be Added / Fix. One file can have several rows with different purposes. Renames show both old and new paths. Target lines belong to added or modified code; baseline lines for removals must be marked `old`. Use an exact starting line if that is all that is known; never invent a range. Use `—` for binary or unavailable lines. Prefer narrow relevant ranges over whole-file ranges. Paths are relative to each named repository root; keep independent revision context internally.

Inspection-only locations:

| File | Lines | Finding or proposed change |
|---|---|---|
| `relative/path` | `24` | Inspected behavior or proposed edit owner |

Do not present a proposed edit as Modified. A helper's diff ranges are file evidence, not causal or task attribution. Check actual source and the selected revision before citing.

## Evidence limits

Use exact test counts only from current command output or clearly attributed supplied evidence. Qualify previous results after later code changes. Map each check to the condition it covers; one shared suite pass does not verify all BUG IDs. Code inspection does not prove browser timing, rendering, device or deployed behavior. List failures and blockers. Do not turn filenames, route names, or commit chronology into root-cause or permission conclusions.
