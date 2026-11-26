# Parallel preparation and integration

Balanced assesses independence by default, preparing worktrees for safe groups inside Git and analysis outside Git. Detailed stays sequential unless selected. Bare --parallel-ready means analysis; =worktree requires Git; =off disables preparation in a new revision. Light permits off only. These are instructions for later execution: planning never creates a branch/worktree, launches a worker, merges or deletes anything.

## Prove the split

Trace contracts, transitive dependencies, owned files, generated outputs and mutable resources (databases, workers, ports, fixtures). Different filenames are insufficient. Shared read-only contracts are allowed; freeze them for a group and revalidate affected workers after changes. Unknown coupling stays sequential. A small task may be cheaper sequentially; no safe split with a specific reason is a valid result.

PROMPTS.md marks each task's prerequisite/start condition, separate-session eligibility and safe concurrent partners. Separate sessions are not automatically concurrent. Include integration work in the named task ownership/count rather than hiding an extra stage. Preserve the current integration branch unless the user selected another target. A grouped worker needs an actual committed baseline; detached/unborn Git state cannot be guessed into readiness.

Balanced records grouped worker ownership/read sets/resources only; ungrouped tasks retain their normal prompt/dependencies. Legacy schema 3 analysis describes every phase. No groups means no worktree identities or merge file.

## Worker lifecycle

Every invoked isolated task must:

1. Inspect live root/branch/HEAD/status and existing worktrees/refs. Validate baseline relevance and ownership. Never reset, stash unrelated changes, silently move the baseline or reuse an unowned branch/directory.
2. Create only its named branch and separate absolute worktree after invocation; choose short sibling paths, never nested directories. Record ownership, baseline and created paths. Resume existing work only after its identity matches.
3. Verify exact ignored-package access; .implementation-plans does not follow Git branches. Read the canonical package through its absolute path or copy only the needed files and verify hashes before writing source. Explicitly run source commands in the worker worktree.
4. Isolate mutable resources and complete owned implementation/tests plus directly related corrections. Resolve routine reversible choices; a newly discovered ownership or shared-contract conflict stops only dependent work and requires a recorded resolution before crossing that boundary.
5. Store actual commands, source/commit identity, results and material remaining gates under phase-NN/outputs/ for Balanced, or evidence/<phase-id>/ for legacy packages. Meaningful worker decisions go in the owned output DECISIONS.md; one integration owner folds results into shared STATUS/DECISIONS (legacy PROGRESS/HANDOFF). Workers never race to rewrite shared files. Transfer and verify evidence before cleanup.
6. Respect saved commit policy: off leaves owned changes with a detailed draft and integration pending; scoped permits and auto requires verified owned local commits. Failed required checks, missing prerequisites and no owned changes prevent a commit. Stop after this selected task with a recommended next move and copyable prompt; do not merge or launch another worker automatically.

Coupled multi-repository tasks stay sequential unless split coherently. Different repositories require separate integration operations.

## One shared merge file

Balanced uses root MERGE_PROMPTS.md; legacy Detailed uses prompts/MERGE_PROMPTS.md. Exactly one file holds all named operations with exact level-two headings such as ## M01 and ## M02, shared rules first, descriptive objectives and separators. Nested headings are level three or deeper. PROMPTS.md links the sections; do not duplicate bodies.

Each operation identifies the exact package/repository, target and source branches, actual baseline, dependencies, owner, required combined checks, evidence/decision destinations, allowed corrections and recovery/cleanup rules. Include one copyable request with real paths:

~~~text
Execute only M01 from "<exact-package>/MERGE_PROMPTS.md". Read shared rules and its selected section. Integrate only its named verified commits, complete affected integration checks and clear in-scope corrections, preserve evidence, remove eligible owned worktrees and safely delete merged branches, record the outcome and stop.
~~~

Use the legacy path for old layouts. The accessor displays only the named section; it must instruct the agent to read shared rules. Displaying a request grants no execution permission. Invoking it authorizes that named local integration, necessary merge commit and guarded cleanup, not dirty worker commits, unrelated code, push, deployment or another operation. Corrections requiring product-policy decisions or additional scope remain separate.

## Integration and recovery

One owner integrates serially. Establish exact live refs and worker-tested source commits, completed prerequisites, a clean target and no existing Git operation. Inspect target drift since the baseline and revalidate affected assumptions. Source commits must match verified work. Uncommitted results or missing required proof leave MERGE_PENDING. A planned hash alone is not implementation evidence.

Use explicit refs and repository merge policy. Never force-update, automatically rebase/squash, reset or stash. Already-landed exact source commits are recognized on resume; do not replay them. Resolve only mechanically clear conflicts or integration regressions within the named owned scope, preserving intended source/target behavior and recording meaningful choices. Ambiguous contracts, unknown ownership and destructive choices stop dependent integration with recoverable hashes, conflict paths, operation state and a copyable recovery request.

After merging, run affected combined checks on the target, beyond worker checks. Fix clear authorized integration failures and rerun affected proof. If required checks still fail or scope is insufficient, retain source branches/worktrees/evidence and record the landed commit and exact next action. Never remove recovery material to make the state look complete.

Only after combined proof passes:
- Verify all worker source commits are reachable from the target.
- Copy/verify needed ignored/untracked artifacts and decision records into durable package storage.
- Verify every branch/worktree is task-owned, clean and no longer needed by another worker.
- Remove only those exact owned worktrees and use git branch -d, never force deletion.
- Verify Git registration and directory existence, especially on Windows. Before any recursive filesystem removal, resolve and check the absolute target against the recorded owned path.

Uncertain ownership, valuable unpreserved artifacts or a dirty worktree leave cleanup pending. Do not remove pre-existing worktrees. Cleanup failure is reported independently from successful integration. Update canonical current source/target identities, checks, decisions, cleanup outcome and recommended next request. Stop at the named operation.

## Metadata

Schema 4 Balanced and schema 3 Detailed share these fields; profile/layout-specific files differ:

| Field | Contract |
|---|---|
| dependencies | Every Pxx maps to prerequisite IDs; ordered, existing and acyclic. |
| parallel_reason | Source-backed rationale, including when no split is safe. |
| parallel_groups | Gxx maps to at least two independent Pxx IDs; each appears in at most one group. |
| parallel_tasks | Schema 4 maps exactly grouped phases; schema 3 maps all phases. Each has concrete owned_paths, isolated write_resources (possibly empty), existing relative read_set files/fragments, and a reason. |
| Worktree identity | Grouped worktree tasks additionally have absolute repository/worktree, distinct branch and actual full base_commit. Worktrees are outside the source checkout and not nested in each other. |
| merges | Mxx identifies phases (each isolated source covered once), existing owner_phase depending on its sources, repository, different target_branch, actual target_commit and acyclic depends_on merge IDs. Analysis/off have no merges. |

The helper checks graph/file/resource/worktree/merge structure and live Git ref syntax/existing baseline commits. It never determines semantic independence, mutates Git, runs worker checks or certifies native agent adherence. Manually review read-set relevance, shared resources, ownership and source-bound acceptance before marking ready. Disabling parallel preparation clears new revision metadata without deleting outstanding worktrees or their recovery evidence.
