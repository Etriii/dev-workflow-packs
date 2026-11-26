# Balanced planning

This is the default for new work. Keep decisions complete, reading selective and file ownership clear. Use the smallest coherent task split; one task is valid. Do not require more tasks or documents merely to fill a template. Integration proof belongs to the affected task unless multiple independent results need a named integration owner.

## Revision layout

```text
<feature>/<revision>/
  .package.json
  PLAN.md
  PROMPTS.md
  STATUS.md
  DECISIONS.md
  phase-01/
    PROMPT.md
    outputs/                 # only when actual evidence is produced
  phase-02/
    PROMPT.md
  MERGE_PROMPTS.md            # only when isolated work needs integration
```

Root files own shared facts. Each phase folder owns its prompt and outputs; there is no additional features/ or prompts/ hierarchy. Preserve a supplied Markdown file as ORIGINAL_PLAN.md, or PDF as SOURCE_DOCUMENT.pdf, with its checksum. Chat/PDF working decisions belong directly in PLAN.md; do not duplicate that plan as an original snapshot. Actual supplied snapshots survive revisions. The helper reserves metadata and snapshots, not a completed package or placeholder output folders.

| File | Owns |
|---|---|
| PLAN.md | Goal, exclusions, accepted requirements, shared contracts/policies, source evidence and limits, task/dependency map, common recovery constraints. Split a large reusable contract only when necessary; link its relevant sections. |
| PROMPTS.md | One linked row per stored Pxx: descriptive objective, prerequisite/start condition, separate-session eligibility, safe concurrent partners/group, isolation and integration owner. Link merge sections when present. Distinguish separate sessions from safe simultaneous writes. |
| STATUS.md | Sole current task state, evidence pointers, source/branch/commit identity, actual blockers and immediate next action. Replace obsolete current statements; outputs own long history. |
| DECISIONS.md | Meaningful questions, alternatives and chosen answers, tagged by task; proposed/applied/changed/reverted state, proof and the two recovery prompts described in the completion contract. Initially state that no execution decisions exist. |
| phase-NN/PROMPT.md | Only that Pxx's objective, owned components, dependencies, exact reading set, changes, acceptance, actual check commands, completion conditions and detailed feature-specific commit drafts. Use phase-01 for P01, phase-02 for P02, including IDs above 99 without truncation. |
| phase-NN/outputs/ | Actual logs, screenshots, test artifacts and optional result summary. Do not create empty logs, copy all source, or regenerate evidence already valid for the relevant source. |

## Current state and minimal reading

STATUS.md has an exact `## Current` section with this table, using one row per task:

```markdown
## Current

| Task | State | Evidence |
|---|---|---|
| P01 | NOT_STARTED | NOT_RUN |
| P02 | NOT_STARTED | NOT_RUN |

Source: actual planning revision; no implementation proof yet.
Next: invoke the first ready task from PROMPTS.md.
```

States are NOT_STARTED, IN_PROGRESS, PAUSED, BLOCKED, VERIFIED, MERGE_PENDING, MERGED, COMPLETE or REVERTED. VERIFIED means worker proof, not integration. A task consuming an isolated result waits for MERGED; sequential prerequisites require COMPLETE or MERGED. Missing state is unknown, never ready. Status output is recorded eligibility and always requires live source/preflight validation; it is not a scheduler or proof of current correctness. Any historical notes go outside Current, preferably in the owning outputs. Routine status/commit updates do not create new package revisions.

For a read-only task expecting no tracked change, put `NO_COMMIT_EXPECTED: <specific reason>` in its prompt instead of inventing a commit draft. This exception does not excuse a subject-only draft or permit an implementation task to omit its required message.

Start a task by reading its prompt, STATUS Current and only its named PLAN/contract sections and source. Read decisions only when they affect the task. Do not blanket-read every document, old failed run or unrelated skill reference. Keep one owner for shared policies and acceptance; link them rather than copying bodies. A necessary detail is retained even if it makes a prompt longer.

## Metadata and checks

New Balanced reservations use schema 4, profile=balanced, explicit ordered phases/dependencies, and phase mappings such as `P01: phase-01/PROMPT.md`. Keep skill assignments and saved commit/test policies. Default parallel_mode is worktree inside Git and analysis outside Git. This assesses independence; no safe split is a valid result with a concise reason, empty groups/tasks/merges and no merge file. Explicit off skips preparation. Only grouped tasks need parallel ownership/read-set/resource metadata in schema 4. Actual safe groups follow the parallel reference. Never fabricate a committed baseline to make a prompt look ready.

Run the helper check plus manual source-to-plan review. It checks required documents, ordered mappings, dependencies, task state coverage, index links, draft bodies, two addressed recovery prompts per decision and isolated metadata. Worker decision logs are inspected only when present under their owning outputs. It cannot establish semantic independence, native agent adherence, decision safety or runtime completion. A chat task with one prompt needs six files total: metadata, four shared documents and the prompt; no source duplicate, evidence files or merge file is necessary.

Revisions inherit the saved profile and policies unless explicitly changed. New Balanced content derived from an old Detailed/Light revision retains accepted requirements, actual supplied snapshots and valid evidence, with old-to-new task mapping. Leave the old package readable in place; no automatic migration or untracking.
