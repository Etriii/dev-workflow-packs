# Plan Review

Review a draft plan or reviewed requirements before implementation planning or development. The report explains each request, the proposed solution, what work would follow, why it is justified and the expected benefit. It also checks coverage, dependencies and current implementation. The default and detailed reports end with an overall summary; `--summary` creates a shorter client-ready version of an identified review.

Skill responses and generated reports are in English, including for Tagalog or Bisaya requests. Original quotations, code, identifiers, and application content keep their source language when needed for accuracy.

## Install

### Direct install with npx (recommended)

No manual clone, ZIP download, or Python checkout is required to install this skill. The external CLI obtains the published source for you.

Prerequisites: [Node.js 22.20+](https://nodejs.org/en/download) with npm/npx, network access to npm/GitHub, and [Git](https://git-scm.com/downloads) for repository fallback. If a command is missing, install that prerequisite and reopen the terminal. These are installer prerequisites; the skill's runtime requirements are listed separately below.

PowerShell, from any folder, check tools first:

```powershell
node --version
npm --version
npx --version
git --version
```

PowerShell: replace `D:\My App` with your existing target application, then run each line separately:

```powershell
Set-Location 'D:\My App'
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill plan-review --agent codex claude-code --copy
```

This selects only `plan-review` for Codex and Claude Code in the current project. Review the selected source, agents, scope and destinations in the CLI summary. npm may ask to download the pinned CLI; the skill installer may also prompt. These examples do not force noninteractive approval.

Still in the application folder, confirm the project copies:

```powershell
Test-Path '.agents/skills/plan-review/SKILL.md'
Test-Path '.claude/skills/plan-review/SKILL.md'
```

Both should return `True` for the two-agent project install. Refresh the coding-agent session, then use the chat requests in this README. Installation copies instructions; it does not run the skill.

For one agent, replace `--agent codex claude-code` with `--agent codex` or `--agent claude-code`. For an intended global installation across projects, choose this alternative command after the same prerequisites; do not run both scope examples unless you want both copies:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill plan-review --agent codex claude-code -g --copy
```

Global destinations are shown by the CLI; the project-relative `Test-Path` checks above do not verify global copies. Remote URLs install published files, so local unpushed changes are not included. PowerShell execution-policy errors can use `npx.cmd` instead of `npx`; see [troubleshooting](../../../../docs/NPX_INSTALLATION.md#troubleshooting) for missing tools, names, network access and refresh issues.

### Optional recorded or offline installation with Python

Keep this route when you want manifest verification, retained backups and Markdown operation history. It requires Python 3.11+ and a **complete local collection** first. Follow [download/extract or clone steps](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use), then identify the root containing `tools/`, `packs/`, and `README.md`. `tools/install_skills.py` is a file in that root, not a global command.

PowerShell: replace `D:\Tools\dev-workflow-packs` with that actual collection root and `D:\My App` with the existing destination application. For a ZIP, the extracted root may instead end in `dev-workflow-packs-main`.

```powershell
Set-Location 'D:\Tools\dev-workflow-packs'
python --version
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills plan-review --dry-run
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills plan-review
```

The first installer command previews and writes nothing. The second requests the existing confirmation and performs the copy with operation records. Run them separately. Python uses `--agent both`; npx uses `--agent codex claude-code`. For Python-only Codex or Claude choose `--agent codex` or `--agent claude`. User-scope options are in the [installation guide](../../../../INSTALL.md#choose-a-pack-agent-and-scope).

Use the installer that owns an existing copy for updates/removal; npx and Python maintain different records and protections. Preserve local edits before replacement. See the [pack guide](../../README.md), [npx lifecycle](../../../../docs/NPX_INSTALLATION.md#updates-and-removal), and [recorded removal guide](../../../../UNINSTALL.md).

## Update an installed copy

For an existing **npx-managed project copy**, have Node.js 22.20+ with npm/npx, network access to npm and the recorded source, and Git for repository fallback. Save local edits first. PowerShell: replace `D:\My App` with the application where this skill is installed, then start there:

```powershell
Set-Location 'D:\My App'
```

Update only `plan-review` in that project:

```powershell
npx skills@1.7.4 update plan-review --project
```

For an existing **npx-managed global copy**, choose this alternative from any PowerShell folder. The project command cannot find a global copy:

```powershell
npx skills@1.7.4 update plan-review --global
```

To retain copied Codex and Claude Code destinations, choose this selected global reinstall from any PowerShell folder instead of `update`. It uses the published repository's default branch; if the existing copy came from a local or pinned source, use that original source/ref instead:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill plan-review --agent codex claude-code -g --copy
```

Check the CLI summary and installed destination. For `update`, look for updated, current, skipped or failed status; a skipped update is not success. Verify the intended installed file at the reported destination (for Codex project copies):

```powershell
Test-Path '.agents/skills/plan-review/SKILL.md'
```

For a Codex global copy, verify from any PowerShell folder:

```powershell
Test-Path (Join-Path $env:USERPROFILE '.agents/skills/plan-review/SKILL.md')
```

For Claude Code, check `.claude/skills/plan-review/SKILL.md` in the project or beneath `$env:USERPROFILE` for a global copy. Refresh the agent session before invoking the skill in chat. The updater does not forward explicit `--agent` or `--copy`. For copied global destinations use the selected `add` command above; for a project copy, repeat the matching `add` command in Install with its original source and scope. Python-managed copies use the [recorded replacement workflow](../../../../INSTALL.md#existing-copies-and-replacement), not this npx command. See [global scope, source and removal details](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).


## Use

Refresh the agent session and open the target application. Provide one complete draft plan or a reviewed-requirements handoff from `$request-review`; the handoff must contain the full scope, decisions and evidence, not just its short summary. The skill can use one clearly identified source already in the current conversation. It reads the source and the relevant application code and tests. A source file path must exist. In Codex agent chat, choose one of these independent requests:

```text
$plan-review "docs/plan.md"
$plan-review "docs/plan.md" --detailed
$plan-review "<request-review-run>/reviewed-requirements.md"
$plan-review --summary
$plan-review help
$plan-review Review docs/plan.md for requirement coverage and dependency order. Inspect phase 2 deeply after reading all phases.
```

Replace `<request-review-run>` with the actual saved handoff folder. A review in the current conversation can be requested without a file, for example `$plan-review Review the reviewed requirements above against the application before implementation planning.` For Claude Code use `/plan-review`. These are agent-chat requests, not terminal commands. `--detailed` changes presentation only: the default review investigates the same scope. `--summary` works after one identifiable plan-review result in the conversation; it reuses that result without new source inspection. If several reviews might apply, identify the one to summarize in natural language. `--summary` cannot be combined with `--detailed` or a new review input. Unknown flags, competing source files and missing path-like files are errors. `help` only shows the main examples. A bare invocation with no unambiguous source asks for one.

### Recommended sequence

1. Use `$request-review` to settle informal feedback or a requirements PDF. If a later session will do the planning, save its full `reviewed-requirements.md` handoff.
2. Use `$plan-review "<request-review-run>/reviewed-requirements.md"` to assess whether the proposed solutions address each request and are ready for implementation planning. If a complete draft plan already exists, review that instead; the report also checks phase coverage and order.
3. Use `$plan-review --summary` after the review for copyable client communication. Send it yourself and record any client decisions. The summary does not carry all source evidence needed for planning.
4. When the reviewed scope is settled, give the full request-review handoff and plan-review findings to `$implementation-plan`, which asks its own phase-sizing and output questions. A separate later request is needed to implement a selected phase. `$change-report` explains completed implementation after development; it does not approve the proposal.

None of these steps runs automatically. Client approval of the summary confirms only the stated scope and decisions; it does not authorize code changes or publication.

## Expected result and stopping point

The default report groups by familiar application area or role. Each request gets its original ID when available, its current finding, proposed solution, work to plan, reason and expected benefit, plus a material decision or blocker. Viewable pages include a verified application-relative URL and access conditions; non-page work names its job or integration. A complete plan gets requirement-to-phase coverage and dependency findings. For reviewed requirements without phases, phase assignment stays pending implementation-plan. The report ends with a short overall summary.

`--detailed` retains that readable structure and adds source references and lines, request-to-phase mapping where available, alternatives, dependencies, access/data effects and observable acceptance checks. `--summary` condenses the identified result by client-facing category, preserves restrictions and open decisions, and ends with the decision needed and next step. It omits file tables and internal execution details. A short summary alone is not a complete implementation-plan handoff.

Illustrative default excerpt, not a finding about any real application:

```text
Queue tickets
- REQ-04 — Ticket reprint, /queue-system
  Request: Let visitors reprint an issued ticket without getting a new number.
  Current finding: A print action exists; retention after refresh is unverified.
  Proposed solution: Reprint the stored ticket from the existing queue page.
  Work to plan: Verify ticket persistence and ensure reprint creates no new queue entry.
  Why and expected benefit: A visitor can replace lost paper without losing their place.
  Decision needed: How long should an issued ticket remain available?

Overall summary: The reprint flow is reasonable to plan after retention is decided.
Persistence still needs verification. No implementation has been completed.
```

A `--detailed` review of that fictional case would also identify the source requirement, inspected route and relevant code lines, ticket-retention dependency, and an acceptance check that reprinting does not increase the queue count. A later `$plan-review --summary` would read:

```text
Reviewed source: REQ-04 from the current conversation; persistence remains unverified.

Queue tickets
- Visitors should be able to reprint an issued ticket without receiving a new number.
  We recommend reusing the saved ticket so they keep their place in the queue.
  The existing print action is known, but retention after refresh still needs verification.

Decision needed: Confirm how long tickets remain available for reprint.
Next step: After that decision and persistence check, prepare the implementation plan.
```

Reordering is previewed with old-to-new phase mapping and coverage proof before any approved plan replacement. Normal reviews and summaries stay in chat; they do not edit application code or project documents, stage, commit, push, deploy or contact a client. No tests are implied to have passed merely because source or test files were read. The agent states which checks actually ran and what remains unverified.

Supply the selected source and relevant project in the request or conversation. The only flags are `--detailed` and `--summary`; scope and deep-inspection focus use natural language. Do not add another skill's `run`, `build` or `--auto` syntax.

## Prerequisites and limits

Provide the source plan or full reviewed requirements and access to the application repository. If a saved handoff or repository is unavailable, provide the missing input and rerun the same request. If the handoff is old, the review checks current source where feasible and labels unverified evidence. A summary uses its identified prior review and may be stale; request a new review to refresh it. Reordering needs approval; the review does not implement phases. For a planning handoff, carry the full requirements and findings into implementation-plan, not just the client summary.

The skill itself needs no private runner, API key or third-party runtime package. It uses the target repository's existing tools where the requested checks require them. Installing instructions does not execute them or prove model adherence.

Read the complete [agent instructions](SKILL.md), [installation options](../../../../INSTALL.md), and [npx update/removal guide](../../../../docs/NPX_INSTALLATION.md#updates-and-removal). Use the installer that owns the copy for updates and removal. [Contribute](../../../../CONTRIBUTING.md).

## Generated artifact storage

When this workflow saves reports or run evidence, use its target-workspace output owner and a new UTC `YYYYMMDDTHHMMSSZ-<unique-id>/` run directory; preserve earlier runs. Before saving in Git, the skill preserves or creates the root `.gitignore`, adds only the required scoped output rule, and verifies exclusion. Tracked output is refused without automatic untracking. Non-Git exclusion remains unverified, and workflows requiring Git retain that prerequisite. Unsafe storage or failed exclusion is reported before persistence. Existing state/resume paths and deliberately tracked project documents remain compatible. See the installed [artifact instructions](SKILL.md#generated-artifacts); chat-only requests create no extra output.
