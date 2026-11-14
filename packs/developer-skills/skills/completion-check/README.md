# Completion Check

Check acceptance criteria against executed evidence, configuration and integration state.

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
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill completion-check --agent codex claude-code --copy
```

This selects only `completion-check` for Codex and Claude Code in the current project. Review the selected source, agents, scope and destinations in the CLI summary. npm may ask to download the pinned CLI; the skill installer may also prompt. These examples do not force noninteractive approval.

Still in the application folder, confirm the project copies:

```powershell
Test-Path '.agents/skills/completion-check/SKILL.md'
Test-Path '.claude/skills/completion-check/SKILL.md'
```

Both should return `True` for the two-agent project install. Refresh the coding-agent session, then use the chat requests in this README. Installation copies instructions; it does not run the skill.

For one agent, replace `--agent codex claude-code` with `--agent codex` or `--agent claude-code`. For an intended global installation across projects, choose this alternative command after the same prerequisites; do not run both scope examples unless you want both copies:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill completion-check --agent codex claude-code -g --copy
```

Global destinations are shown by the CLI; the project-relative `Test-Path` checks above do not verify global copies. Remote URLs install published files, so local unpushed changes are not included. PowerShell execution-policy errors can use `npx.cmd` instead of `npx`; see [troubleshooting](../../../../docs/NPX_INSTALLATION.md#troubleshooting) for missing tools, names, network access and refresh issues.

### Optional recorded or offline installation with Python

Keep this route when you want manifest verification, retained backups and Markdown operation history. It requires Python 3.11+ and a **complete local collection** first. Follow [download/extract or clone steps](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use), then identify the root containing `tools/`, `packs/`, and `README.md`. `tools/install_skills.py` is a file in that root, not a global command.

PowerShell: replace `D:\Tools\dev-workflow-packs` with that actual collection root and `D:\My App` with the existing destination application. For a ZIP, the extracted root may instead end in `dev-workflow-packs-main`.

```powershell
Set-Location 'D:\Tools\dev-workflow-packs'
python --version
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills completion-check --dry-run
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills completion-check
```

The first installer command previews and writes nothing. The second requests the existing confirmation and performs the copy with operation records. Run them separately. Python uses `--agent both`; npx uses `--agent codex claude-code`. For Python-only Codex or Claude choose `--agent codex` or `--agent claude`. User-scope options are in the [installation guide](../../../../INSTALL.md#choose-a-pack-agent-and-scope).

Use the installer that owns an existing copy for updates/removal; npx and Python maintain different records and protections. Preserve local edits before replacement. See the [pack guide](../../README.md), [npx lifecycle](../../../../docs/NPX_INSTALLATION.md#updates-and-removal), and [recorded removal guide](../../../../UNINSTALL.md).

## Update an installed copy

For an existing **npx-managed project copy**, have Node.js 22.20+ with npm/npx, network access to npm and the recorded source, and Git for repository fallback. Save local edits first. PowerShell: replace `D:\My App` with the application where this skill is installed, then start there:

```powershell
Set-Location 'D:\My App'
```

Update only `completion-check` in that project:

```powershell
npx skills@1.7.4 update completion-check --project
```

For an existing **npx-managed global copy**, choose this alternative from any PowerShell folder. The project command cannot find a global copy:

```powershell
npx skills@1.7.4 update completion-check --global
```

To retain copied Codex and Claude Code destinations, choose this selected global reinstall from any PowerShell folder instead of `update`. It uses the published repository's default branch; if the existing copy came from a local or pinned source, use that original source/ref instead:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill completion-check --agent codex claude-code -g --copy
```

Check the CLI summary and installed destination. For `update`, look for updated, current, skipped or failed status; a skipped update is not success. Verify the intended installed file at the reported destination (for Codex project copies):

```powershell
Test-Path '.agents/skills/completion-check/SKILL.md'
```

For a Codex global copy, verify from any PowerShell folder:

```powershell
Test-Path (Join-Path $env:USERPROFILE '.agents/skills/completion-check/SKILL.md')
```

For Claude Code, check `.claude/skills/completion-check/SKILL.md` in the project or beneath `$env:USERPROFILE` for a global copy. Refresh the agent session before invoking the skill in chat. The updater does not forward explicit `--agent` or `--copy`. For copied global destinations use the selected `add` command above; for a project copy, repeat the matching `add` command in Install with its original source and scope. Python-managed copies use the [recorded replacement workflow](../../../../INSTALL.md#existing-copies-and-replacement), not this npx command. See [global scope, source and removal details](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).


## Use

Refresh the agent session, open the target application, and invoke this in agent chat:

```text
$completion-check Verify phase 2 against docs/plan.md and the current revision. Report pass, fail, blocked and unavailable evidence.
```

In Claude Code use `/completion-check`. These are agent chat instructions, not terminal commands.

## Expected result and stopping point

Expect a criterion-by-criterion pass, fail, unavailable or blocked result with executed checks and remaining proof. It verifies existing work; application fixes, merging and deployment are outside this request.

Supply the selected task or subject and relevant paths in the request or conversation. This skill uses natural-language scope rather than a fixed set of subcommands; do not add another skill's `run`, `build` or `--auto` syntax.

## Prerequisites and limits

Provide acceptance criteria, revision and prior evidence. Verification does not authorize product edits, merges or deployment.

The skill itself needs no private runner, API key or third-party runtime package. It uses the target repository's existing tools where the requested checks require them. Installing instructions does not execute them or prove model adherence.

Read the complete [agent instructions](SKILL.md), [installation options](../../../../INSTALL.md), and [npx update/removal guide](../../../../docs/NPX_INSTALLATION.md#updates-and-removal). Use the installer that owns the copy for updates and removal. [Contribute](../../../../CONTRIBUTING.md).

## Generated artifact storage

When this workflow saves reports or run evidence, use its target-workspace output owner and a new UTC `YYYYMMDDTHHMMSSZ-<unique-id>/` run directory; preserve earlier runs. Before saving in Git, the skill preserves or creates the root `.gitignore`, adds only the required scoped output rule, and verifies exclusion. Tracked output is refused without automatic untracking. Non-Git exclusion remains unverified, and workflows requiring Git retain that prerequisite. Unsafe storage or failed exclusion is reported before persistence. Existing state/resume paths and deliberately tracked project documents remain compatible. See the installed [artifact instructions](SKILL.md#generated-artifacts); chat-only requests create no extra output.
