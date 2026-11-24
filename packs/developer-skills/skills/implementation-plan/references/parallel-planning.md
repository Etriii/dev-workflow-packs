# Parallel preparation and merge prompts

Read only for parallel preparation. `--parallel-ready` means `analysis`; `--parallel-ready=worktree` additionally prepares isolated Git execution and integration instructions. `--parallel-ready=off` removes parallel preparation in a new revision. Light mode cannot combine with analysis/worktree. Planning performs read-only Git inspection and package writes, never branch/worktree creation, implementation, merges or deletion. No unattended executor or scheduler is installed.

## Establish independence

Trace behavior, contracts and transitive dependencies before grouping tasks. Account for shared files, generated outputs, schema/migration ordering, API/data contracts, databases, workers, ports, fixtures and test resources. Different filenames alone do not establish independence. Record every phase's prerequisites, concrete owned repository-relative paths, mutable resources, exact package reading set, output and reason. Shared read-only contracts are allowed; mutable shared state must be isolated or serialized. Freeze shared contracts for a parallel group; contract changes require coordinator review and revalidation of affected workers.

Describe eligible groups in PHASES.md with source-backed reasons and a dependency/ownership table. A phase belongs to at most one group. Do not group transitive dependencies or overlapping ownership. Unknown coupling is sequential. A valid result is no parallel group with a specific explanation. Integration and merge work belong to identified phases and count in sizing, dependencies and acceptance; do not disguise extra work to fit `--max-phases`.

Analysis mode does not promise concurrent writes in a shared checkout. Read-only work may overlap; simultaneous writers require verified isolation through worktrees or separate checkouts. Preserve the current branch; record another integration target only when selected. In detached/unborn Git state, settle a real branch and committed baseline before marking worktree prompts ready.

## Worktree execution contract

For each grouped task identify one Git root, actual committed baseline, new task-owned branch, separate absolute worktree directory and integration target. A task that spans coupled repositories stays sequential unless it can be coherently split within the confirmed scope/count. For multiple repositories use separate per-repository merge operations. An instruction naming a branch is not isolation; each simultaneous writer needs a different working directory and index. Choose short sibling worktree paths, avoiding nesting and collisions.

Every later worker prompt must:

1. Inspect live Git roots, branch/HEAD, status and existing worktrees/refs. Verify the saved baseline still applies; do not silently move it, reset, stash unrelated changes, or reuse an unowned branch/directory. Record stale planning evidence and revalidate before changes.
2. Create only its named branch/worktree after the prompt is explicitly invoked. Preserve the integration checkout and unrelated work. Record created paths, branch and baseline as task-owned evidence. Existing owned work resumes only after matching those records.
3. Verify access to the exact package revision and its relevant read set. Ignored `.implementation-plans/` files do not follow branches. Use the canonical absolute package path read-only or copy the required files, wait for copying to finish and verify hashes. Rewrite working-directory instructions explicitly rather than accidentally editing the canonical checkout.
4. Use isolated mutable test/runtime resources and concrete ownership. Stop and report a discovered shared-contract or ownership conflict; do not edit another worker's scope.
5. Run required checks and record observed result, source commit, outstanding work and commit drafts in a task-owned evidence file in the canonical package's `evidence/<phase-id>/` directory. One coordinator alone updates canonical PROGRESS.md, HANDOFF.md, shared contracts and COMMIT_MESSAGES.md; workers submit drafts rather than racing on those documents. Verify artifact transfer before removing a worktree.
6. Respect saved commit policy. With commits off, leave the result ready for an explicit commit request; mark merge pending. With scoped/auto, commit only verified owned changes as authorized. Record the actual branch, HEAD and checks. Stop at the selected task; do not merge or start another task automatically.

## One file for all merge prompts

Write exactly `prompts/MERGE_PROMPTS.md` when isolated tasks exist; do not write one merge file per task. Use exact level-two headings `## M01`, `## M02`, and so on, with a descriptive objective underneath and `---` between sections. Use level-three headings within a section. Include shared rules in this file before its sections, but each selected section must explicitly tell the executing agent to read those shared rules and the named relevant package sections. The `prompt` accessor returns only the selected section, not the whole file.

Each section states its exact package and repository, integration target and planning baseline, source phases/branches and dependency gates, owner phase, verification commands, evidence destinations, conflict/recovery rules and cleanup eligibility. Include one copyable agent-chat request with real absolute paths:

```text
Execute only M01 from "<exact-package>/prompts/MERGE_PROMPTS.md". Read its shared rules and selected section, verify live prerequisites, integrate only its named committed work, run required checks, preserve evidence, perform eligible owned cleanup, record the outcome and stop.
```

