---
name: implementation-plan
description: Plan development from Markdown, PDF or chat with compact balanced packages, optional detailed or light profiles, and isolated parallel handoffs. Planning only; implementation requires a later selected task.
---

Write user-facing output in English. Preserve original quotations, code and application content where accuracy requires it.

# Implementation Plan

Trace the current behavior and owners, settle scope, and prepare an actionable plan. New work defaults to Balanced: enough detail to complete each task with a small reading set. Explicit --detailed retains the comprehensive contract; --light is one small task. This skill plans only: never implement a task, run application tests, commit, create branches/worktrees, merge, delete branches or deploy while planning.

## Chat interface

These are agent-chat requests, not shell commands:

- <source-file> [--project PATH] [--max-phases N] [--skills a,b] [--skills-mode auto|all] [--commits off|scoped] [--auto-commit] [--test-scope focused|full] [--balanced|--detailed|--light] [--parallel-ready[=analysis|worktree|off]] starts from a UTF-8 Markdown plan or PDF. Quote paths with spaces; options may precede the path. Missing path-like input is an error.
- create "<task>" [same options] starts from chat. Quoted non-path task text without create remains an alias. Bare invocation asks for the source or task.
- revise <package> "<changes>" [same options] saves a new revision in the same project, carrying valid decisions, evidence, task identities and unspecified policies forward.
- skills <package> lists assignments. --add a,b, --remove a,b and/or --skills-mode auto|all revise only skill selection. Adding/removing the same skill is invalid.
- prompt <package> <Pxx|Mxx> displays one stored execution or integration prompt without executing it.
- check <package> is read-only: report structural errors and manually inspect scope coverage, dependencies, ownership, evidence and recovery instructions.
- status [package] shows recorded current states, dependencies and next action; without a path list recognized project packages. status <package> --history explicitly includes the saved ledger, not all output logs.
- help explains the complete interface and boundaries without writes.

Reject unknown options and conflicts before writes. The --balanced, --detailed and --light selectors conflict with each other; omitted selectors inherit on revision. --auto-commit conflicts with --commits and maps to the helper's commits=auto for later implementation only. --max-phases is a positive hard cap including necessary integration; choose the smallest complete split, never hide extra tasks to fit it. No run, --auto or all-task executor exists.

## Resolve the plan

1. Resolve project, repository instructions, current Git/source, tests and supplied evidence. Read every relevant PDF page; request accessible input if it cannot be read reliably. Carry reviewed requirement IDs and accepted decisions forward, then verify against current code. Distinguish implemented, missing, conflicting and unknown behavior.
2. Read optional ~/.config/implementation-plan/config.json for new work. Require schema_version=1, complete defaults_at_setup/current objects and only commits=off|scoped|auto, test_scope=focused|full, skills_mode=auto|all. Use current; preserve setup defaults. Missing config means off/focused/auto. Invalid config stops before writes. Explicit options win. Existing packages use saved policies, not changed global defaults.
3. State resolved profile, parallel mode, commit/test/skill policies briefly. In Balanced recommend the smallest coherent count and decide routine reversible details from evidence; skip a sizing questionnaire unless scope or a supplied cap needs a material choice. Detailed still offers Compact, Balanced and Custom maximum sizing with exact counts before presentation/writes. Light uses one task. Honor settled answers.
4. Honor an explicit chat/package selection; otherwise ask, recommending a package for work requiring handoff. Routine choices within clear scope should not become questions. Material public behavior, security, destructive data, billing or hard-to-reverse choices require an answer when existing authorization does not settle them. Record meaningful recommended choices and alternatives; planning never labels them implemented.
5. Map requirements to observable acceptance, owners, dependencies and actual verification commands. Include failure/recovery effects where relevant. Prefer complete feature slices over separating necessary implementation from its own proof. Do not invent paths, test results or uniform model-quality claims.

