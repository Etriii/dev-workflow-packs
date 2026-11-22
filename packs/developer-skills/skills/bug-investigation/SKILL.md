---
name: bug-investigation
description: Investigate reported bugs across roles, pages, or repositories; optionally fix and verify them with evidence-based brief or detailed reports.
---

Write user-facing responses and generated reports in English, even when the request is in Tagalog or Bisaya. Preserve original quotations, code, identifiers, and application content when needed for accuracy.

# Bug Investigation

Codex: `$bug-investigation`; Claude Code: `/bug-investigation`. These are agent-chat requests. Default: investigate and recommend, without application edits. `--fix` authorizes a focused correction. `--verify` rechecks an identified prior investigation or fix. `--detailed` selects the evidence report. `help` gives short examples and performs no investigation.

## Interface

Accept a quoted problem or established conversation subject, plus optional `--fix`, `--verify`, `--detailed`, `--group role|page`, `--history`, `--project ALIAS`, and `--save PATH.md` in sensible order. `--verify --fix` may correct a failed recheck after investigating it. `--history` inspects local Git history only when useful. `--save` writes only the selected Markdown format to the explicit path; refuse an unrelated existing document and do not save by default. Reject unknown options, missing values, duplicate conflicting selectors, and positional `detailed`. Use [scripts/bug_investigation.py](scripts/bug_investigation.py) `parse` if option ambiguity matters; it validates syntax, not subject identity or authorization. Bare invocation uses a clearly established current problem; otherwise ask for it. Verification without an identifiable problem, report, or active investigation must ask which one to verify.

For `--project`, use the compatible project registry described in [repository evidence](references/repository-evidence.md). The helper works without `change-report`. Inspect only selected repositories. Validate every selected repository before `--fix`; unavailable members limit read-only coverage and prohibit a cross-repository fix that depends on them. Never switch branches, fetch, pull, merge, initialize, stage, commit, push, deploy, or modify production data for this skill.

## Investigation

1. Establish trigger, observed result, expected behavior, role, page, environment, and data conditions from the report and available context. Keep reported behavior separate from reproduced behavior. Read supplied requirements, plans, and handoffs for intended behavior; checked boxes are not proof.
2. Trace the relevant UI/route/controller/service/storage/query/permission/response path as it applies. Inspect code, tests, logs, sanitized examples, config, and schema only where useful. Reproduce safely with local fixtures or isolated data when practical. Do not treat the visible symptom or latest touching commit as the cause.
3. Separate confirmed causes, contributing conditions, distinct defects, ruled-out explanations, and unresolved possibilities. A rule that seems surprising may be intentional; resolve material business-rule ambiguity before changing it. Do not weaken permissions, validation, or error handling to suppress a symptom.
4. If `--history`, compare when incompatible data or assumptions entered with when code began rejecting them. State only supported origin conclusions; omit hashes unless explicitly requested.
5. If `--fix`, make the smallest coherent correction in the responsible owner, preserve unrelated edits and access boundaries, add meaningful regression coverage, and run focused relevant checks. A regression test should exercise the failing condition, expected result, and an important unchanged boundary; show that it detects the old defect when practical. Without `--fix`, do not modify application code. Without `--fix`, `--verify` remains read-only.
6. For follow-ups, reuse an identified report or active bug context and preserve its BUG IDs. Read final integrated changes when agents contributed; distinguish unmerged branches or worktrees and do not double-count fixes. Report checks run now separately from earlier reported results.

Assign BUG-01, BUG-02, etc. when needed to distinguish issues. Preserve IDs in follow-ups; never renumber when another appears. One shared cause can cover several IDs, but mark verification separately for each. Mention unrelated findings separately without silently expanding fix scope.

## Report

Read [report rules](references/report-format.md) and use the [brief](assets/brief.md) or [detailed](assets/detailed.md) template as a shape, never as evidence. Group by actual role or page based on navigation and access; `--group` overrides presentation only. Use relevant non-page categories for background jobs, data processing, or configuration. For unrelated projects, add separate project sections; never a Project table column. Give a shared issue one primary location and reference it elsewhere.

Brief is a compact categorized problem, cause, proposed or implemented correction, and material verification limit. Detailed uses applicable sections in the required order, exact relative source locations, and truthful evidence states. Distinguish inspected code, runtime observation, current tests, previous test reports, browser checks, and deployed proof. Source locations cannot establish causality by themselves. Do not invent paths, line ranges, test counts, origins, or access roles. Keep hashes hidden unless asked. Redact credentials and personal records.

If `change-report` is available, an optional later handoff is: investigate and fix here, verify here, then request `change-report` for the role/page change walkthrough. Do not invoke it automatically or require it to be installed.

## Generated artifacts

Chat output creates no files. `--save` is a user-requested project document: check the explicit destination, parent, tracking/ignore status, and existing content before writing. Do not overwrite an unrelated document or change `.gitignore` to hide the report. If the requested output is generated run evidence rather than a deliberate project document, use a stable target-workspace `.bug-investigation/` root and exclusively create a UTC `YYYYMMDDTHHMMSSZ-<unique-id>/` folder. Reject links, traversal, and unrelated same-name folders; preserve prior runs. In Git, refuse tracked generated output, append only a root-anchored ignore rule if needed while preserving existing `.gitignore` bytes, and verify exclusion with `git check-ignore`. Outside Git, disclose that exclusion is unverified. Do not create a run folder for normal chat or `--save` to a deliberate project document.
