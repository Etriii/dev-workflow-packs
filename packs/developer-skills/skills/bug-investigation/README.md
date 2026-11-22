# Bug Investigation

Investigate reported bugs by role or page. Detailed mode adds causes, source locations, fixes and verification. The skill can fix application code only with --fix; its helper never writes application code.

Skill responses and generated reports are in English, including for Tagalog or Bisaya requests. Original quotations, code, identifiers, and application content keep their source language when needed for accuracy.

## Install

### Direct project install with npx

Installer prerequisites: Node.js 22.20+ with npm/npx, network access to npm and the published source, and Git for repository fallback. Runtime prerequisites: Python 3.11+, Git, and readable target repositories. No extra Python packages are needed. On Windows use PowerShell. The direct installer obtains the published skill; no manual clone is required.

PowerShell, from any folder, check prerequisites:

```powershell
node --version
```

```powershell
npm --version
```

```powershell
npx --version
```

```powershell
git --version
```

Replace `D:\My App` with the application folder. Start there, then install only `bug-investigation` for both agents in that project:

```powershell
Set-Location 'D:\My App'
```

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill bug-investigation --agent codex claude-code --copy
```

`--agent codex claude-code` selects both agents; use only one name to select one. `--copy` keeps project copies. Review the CLI destination summary and any install prompt. Verify the selected copies in the application folder:

```powershell
Test-Path '.agents/skills/bug-investigation/SKILL.md'
```

```powershell
Test-Path '.claude/skills/bug-investigation/SKILL.md'
```

Refresh each agent session after installation. Then invoke `$bug-investigation` in Codex chat or `/bug-investigation` in Claude Code chat. These are **agent-chat requests**, not terminal commands. Installation does not generate a report or install an automatic completion hook.

Choose this alternative for a global copied installation from any PowerShell folder; `-g` changes scope:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill bug-investigation --agent codex claude-code -g --copy
```

Verify global copies at the destinations shown by the CLI, normally beneath the user profile's `.agents/skills/bug-investigation/` and `.claude/skills/bug-investigation/`, then refresh agent sessions. Remote commands use **published** files. Until `bug-investigation` is published at that source, use a local source checkout or the optional Python installer; a local unpushed edit is not fetched remotely. For a local npx source, replace the URL with the complete local collection path and retain the intended scope and agent flags. See [npx source and troubleshooting](../../../../docs/NPX_INSTALLATION.md#troubleshooting).

### Optional recorded or offline install with Python

Python installation needs Python 3.11+ and a complete checkout or ZIP containing `tools/`, `packs/` and `README.md`. [Download and extract or clone it](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use), then find that collection root. `tools/install_skills.py` is a local file, not a global command. PowerShell: replace `D:\Tools\dev-workflow-packs` with that root and `D:\My App` with the target application. Start in the collection root:

```powershell
Set-Location 'D:\Tools\dev-workflow-packs'
```

Preview only:

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills bug-investigation --dry-run
```

Install after the installer's confirmation:

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills bug-investigation
```

