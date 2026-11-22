# Ultimate QA Client

Prepare optional client reports and approval checklists, preserving returned decisions.

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
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa-client --agent codex claude-code --copy
```

The selected skill and support files now come from the same downloaded source. Keep the kit folder available. To reuse that existing kit instead of downloading again, use:

```powershell
$env:ULTIMATE_QA_KIT = 'D:\Tools\dev-workflow-packs-qa\dev-workflow-packs-main\packs\ultimate-qa'
Set-Location 'D:\My App'
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa-client --agent codex claude-code --copy
```

Set the kit path again in a new terminal and start the coding agent from this terminal in the application, or provide the absolute kit path to an already-running agent. The environment assignment applies to this process and its children; it does not reconfigure an agent already running elsewhere. The kit is not the application to review. See the [full QA setup](../../../../docs/NPX_INSTALLATION.md#ultimate-qa-support-files) for the complete pack and helper verification.

This selects only `ultimate-qa-client` for Codex and Claude Code in the current project. Review the selected source, agents, scope and destinations in the CLI summary. npm may ask to download the pinned CLI; the skill installer may also prompt. These examples do not force noninteractive approval.

Still in the application folder, confirm the project copies:

```powershell
Test-Path '.agents/skills/ultimate-qa-client/SKILL.md'
Test-Path '.claude/skills/ultimate-qa-client/SKILL.md'
```

Both should return `True` for the two-agent project install. Refresh the coding-agent session, then use the chat requests in this README. Installation copies instructions; it does not run the skill.

For one agent, replace `--agent codex claude-code` with `--agent codex` or `--agent claude-code`. For an intended global installation across projects, choose this alternative command after the same prerequisites and kit setup; do not run both scope examples unless you want both copies:

```powershell
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa-client --agent codex claude-code -g --copy
```

Global destinations are shown by the CLI; the project-relative `Test-Path` checks above do not verify global copies. Remote URLs install published files, so local unpushed changes are not included. PowerShell execution-policy errors can use `npx.cmd` instead of `npx`; see [troubleshooting](../../../../docs/NPX_INSTALLATION.md#troubleshooting) for missing tools, names, network access and refresh issues.

### Optional recorded or offline installation with Python

Keep this route when you want manifest verification, retained backups and Markdown operation history. It requires Python 3.11+ and a **complete local collection** first. Follow [download/extract or clone steps](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use), then identify the root containing `tools/`, `packs/`, and `README.md`. `tools/install_skills.py` is a file in that root, not a global command.

PowerShell: replace `D:\Tools\dev-workflow-packs` with that actual collection root and `D:\My App` with the existing destination application. For a ZIP, the extracted root may instead end in `dev-workflow-packs-main`.

```powershell
Set-Location 'D:\Tools\dev-workflow-packs'
python --version
python tools/install_skills.py --pack ultimate-qa --agent both --project "D:\My App" --skills ultimate-qa-client --dry-run
python tools/install_skills.py --pack ultimate-qa --agent both --project "D:\My App" --skills ultimate-qa-client
```

The first installer command previews and writes nothing. The second requests the existing confirmation and performs the copy with operation records. Run them separately. Python uses `--agent both`; npx uses `--agent codex claude-code`. For Python-only Codex or Claude choose `--agent codex` or `--agent claude`. Core/client copies receive a persistent kit pointer to this local collection; keep that kit on disk. User-scope options are in the [installation guide](../../../../INSTALL.md#choose-a-pack-agent-and-scope).

Use the installer that owns an existing copy for updates/removal; npx and Python maintain different records and protections. Preserve local edits before replacement. See the [pack guide](../../README.md), [npx lifecycle](../../../../docs/NPX_INSTALLATION.md#updates-and-removal), and [recorded removal guide](../../../../UNINSTALL.md).

## Update an installed copy

For an existing **npx-managed project copy**, have Node.js 22.20+ with npm/npx, network access to npm and the recorded source, and Git for repository fallback. Save local edits first. PowerShell: replace `D:\My App` with the application where this skill is installed, then start there:

```powershell
Set-Location 'D:\My App'
```

Update only `ultimate-qa-client` in that project:

```powershell
npx skills@1.7.4 update ultimate-qa-client --project
```

For an existing **npx-managed global copy**, choose this alternative from any PowerShell folder. The project command cannot find a global copy:

```powershell
npx skills@1.7.4 update ultimate-qa-client --global
```

To retain copied Codex and Claude Code destinations, first obtain a new complete QA snapshot and set `ULTIMATE_QA_KIT` to that snapshot's durable `packs/ultimate-qa` folder as shown in Install. Then choose this selected global reinstall from any PowerShell folder instead of `update`; it refreshes the skill from the same snapshot as its kit:

```powershell
npx skills@1.7.4 add "$env:ULTIMATE_QA_KIT" --skill ultimate-qa-client --agent codex claude-code -g --copy
```

Check the CLI summary and installed destination. For `update`, look for updated, current, skipped or failed status; a skipped update is not success. Verify the intended installed file at the reported destination (for Codex project copies):

```powershell
Test-Path '.agents/skills/ultimate-qa-client/SKILL.md'
```

For a Codex global copy, verify from any PowerShell folder:

```powershell
Test-Path (Join-Path $env:USERPROFILE '.agents/skills/ultimate-qa-client/SKILL.md')
```

For Claude Code, check `.claude/skills/ultimate-qa-client/SKILL.md` in the project or beneath `$env:USERPROFILE` for a global copy. Refresh the agent session before invoking the skill in chat. The updater does not forward explicit `--agent` or `--copy`. For copied global destinations use the selected `add` command above; for a project copy, repeat the matching `add` command in Install with its original source and scope. Python-managed copies use the [recorded replacement workflow](../../../../INSTALL.md#existing-copies-and-replacement), not this npx command. See [global scope, source and removal details](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).

These core/client skills also need a matching durable QA kit. Obtain a new complete snapshot, set `ULTIMATE_QA_KIT` to its actual `packs/ultimate-qa` directory, and rerun the selected `add` command in the Install section, pointing it to that same new snapshot. Keep the previous kit until the new skill copy and helper access are verified. [QA kit update steps](../../../../docs/NPX_INSTALLATION.md#update-npx-managed-skills).

## Use

Refresh the agent session, open the target application repository, and invoke this in agent chat:

```text
$ultimate-qa-client prepare
```

In Claude Code use `/ultimate-qa-client`. These are agent chat instructions, not terminal commands. For the combined review plus client preparation, install the core skill too and invoke `$ultimate-qa run --client`.

## Supported operations and outputs

These are agent-chat requests in the same verified application and QA version:

| Request | Result and boundary |
|---|---|
| `$ultimate-qa-client prepare` | Create plain-language QA Markdown and matching rendered/inspected Word reports and approval checklists from the completed audit and plan. Leave client choices blank. |
| `$ultimate-qa-client intake` | Read the returned form, ask only unanswered intake questions, and record supported requirements/conditions without credentials. |
| `$ultimate-qa-client decisions` | Record returned approvals, rejections, deferrals, reasons and alternatives verbatim; missing choices stay pending. |
| `$ultimate-qa-client report` | After separately authorized implementation, summarize actual changes and evidence for the client. Proposed work is not reported as completed. |
| `$ultimate-qa-client next-version` | Carry unresolved decisions and accepted unfinished work with their original IDs; preserve closed history. |

Provide the actual returned form or decision source when it is not already clear. Client artifacts live under `qa-findings/v<N>/client/`; implementation summaries use its `after_implementation/` subtree. Reruns archive generated files and preserve returned decisions. Missing audit/plan, client skill dependencies, or rendering capability remain explicit blockers. Supplying decisions does not itself change QA finding status without implementation evidence.

Use `prepare` explicitly; there is no documented bare-invocation default or generic `--auto` mode. For the complete review and preparation workflow use `$ultimate-qa run --client`. None of these operations automatically implements recommendations or sends documents.

## Prerequisites and limits

Requires the complete QA kit, a completed audit and improvement plan, Python 3.11+, and the optional `python-docx` package for Word output. Word deliverables also need a compatible renderer and visual inspection.

Use only when client-facing output is requested. Preparing an approval checklist does not approve fixes, start implementation or send documents.

Read the full [agent instructions](SKILL.md), [recorded installation guide](../../../../INSTALL.md), and [npx update/removal guide](../../../../docs/NPX_INSTALLATION.md#updates-and-removal). Use the installer that owns the copy for updates and removal. [Contribute](../../../../CONTRIBUTING.md).

## Generated artifact storage

When this workflow saves reports or run evidence, use its target-workspace output owner and a new UTC `YYYYMMDDTHHMMSSZ-<unique-id>/` run directory; preserve earlier runs. Before saving in Git, the skill preserves or creates the root `.gitignore`, adds only the required scoped output rule, and verifies exclusion. Tracked output is refused without automatic untracking. Non-Git exclusion remains unverified, and workflows requiring Git retain that prerequisite. Unsafe storage or failed exclusion is reported before persistence. Existing state/resume paths and deliberately tracked project documents remain compatible. See the installed [artifact instructions](SKILL.md#generated-artifacts); chat-only requests create no extra output.
