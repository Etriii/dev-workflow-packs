# Completion and decision contract

Use this reference to author later execution prompts. Planning creates instructions and proposed decisions only. A later invocation authorizes the selected task's implementation and checks, never every task in the package.

## Complete the selected task

Give each task its necessary consumers, tests and documentation so it can finish a coherent feature slice in one invocation. Inspect current owners and prerequisites, then implement, verify and correct directly related failures whose intended behavior is settled. A minor reversible design choice is not a reason to stop. Resolve clear in-scope prerequisite corrections without requesting another generic confirmation. Preserve unrelated changes and report the exact ownership of any failure.

Preflight critical tools/services early. Try an existing valid equivalent when a verifier is unavailable; do not present weaker proof as equivalent. Continue independent authorized work when a particular step is blocked. A failed required gate prevents that acceptance claim, not unrelated work. Do not fix unrelated features, skip required checks, silently change contracts or call partial work complete. Ask only for unresolved material public behavior, security, destructive data, billing or hard-to-reverse choices that existing authorization does not settle. Never invent a secret, production permission or external-action approval.

Use focused changed-behavior and affected-integration checks unless full scope or repository gates require more. Reuse passing proof only while the relevant source, dependencies, environment and contracts still match. Recheck the affected proof after drift; do not invalidate everything merely because an unrelated file changed. Keep logs under the selected task's outputs instead of pasting them into current status. Count failed, skipped, unavailable and interrupted checks accurately.

## Meaningful autonomous decisions

Record a decision when the choice affects observable behavior, an architectural tradeoff or recovery. Do not record every spelling, routine coding step or already explicit requirement. Choose the smallest compatible recommendation from evidence, implement it within the selected scope, and record the outcome so the user can review it afterward.

Balanced uses root DECISIONS.md with stable task-qualified IDs such as P01-D01. A sequential task owns its entries. Concurrent workers write their entries to phase-NN/outputs/DECISIONS.md, only when a decision exists; one integration owner folds them into the shared log and updates shared STATUS. Workers never race to rewrite root documents. Detailed creates DECISIONS.md only when needed and links it from its ledger; Light keeps a Decisions section in PLAN.md.

Each record has a `## P01-D01` heading (use the actual task/decision ID), followed by:

- Question: the uncertainty that required a choice.
- Options: the concrete alternatives, including the recommended one.
- Answer and reason: what was chosen and the evidence/tradeoff.
- Status: PROPOSED during planning; APPLIED only after actual implementation, or CHANGED/REVERTED after a later request. Record failed or unverified work honestly instead of marking it applied.
- Before and after: observable previous behavior, affected owned paths, baseline commit or bounded prior diff/evidence needed to reconstruct it; never log credentials or patron data.
- Verification and limits: actual commands/results, scope of proof, dependencies and any recovery limit.
- Exactly two copyable fenced text prompts under `### Change` and `### Undo`.

Use the literal field label `Status: PROPOSED`, `Status: APPLIED`, `Status: CHANGED` or `Status: REVERTED` (a list bullet is allowed). Balanced checks record ownership, duplicate IDs, this state and exactly one addressed fenced text block under each recovery heading; both backtick and tilde fences are supported. It checks the shared log and existing phase-owned output decision logs without merging or rewriting them. These structural checks do not verify that an answer is safe, implemented or tested; inspect actual source and proof before recording those claims.

The Change prompt names the exact package, decision and log path and chooses one real alternative so it is immediately usable. Explain that the choice sentence can be replaced by another listed answer or the user's own choice. Its instructions inspect current source and later dependencies, implement only the changed decision, run affected checks, update the decision/current state, follow saved commit policy and stop. No decision-change CLI or unattended executor is required.

The Undo prompt names the same exact identity and restores the recorded prior behavior. Inspect later dependent changes and preserve unrelated work; derive a focused reverse change rather than blindly resetting the branch or reverting an entire mixed commit. Do not remove used schema/data or pretend deleted/external data can be restored from a code diff. Record necessary recovery prerequisites and ask before a destructive or hard-to-reverse operation. A recovery limit remains visible even if the original choice was reasonable. Verify restoration and mark REVERTED only when proven.

These two requests are later explicit authorization for their bounded local changes, not for another task, push or deployment. Displaying them does nothing. During planning they describe future recovery; never imply the recommended option has already changed application code.

## Commit and result handoff

Off leaves owned changes and a detailed draft. Scoped permits verified owned local commits; auto requires them without a second commit question. Missing required proof, failed checks and no owned changes prevent an automatic commit. Inspect actual staged/unstaged diffs, stage explicit owned paths and verify the final subject, substantive body, changed paths and remaining status. Refresh current commit outcomes even on a commit-only follow-up without creating a new package revision or redoing unrelated checks.

Balanced commit drafts live in the owning PROMPT.md; Detailed uses COMMIT_MESSAGES.md; Light uses its plan section. A no-code verification task explains when no commit is expected instead of inventing a change. Worktree commits and integration are separate states: commits off leaves MERGE_PENDING. Only an explicitly invoked integration request authorizes named merges and eligible cleanup.

After every selected task, return a concise result containing completed behavior, actual checks, decision IDs, real remaining gates, one recommended next move and one fenced copyable prompt with exact current paths/IDs. Prefer the next ready task, named integration or smallest recovery action. If nothing remains, recommend review and provide a read-only review prompt instead of inventing another implementation task. Update the canonical current state or submit the worker result to its named integration owner. Stop; recommending a prompt never executes it.