Python uses `--agent both`; npx uses `--agent codex claude-code`. The Python installer records ownership, backups and Markdown operation history. Use the installer that owns an existing copy for later update/removal. An npx install does not migrate Python-managed copies. See [scope and replacement alternatives](../../../../INSTALL.md#existing-copies-and-replacement) and [removal](../../../../UNINSTALL.md).

## Update an installed copy

Save edits to an installed copy first. For an **npx-managed project copy**, use PowerShell in the application folder. Node.js 22.20+, npm/npx, network and the recorded source are required; Git supports repository fallback:

```powershell
Set-Location 'D:\My App'
```

```powershell
npx skills@1.7.4 update bug-investigation --project
```

For an **npx-managed global copy**, use this alternative from any PowerShell folder:

```powershell
npx skills@1.7.4 update bug-investigation --global
```

To retain copied global agent destinations, choose the global `add ... -g --copy` alternative in [Install](#install) using the **original source/ref**. If the existing copy came from a pinned or local source, substitute that same source/ref. Inspect CLI status for updated/current/skipped/failed; skipped is not success. Verify the actual destination's `SKILL.md`, then refresh the agent session. `update` does not forward explicit `--agent` or `--copy`; for a copied project destination, repeat the project `add` command with its original source. Python-managed copies use their [recorded replacement workflow](../../../../INSTALL.md#existing-copies-and-replacement). See [npx updates and removal](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).

## Agent-chat requests

Open the target application or identify it in the conversation. Codex uses `$bug-investigation`; Claude Code uses `/bug-investigation`. These are chat requests, not PowerShell commands. Replace `<problem>`, `<alias>`, and paths with real values. A bare invocation uses an established current problem; otherwise the agent asks for it. `help` only shows examples.

```text
$bug-investigation "<problem>"
$bug-investigation "<problem>" --detailed
$bug-investigation "<problem>" --fix
$bug-investigation "<problem>" --fix --detailed
$bug-investigation "<problem>" --detailed --group role
$bug-investigation "<problem>" --detailed --group page
$bug-investigation "<problem>" --detailed --history
$bug-investigation --verify --detailed
$bug-investigation --project <alias> --detailed
$bug-investigation --detailed --save "docs/bug-investigation.md"
$bug-investigation help
```

Options can appear in sensible order. `--detailed` is the only detailed selector; positional `detailed` is invalid. Unknown options, missing values, conflicting duplicate selectors, and `help` combined with work are invalid. `--group` accepts only `role` or `page`; without it, the agent chooses from inspected navigation and access. `--history` inspects local Git history and includes an Origin section only when supported. It does not assume the last touching commit introduced the defect. Hashes appear only when explicitly requested. `--project <alias>` selects the configured repository group; a problem may also be supplied in that request. The agent inspects selected repositories only.

Default investigation reads source, tests, relevant logs or sanitized examples, and may run safe focused diagnostics. It recommends a correction and does not edit application code. `--fix` first investigates, then authorizes a focused correction, meaningful regression coverage, and relevant checks. It does not authorize staging, committing, pushing, deployment, production data changes, or permission weakening. `--verify` rechecks an identifiable current or supplied investigation without edits. Combine `--verify --fix` only when a failed recheck should be corrected. If there is no identifiable subject, supply the problem or report. Each run ends after its selected investigation, correction, or recheck; follow-ups preserve existing BUG IDs.

By default the report stays in chat. `--save` writes the chosen brief or detailed Markdown to the explicit path. It refuses to silently overwrite an unrelated existing document; resolve that conflict before saving. No report is saved on every run. The selected format, checks, and remaining uncertainty appear in chat even when saving was requested. An optional later `$change-report` or `/change-report` request can present completed changes as a role/page walkthrough; that skill is separate and is never required or invoked automatically.

## Project selection and helper

Runtime prerequisites: Python 3.11+ and Git for the optional bundled helper, plus readable selected repositories. The agent can investigate a single repository without the helper. No external Python packages or `change-report` installation are required. The helper reuses `change-report`'s project registry format and location. If the current folder is a Git repository, its registry lives in Git metadata under `change-report/projects.json`; `CHANGE_REPORT_HOME` can select an existing registry directory. For a parent folder without Git, use `--config` with an explicit JSON registry path. Its schema is `{"schema_version":1,"projects":{"alias":{"name":"path"}}}`. Relative member paths resolve from the registry file's folder; absolute paths cover external repositories. Project setup changes only that registry. The configured alias is selected in agent chat with `--project`; it is not a new application configuration system.

The following are **terminal helper commands**, not chat options. PowerShell, from the target workspace; replace `D:\Tools\dev-workflow-packs` with a complete local collection root and replace aliases and paths. This example uses a parent folder without Git, so it explicitly selects `D:\My App\projects.json`. For a Git-root workspace, omit `--config` to use its Git-metadata registry. After npx installation, use the installed copy's `scripts/bug_investigation.py` instead. Tell the agent the explicit registry path when using `--project` from a non-Git parent, or set `CHANGE_REPORT_HOME` to its directory.

```powershell
Set-Location 'D:\My App'
```

```powershell
python 'D:\Tools\dev-workflow-packs\packs\developer-skills\skills\bug-investigation\scripts\bug_investigation.py' project set --config 'D:\My App\projects.json' --project storefront api=api web=web worker='E:\Related Worker'
```

```powershell
python 'D:\Tools\dev-workflow-packs\packs\developer-skills\skills\bug-investigation\scripts\bug_investigation.py' project list --config 'D:\My App\projects.json'
```

```powershell
python 'D:\Tools\dev-workflow-packs\packs\developer-skills\skills\bug-investigation\scripts\bug_investigation.py' repos --config 'D:\My App\projects.json' --project storefront --require-complete
```

`project set` rejects duplicate aliases and member names. `repos` reports each selected Git root and missing member; without `--require-complete`, missing members produce partial read-only coverage. Use `--require-complete` before a cross-repository fix. A repository's branch and history remain independent. `diff --repo 'D:\My App\api'` can supply HEAD-to-worktree status and old/new line ranges, including untracked files; it cannot attribute a change to this task or prove its purpose. The agent reads final code and tests before reporting. No helper command changes branches, fetches, pulls, merges, or searches the whole machine.

## Report contract

Additional terminal helper operations: `parse -- '<problem>' --fix --detailed` validates option syntax after removing the agent-chat skill name. `validate --file 'docs/bug-investigation.md' --detailed` checks a saved detailed Markdown report's structure. Add `--allow-hashes` only when hashes were explicitly requested. The validator reads the file without editing it; it cannot prove causes, permissions, source attribution, test results or counts. `diff` omits obvious sensitive/generated paths and reports their count. Relative project member inputs stay relative to the registry; explicit absolute external paths stay absolute.

Brief output gives categorized issue bullets and material verification limits, without source tables or routine metadata. Detailed output uses applicable sections in this order: Reported problem, Findings, Confirmed cause (or Cause not yet confirmed), Corrections when an earlier diagnosis was wrong, Expected behavior and fixes (or proposed fixes), Implementation locations, Data and access, Verification, Remaining checks. Origin appears with `--history`; Recommendations appear only when supported. Empty sections are omitted. Grouping is by actual role or page; non-page work uses a relevant category. For unrelated projects use separate sections. Shared causes are explained once and referenced by BUG IDs.

Actual changes use `File | Lines | Status | Type | Change`; inspection-only locations use `File | Lines | Finding or proposed change`. Paths are relative to each repository, with repository labels above tables when needed. Added or modified code uses target lines; removed code uses old lines. Do not infer status or test success from a file's presence. Checks run now, earlier reported checks, browser proof, and deployed proof remain separate. See [the full report rules](references/report-format.md) and the [brief](assets/brief.md) and [detailed](assets/detailed.md) templates.