This request is for a later execution session, not a shell command and not a planning-skill invocation. Do not require `$implementation-plan` in it. PROMPTS.md links to the file's `#m01`, `#m02` anchors; no duplicated bodies. `prompt <package> M01` displays one section read-only. Copying and invoking the execution request authorizes only that local integration and guarded owned cleanup, including a necessary merge commit; it does not authorize source-code fixes, committing dirty worker changes, pushing, deployment or another merge operation.

## Integration, failure and recovery

One coordinator integrates serially. Before touching the target, establish all of the following:

- The exact package, repository, target branch, source branches and expected actual source commits are identified by live refs and worker evidence. Source commits match the changes that were verified. A planned baseline hash alone is not implementation proof.
- The selected merge's prerequisites and required worker checks are complete. Uncommitted results, stale evidence, failed/skipped required checks and unknown ownership leave `MERGE_PENDING`. A merge request never silently enables source commits.
- The target checkout is clean, no Git operation is in progress, and its HEAD is suitable for this integration. Inspect target changes since the recorded baseline and revalidate affected assumptions/checks. Do not assume a dirty main checkout is disposable.

Integrate only named refs using the repository's merge policy. Use explicit refs and record actual source and target hashes; do not force-update refs or automatically rebase, squash, resolve ambiguous conflicts, reset or stash. If the exact source commits are already ancestors of the target, record that rather than merging again. Previously completed operations must not replay on resume.

On a conflict, stop additional merges and cleanup. Record conflicted paths, operation state, source/target hashes and the exact resume action. Leave the state recoverable; do not invent a resolution or declare integration complete. After a successful merge, run the selected combined checks on the integrated target, beyond individual worker checks. On failure retain branches/worktrees/evidence, record `MERGE_PENDING` with the landed commit and failing command, and stop. A retry recognizes landed commits and reruns outstanding proof rather than duplicating merges. Application fixes require separately authorized scope.

Only after combined proof passes, copy/verify durable task evidence and untracked/ignored deliverables needed for recovery. Verify every source commit is reachable from the target, each branch/worktree is recorded as task-owned, worktrees have no uncommitted changes, no worktree still needs a branch, and all referenced artifacts remain accessible. Remove only those exact owned worktrees and use safe merged-branch deletion (`git branch -d`), never force deletion. Cleanup failure is recorded separately from successful integration; verify both Git registration and directory existence, especially on Windows. Never recursively delete a computed directory without checking its resolved target. If ignored/untracked artifacts are valuable or ownership is uncertain, leave cleanup pending. Do not remove pre-existing worktrees or branches.

PROGRESS.md records source commits, resulting target commit, actual checks, integration state and cleanup outcome; HANDOFF.md identifies the exact next outstanding action. Completing a merge does not run the next task or merge section.

## Schema 3 metadata

Keep source snapshots, sizing and saved policies intact. Populate these fields manually after reservation, then run the helper check:

| Field | Contract |
|---|---|
| `profile` | `detailed` for parallel work. |
| `parallel_mode` | `analysis` or `worktree`. |
| `dependencies` | Every Pxx maps to a list of existing prerequisite IDs; acyclic. |
| `parallel_reason` | Evidence-based rationale, including why no split is safe when groups are empty. |
| `parallel_groups` | Gxx maps to at least two mutually independent Pxx IDs. A phase appears once at most. |
| `parallel_tasks` | Every Pxx maps to `owned_paths` (concrete paths, no traversal or glob patterns), `write_resources` (unique mutable-resource names; may be empty), `read_set` (existing package-relative files with optional fragments), and a specific `reason`. |
| Worktree task identity | Each grouped task additionally has absolute `repository` and `worktree`, valid `branch`, and actual `base_commit` (full SHA). Directory and repository identities must not be nested; task worktrees and branch identities must be distinct. |
| `merges` | Mxx maps to `phases` (isolated sources, each covered exactly once), `owner_phase` (existing integration-work owner), `repository` (matching source root), `target_branch` (different from source branches), `target_commit` (actual planning baseline SHA), and `depends_on` (existing merge IDs; acyclic). Analysis/sequential modes have no merges. |

The helper checks graph consistency, concrete overlap, resource collisions, worktree identities and exact section mapping. It reads Git to check root/ref syntax; it does not create worktrees, determine semantic independence, prove that live implementation matches the plan, run tests or perform integration. The author still reviews dependency timing, read-set relevance, acceptance coverage, shared contracts, actual baselines and complete guarded execution/merge instructions. No safe split means empty groups/merges and no merge file, with the reason recorded.

On revision, inherit profile/mode and saved options unless explicitly changed, preserve previous files and valid results, then rebuild affected graphs/prompts from current source and record invalidated evidence. Do not copy a stale ready claim. Turning parallel mode off clears its task/group/merge metadata in the new revision, retaining phase dependencies and explaining outstanding branches/evidence that still need separately authorized recovery.
