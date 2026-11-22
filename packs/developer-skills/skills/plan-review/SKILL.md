---
name: plan-review
description: Review a draft plan or reviewed requirements for solution value, coverage, dependencies and readiness before implementation planning or development.
---

Write user-facing responses and generated reports in English, even when the request is in Tagalog or Bisaya. Preserve original quotations, code, identifiers, and application content when needed for accuracy.

# Plan Review

Use after `$request-review` when reviewed requirements exist, or directly on a complete draft implementation plan. This is an optional review before `$implementation-plan`, which creates the executable plan. Codex uses `$plan-review`; Claude Code uses `/plan-review`. These are agent-chat requests, not shell commands.

## Interface

Accept an identified reviewed-requirements handoff, a draft plan path, or clearly identified current-conversation material. A path-like input must exist. Bare invocation uses one unambiguous source already in context; otherwise ask for the source. `--detailed` changes presentation, not inspection depth. `--summary` condenses one identified plan-review result for a client without re-investigating; if several results could apply, ask which. Accept a natural `help` request for examples without inspecting the project. Reject unknown flags, competing sources, and `--summary` combined with new review input or `--detailed`. Do not silently choose a different source or review.

## Review

1. Resolve the target application and source. Preserve original request IDs, source references, decisions and scope from a request-review handoff. Treat its recommendations and defaults as proposals with their recorded provenance. If the input is a plan, read every phase at a high level before inspecting any phase deeply; preserve phase and subtask IDs, acceptance criteria and source lines. State which source type was reviewed.
2. Compare each included request and proposed solution with current code, tests, routes, permissions, data and relevant integrations. Distinguish reported need, inspected existing behavior, demonstrated behavior, already satisfied work, gaps and unknowns. Do not treat unchecked boxes, a frozen interface, test-file presence or a prior review as proof of functioning or deployed behavior. Revalidate drift-prone evidence from an older handoff where feasible; otherwise label it stale or unverified.
3. Test whether the solution actually addresses the request and whether its benefit is supported. Recommend reuse, a narrower change, investigation, deferral or no implementation when better supported. Describe the work that would be done, why, and the expected user or operational benefit in plain language. Qualify projected benefits; do not promise performance, security or business outcomes without evidence. Identify observable acceptance checks, material access/data effects, prerequisites, shared interfaces, backward dependencies, cycles, missing coverage and factual blockers. For a complete plan, map each request to its proposed phase and flag missing or misplaced work; for reviewed requirements without a plan, say phase assignment is pending implementation-plan rather than inventing phases.
4. Produce the categorized review using [report rules](references/report-format.md). Keep request, proposed solution, planned work, rationale and expected benefit distinct. Mark proposals as proposals, not completed changes. End the default or detailed report with an overall summary of the recommendation, blockers and next decision. `--detailed` adds source and phase traceability, alternatives, dependencies and acceptance evidence while retaining the same investigation and conclusions. `--summary` reuses the identified result, includes the client-relevant scope, benefits, restrictions, decisions and blockers, and omits file tables and internal execution detail. A summary alone is not a complete planning handoff.

Review and recommend by default. Preview any proposed plan reordering with an old-to-new mapping and coverage proof; obtain approval before replacing a plan and preserve completed history. Do not edit application code, implement phases, stage, commit, push, deploy, contact a client or automatically invoke another skill. Client approval of a summary settles only the stated scope and decisions; implementation still needs its own authorization. For a later `$implementation-plan` request, pass the full reviewed requirements and plan-review findings, not just the short client summary. Its own phase sizing and output choice remain separate.

## Generated artifacts

Apply this section only when the workflow saves generated reports, logs, previews, or run evidence. Use a stable skill-owned root in the target workspace, never the installed skill directory. Allocate each new run with an exclusively created `YYYYMMDDTHHMMSSZ-<unique-id>/` directory (UTC); preserve earlier runs and resume the identified active run. Reject linked paths, traversal, and unrelated same-name folders.

Before saving inside Git, resolve the intended repository root, refuse already tracked output, and inspect its `.gitignore`. Preserve existing bytes and line endings; append a root-anchored rule for only the generated output root when needed, creating `.gitignore` if absent. Verify exclusion with `git check-ignore`; never untrack files automatically. Outside Git, disclose that exclusion is unverified; workflows requiring Git retain that prerequisite. If safe storage or required exclusion fails, report the exact limitation before saving and use chat only when this workflow permits it.

Preserve existing state schemas, version identifiers, historical files, and resume paths; timestamp new run evidence beneath its existing owner without an implicit migration. Application source and project documents explicitly intended for version control retain their own contracts. This section does not authorize extra output for a chat-only request or expand the workflow's scope.
