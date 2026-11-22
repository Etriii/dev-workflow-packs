# Ultimate QA

Run a versioned initialize → audit → plan review of an existing application.

Skill responses and generated reports are in English, including for Tagalog or Bisaya requests. Original quotations, code, identifiers, and application content keep their source language when needed for accuracy.

## Install

### Direct setup with curl and npx (recommended)

This skill needs the complete QA kit's templates and helpers after installation. This route downloads a ZIP with curl, retains it in a durable folder, and installs from that same snapshot with npx. A manual Git clone is not required. The QA workflow also requires Python 3.11+ at runtime; Word/client work has additional prerequisites below.

Prerequisites: [Node.js 22.20+](https://nodejs.org/en/download) with npm/npx, network access to npm/GitHub, and [Git](https://git-scm.com/downloads) for repository fallback. If a command is missing, install that prerequisite and reopen the terminal. These are installer prerequisites; the skill's runtime requirements are listed separately below.

PowerShell, from any folder, check tools first:

```powershell
node --version
npm --version
npx --version
git --version
curl.exe --version
Get-Command Expand-Archive
```

PowerShell: replace `D:\My App` with your existing application folder. Choose a new, durable kit directory for `$qaKitFolder`; do not use an external CLI's temporary source directory.

```powershell
$qaKitFolder = 'D:\Tools\dev-workflow-packs-qa'
if (Test-Path -LiteralPath $qaKitFolder) { throw 'Reuse the existing QA kit below, or choose a new kit folder.' }
New-Item -ItemType Directory -Path $qaKitFolder -ErrorAction Stop | Out-Null
curl.exe --fail --location --output "$qaKitFolder\dev-workflow-packs-main.zip" 'https://github.com/Etriii/dev-workflow-packs/archive/refs/heads/main.zip'
if ($LASTEXITCODE -ne 0) { throw 'QA kit download failed.' }
Expand-Archive -LiteralPath "$qaKitFolder\dev-workflow-packs-main.zip" -DestinationPath $qaKitFolder -ErrorAction Stop
$env:ULTIMATE_QA_KIT = Join-Path $qaKitFolder 'dev-workflow-packs-main\packs\ultimate-qa'
Set-Location 'D:\My App'
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa --agent codex claude-code --copy
```

The selected skill and support files now come from the same downloaded source. Keep the kit folder available. To reuse that existing kit instead of downloading again, use:

```powershell
$env:ULTIMATE_QA_KIT = 'D:\Tools\dev-workflow-packs-qa\dev-workflow-packs-main\packs\ultimate-qa'
Set-Location 'D:\My App'
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa --agent codex claude-code --copy
```

Set the kit path again in a new terminal and start the coding agent from this terminal in the application, or provide the absolute kit path to an already-running agent. The environment assignment applies to this process and its children; it does not reconfigure an agent already running elsewhere. The kit is not the application to review. See the [full QA setup](../../../../docs/NPX_INSTALLATION.md#ultimate-qa-support-files) for the complete pack and helper verification.

This selects only `ultimate-qa` for Codex and Claude Code in the current project. Review the selected source, agents, scope and destinations in the CLI summary. npm may ask to download the pinned CLI; the skill installer may also prompt. These examples do not force noninteractive approval.

Still in the application folder, confirm the project copies:

```powershell
Test-Path '.agents/skills/ultimate-qa/SKILL.md'
Test-Path '.claude/skills/ultimate-qa/SKILL.md'
```

Both should return `True` for the two-agent project install. Refresh the coding-agent session, then use the chat requests in this README. Installation copies instructions; it does not run the skill.

For one agent, replace `--agent codex claude-code` with `--agent codex` or `--agent claude-code`. For an intended global installation across projects, choose this alternative command after the same prerequisites and kit setup; do not run both scope examples unless you want both copies:

```powershell
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa --agent codex claude-code -g --copy
```

Global destinations are shown by the CLI; the project-relative `Test-Path` checks above do not verify global copies. Remote URLs install published files, so local unpushed changes are not included. PowerShell execution-policy errors can use `npx.cmd` instead of `npx`; see [troubleshooting](../../../../docs/NPX_INSTALLATION.md#troubleshooting) for missing tools, names, network access and refresh issues.

### Optional recorded or offline installation with Python

Keep this route when you want manifest verification, retained backups and Markdown operation history. It requires Python 3.11+ and a **complete local collection** first. Follow [download/extract or clone steps](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use), then identify the root containing `tools/`, `packs/`, and `README.md`. `tools/install_skills.py` is a file in that root, not a global command.

PowerShell: replace `D:\Tools\dev-workflow-packs` with that actual collection root and `D:\My App` with the existing destination application. For a ZIP, the extracted root may instead end in `dev-workflow-packs-main`.

```powershell
Set-Location 'D:\Tools\dev-workflow-packs'
python --version
python tools/install_skills.py --pack ultimate-qa --agent both --project "D:\My App" --skills ultimate-qa --dry-run
python tools/install_skills.py --pack ultimate-qa --agent both --project "D:\My App" --skills ultimate-qa
```

The first installer command previews and writes nothing. The second requests the existing confirmation and performs the copy with operation records. Run them separately. Python uses `--agent both`; npx uses `--agent codex claude-code`. For Python-only Codex or Claude choose `--agent codex` or `--agent claude`. Core/client copies receive a persistent kit pointer to this local collection; keep that kit on disk. User-scope options are in the [installation guide](../../../../INSTALL.md#choose-a-pack-agent-and-scope).

Use the installer that owns an existing copy for updates/removal; npx and Python maintain different records and protections. Preserve local edits before replacement. See the [pack guide](../../README.md), [npx lifecycle](../../../../docs/NPX_INSTALLATION.md#updates-and-removal), and [recorded removal guide](../../../../UNINSTALL.md).

## Update an installed copy

For an existing **npx-managed project copy**, have Node.js 22.20+ with npm/npx, network access to npm and the recorded source, and Git for repository fallback. Save local edits first. PowerShell: replace `D:\My App` with the application where this skill is installed, then start there:

```powershell
Set-Location 'D:\My App'
```

Update only `ultimate-qa` in that project:

```powershell
npx skills@1.7.4 update ultimate-qa --project
```

For an existing **npx-managed global copy**, choose this alternative from any PowerShell folder. The project command cannot find a global copy:

```powershell
npx skills@1.7.4 update ultimate-qa --global
```

To retain copied Codex and Claude Code destinations, first obtain a new complete QA snapshot and set `ULTIMATE_QA_KIT` to that snapshot's durable `packs/ultimate-qa` folder as shown in Install. Then choose this selected global reinstall from any PowerShell folder instead of `update`; it refreshes the skill from the same snapshot as its kit:

```powershell
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa --agent codex claude-code -g --copy
```

Check the CLI summary and installed destination. For `update`, look for updated, current, skipped or failed status; a skipped update is not success. Verify the intended installed file at the reported destination (for Codex project copies):

```powershell
Test-Path '.agents/skills/ultimate-qa/SKILL.md'
```

For a Codex global copy, verify from any PowerShell folder:

```powershell
Test-Path (Join-Path $env:USERPROFILE '.agents/skills/ultimate-qa/SKILL.md')
```

For Claude Code, check `.claude/skills/ultimate-qa/SKILL.md` in the project or beneath `$env:USERPROFILE` for a global copy. Refresh the agent session before invoking the skill in chat. The updater does not forward explicit `--agent` or `--copy`. For copied global destinations use the selected `add` command above; for a project copy, repeat the matching `add` command in Install with its original source and scope. Python-managed copies use the [recorded replacement workflow](../../../../INSTALL.md#existing-copies-and-replacement), not this npx command. See [global scope, source and removal details](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).

These core/client skills also need a matching durable QA kit. Obtain a new complete snapshot, set `ULTIMATE_QA_KIT` to its actual `packs/ultimate-qa` directory, and rerun the selected `add` command in the Install section, pointing it to that same new snapshot. Keep the previous kit until the new skill copy and helper access are verified. [QA kit update steps](../../../../docs/NPX_INSTALLATION.md#update-npx-managed-skills).

## Use

Refresh the agent session, open the target application repository, and invoke this in agent chat:

```text
$ultimate-qa run
```

In Claude Code use `/ultimate-qa`. These are agent chat instructions, not terminal commands. Use `status` to inspect progress; add `--client` only when client deliverables are wanted and the client skill is installed.

## Commands, continuation and expected output

Enter these in the same target application's agent chat:

| Request | Behavior and stopping point |
|---|---|
| `$ultimate-qa run` | Initialize or reconcile the active review, audit relevant areas, and produce the improvement plan in one workflow. Stop before implementation. |
| `$ultimate-qa run --client` | Complete that review, then prepare optional client deliverables when the client skill and document tools are available. Stop before implementing or sending them. |
| `$ultimate-qa initialize` | Complete intake, preflight and versioned state/template preparation. Use when setup alone is wanted. |
| `$ultimate-qa audit request creation and approval` | Audit the named scope in an initialized review; save findings and executed evidence. Replace the example scope. |
| `$ultimate-qa plan` | Build the improvement plan from current findings/gaps and existing plans. No automatic client files or implementation. |
| `$ultimate-qa status` | Read current version state, findings and next action without file changes. |
| `$ultimate-qa next-version` | Reconcile unresolved work against current evidence, preserve earlier versions, create the next version and audit for new issues. |

There is no `--auto` switch: `run` is the supported continuous intake/audit/plan request. It asks only unanswered intake questions and resumes after the reply. If setup or checks are blocked, provide the missing input/service and repeat the original invocation, retaining `--client` if supplied. `status` identifies the recorded next action; repeating a still-applicable completed `run` does not create another version. Use `next-version` explicitly for that transition.

Expected output lives under the verified application's `qa-findings/` root: version state, requirements, audit/gap reports, improvement plan, and evidence with commands/results. Optional client files appear only when requested. A missing state directs standalone `audit` or `plan` back to initialization. Bare invocation is not documented as a complete run; use `run` explicitly. `--client` does not convert the plan into implementation approval.

## Prerequisites and limits

Requires the complete QA kit, Python 3.11+, Git and an existing application repository. Use the application's own runtime, test accounts and safe environment. Docker-dependent checks remain blocked when Docker is unavailable. Client documents require the optional client skill.

The workflow stops at recommendations. Code implementation, destructive tests, deployment and sending documents need separate authorization.

Read the full [agent instructions](SKILL.md), [recorded installation guide](../../../../INSTALL.md), and [npx update/removal guide](../../../../docs/NPX_INSTALLATION.md#updates-and-removal). Use the installer that owns the copy for updates and removal. [Contribute](../../../../CONTRIBUTING.md).

## Generated artifact storage

When this workflow saves reports or run evidence, use its target-workspace output owner and a new UTC `YYYYMMDDTHHMMSSZ-<unique-id>/` run directory; preserve earlier runs. Before saving in Git, the skill preserves or creates the root `.gitignore`, adds only the required scoped output rule, and verifies exclusion. Tracked output is refused without automatic untracking. Non-Git exclusion remains unverified, and workflows requiring Git retain that prerequisite. Unsafe storage or failed exclusion is reported before persistence. Existing state/resume paths and deliberately tracked project documents remain compatible. See the installed [artifact instructions](SKILL.md#generated-artifacts); chat-only requests create no extra output.