Read only the selected profile reference: [Balanced](references/balanced-planning.md), [Detailed](references/package-contract.md), or [Light](references/light-planning.md). New Balanced work assesses independence by default and prepares worktree instructions only for proven safe groups; without Git use analysis. Detailed is sequential unless parallel mode is selected. Bare --parallel-ready means analysis; =off disables preparation; =worktree requires Git. Revisions inherit profile/mode unless overridden. Read [parallel preparation](references/parallel-planning.md) only for actual isolated groups or explicit parallel requests.

## Save and verify

Inspect selected installed skills and assign them only where relevant in auto mode; all mode routes all selected skills without expanding scope. Do not invoke or install them while planning. Missing/conflicting required skills leave affected work pending. Execution prompts use host-appropriate skill invocations and never invoke implementation-plan.

Use Python 3.11+ and the installed scripts/package_store.py start --project <root> --feature <name> --phase-count <chosen-count>. Pass --profile balanced|detailed|light, selected policies, and --previous for revisions. Markdown uses --source-plan; PDF uses --source-document; they conflict. The helper preserves actual source bytes and checksums. Balanced chat input needs no duplicate original-plan document. Detailed/Light retain their source contract. Use the returned exact path.

Populate profile-specific documents and metadata, then run the same helper's check --package <exact-path>. Review feature coverage, exact reading sets, dependency order, file links, detailed commit bodies, current state, UTF-8 and evidence limits. A structural pass is not semantic quality or implementation proof. Mark ready only after both checks. Report the path, tasks, routing, exclusion and real prerequisites. Package creation runs no application checks and never commits.

## Later execution boundary

A separately invoked task authorizes only its scope. Generated prompts follow saved focused/full test policy and off/scoped/auto commit policy; auto requires verified owned local commits without another commit question. Stage explicit owned paths, use a Conventional Commit subject plus substantive body grounded in actual behavior and checks, verify the commit and remaining status. Failed required checks, missing prerequisites and no owned changes prevent a commit. Detailed drafts remain required even with commits off.

Use [the completion contract](references/execution.md) when authoring execution prompts: routine decisions are recorded with change/undo requests, in-scope failures are resolved, independent work can continue, and every result includes a recommended next move and copyable prompt. Shared policies are referenced once, not pasted into every task. Detailed uses PROGRESS/HANDOFF/COMMIT_MESSAGES; Balanced uses STATUS and task-prompt commit drafts; Light uses sections in PLAN.

A later explicit commit-only request rereads the exact active revision's matching draft, compares actual owned diffs and recorded checks, adapts and verifies only that local commit. It does not authorize product edits, unrelated files, push or another task. Do not rerun checks or create a package revision solely for committing unless a repository rule/hook requires it; refresh the recorded commit outcome/current status.

Integration requires explicit invocation of the named merge request. It covers named verified commits, combined checks and eligible owned cleanup only. Planning and displaying a prompt authorize no Git mutation. Never automatically continue to another task, push or production change.

In host read-only Plan mode, write nothing. A package-creation host plan contains only package preparation/checking steps; its Implement plan action authorizes that package creation only. After a package exists, generic continuation without an identified task is insufficient to start application work.

## Generated artifacts

Reserve under <project>/.implementation-plans/YYYYMMDDTHHMMSSZ-<feature>/YYYYMMDDTHHMMSSZ-<unique-id>/. Each revision has .package.json; store/feature ownership markers protect unrelated folders. Resume an identified unfinished revision; preserve prior revisions and original supplied evidence. Old detailed/light and docs/<feature>/<run-id> packages remain readable without implicit moves.

The helper rejects linked/traversing paths, unowned or tracked output. It adds only the root-anchored /.implementation-plans/ rule when necessary, preserves existing ignore bytes/line endings, verifies Git exclusion and never untracks files. Outside Git disclose unverified exclusion. Package writes and that narrow ignore rule are the only planning mutations. Installed skill files are never artifact destinations.
