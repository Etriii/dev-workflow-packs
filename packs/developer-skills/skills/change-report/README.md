# Change Report

Explain completed development changes as a brief walkthrough by role or page. Each viewable change includes the verified application-relative URL where it can be seen, such as `/queue-system`. Detailed mode adds source ranges, change purpose, verification and follow-up. The skill reads Git evidence; its Python helper does not write application code or Git state.

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

Replace `D:\My App` with the application folder. Start there, then install only `change-report` for both agents in that project:

```powershell
Set-Location 'D:\My App'
```

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill change-report --agent codex claude-code --copy
```

`--agent codex claude-code` selects both agents; use only one name to select one. `--copy` keeps project copies. Review the CLI destination summary and any install prompt. Verify the selected copies in the application folder:

```powershell
Test-Path '.agents/skills/change-report/SKILL.md'
```

```powershell
Test-Path '.claude/skills/change-report/SKILL.md'
```

Refresh each agent session after installation. Then invoke `$change-report` in Codex chat or `/change-report` in Claude Code chat. These are **agent-chat requests**, not terminal commands. Installation does not generate a report or install an automatic completion hook.

Choose this alternative for a global copied installation from any PowerShell folder; `-g` changes scope:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill change-report --agent codex claude-code -g --copy
```

Verify global copies at the destinations shown by the CLI, normally beneath the user profile's `.agents/skills/change-report/` and `.claude/skills/change-report/`, then refresh agent sessions. Remote commands use **published** files. Until `change-report` is published at that source, use a local source checkout or the optional Python installer; a local unpushed edit is not fetched remotely. For a local npx source, replace the URL with the complete local collection path and retain the intended scope and agent flags. See [npx source and troubleshooting](../../../../docs/NPX_INSTALLATION.md#troubleshooting).

### Optional recorded or offline install with Python

Python installation needs Python 3.11+ and a complete checkout or ZIP containing `tools/`, `packs/` and `README.md`. [Download and extract or clone it](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use), then find that collection root. `tools/install_skills.py` is a local file, not a global command. PowerShell: replace `D:\Tools\dev-workflow-packs` with that root and `D:\My App` with the target application. Start in the collection root:

```powershell
Set-Location 'D:\Tools\dev-workflow-packs'
```

Preview only:

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills change-report --dry-run
```

Install after the installer's confirmation:

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project "D:\My App" --skills change-report
```

Python uses `--agent both`; npx uses `--agent codex claude-code`. The Python installer records ownership, backups and Markdown operation history. Use the installer that owns an existing copy for later update/removal. An npx install does not migrate Python-managed copies. See [scope and replacement alternatives](../../../../INSTALL.md#existing-copies-and-replacement) and [removal](../../../../UNINSTALL.md).

## Update an installed copy

Save edits to an installed copy first. For an **npx-managed project copy**, use PowerShell in the application folder. Node.js 22.20+, npm/npx, network and the recorded source are required; Git supports repository fallback:

```powershell
Set-Location 'D:\My App'
```

```powershell
npx skills@1.7.4 update change-report --project
```

For an **npx-managed global copy**, use this alternative from any PowerShell folder:

```powershell
npx skills@1.7.4 update change-report --global
```

To retain copied global agent destinations, choose the global `add ... -g --copy` alternative in [Install](#install) using the **original source/ref**. If the existing copy came from a pinned or local source, substitute that same source/ref. Inspect CLI status for updated/current/skipped/failed; skipped is not success. Verify the actual destination's `SKILL.md`, then refresh the agent session. `update` does not forward explicit `--agent` or `--copy`; for a copied project destination, repeat the project `add` command with its original source. Python-managed copies use their [recorded replacement workflow](../../../../INSTALL.md#existing-copies-and-replacement). See [npx updates and removal](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).

## Everyday requests

Run these in agent chat from a target repository. For Claude Code, replace `$change-report` with `/change-report`. Each line is a separate example, not a shell command:

```text
$change-report
$change-report detailed
$change-report latest
$change-report working
$change-report session
$change-report start
$change-report --from <revision>
$change-report --from <revision> --to <revision>
$change-report --from <revision> --to working
$change-report detailed --group page
$change-report --project <alias>
$change-report --all
$change-report --plan "<package-path>" --phase P02
$change-report --verify
$change-report --save "<report-path.md>"
$change-report help
```

Replace angle-bracket placeholders with actual revision, configured alias and paths. `--group role` also works. `detailed` and options can be combined in any sensible order, for example `$change-report detailed session --project storefront --group role --verify`. `--save` writes only the selected brief or detailed Markdown format to the specified path, without automatic report files. It does not overwrite an existing file without explicit permission. `--verify` may run relevant focused checks; without it, the skill only reports checks it can substantiate from existing evidence. `help` only explains commands.

Bare invocation uses a matching current task baseline, otherwise current uncommitted changes, otherwise the latest local commit. `working` includes staged, unstaged and relevant untracked files. `latest` uses the first parent of a merge commit and the empty tree for an initial commit. `--from A` compares A with HEAD; `--from A --to B` compares snapshots directly; `--to working` uses the worktree. Invalid revisions, no commits for `latest`, no matched baseline for `session`, and empty diffs are reported explicitly. Branches are never changed or fetched.

### Record a task baseline

Before implementation, request `$change-report start`. The agent gives the helper a specific task/run context and retains its returned token. After work, use `$change-report session`; it must match the token, context and repository set. `start` records hashes of pre-existing index and worktree lines so later reports can separate them from task edits without storing source content. When those states differ, marked rows need review before attribution. State lives under the invoking repository's Git metadata in `change-report/`, or the deliberately set `CHANGE_REPORT_HOME`; it never stashes or changes the index/worktree. A missing or stale baseline cannot be recovered as an accurate session report. Re-run `start` before a new task, and carry its token into any handoff.

### Several repositories

In agent chat, request `Configure change-report project storefront: frontend="D:\Work\Store\frontend" backend="D:\Work\Store\backend" notifications="E:\Services\Notify".` The agent runs `project set --project storefront name=PATH ...` using the bundled helper. `project list` shows configured aliases. Definitions live in the invoking repository's Git metadata. Nearby paths are saved relative to that configuration; external paths stay absolute. The agent validates every selected repository and deduplicates paths to one Git worktree. `--project storefront` reports that project; `--all` reports every project configured in this workspace, in separate project sections. If a member is unavailable, fix its path or configuration and rerun; no partial report is presented as complete.

Independent histories can use `$change-report --project storefront --from main --repo-from frontend=v2 --repo-from backend=release-7`, or `--repo-to NAME=REV` for targets. Names match configured members; with `--all`, prefix each name as `alias/member`. A common revision must resolve in every member without an override. `--all` and `--project` conflict. No recursive machine scan occurs.

### Implementation plan

For `$change-report --plan "<package-path>" --phase P02`, the agent reads `PLAN.md`, `CONTRACTS.md`, `PHASES.md`, `ACCEPTANCE.md`, `PROGRESS.md`, `HANDOFF.md` and the selected `prompts/P02_*.md` where present. A missing package or selected phase is an error. It compares selected acceptance with actual code changes; plan text is not implementation evidence. For accurate completion reporting, add these chat instructions to the phase execution prompt: `$change-report start` before implementation, then `$change-report session --plan "<package-path>" --phase P02` after checks. The agent retains the baseline token/context in the handoff. The installed skill cannot create an automatic completion hook.

## Output and effects

Brief output is a compact role/page walkthrough without hashes, file paths, counts, classifications or routine check logs. For every viewable page or workflow, brief and detailed output include a verified application-relative URL starting with `/`, such as `/queue-system`; required query strings or fragments stay in the URL, and required route parameters are identified when a concrete value is unavailable. The agent checks routes and navigation in the selected source. If it cannot verify a URL, the report says `URL unverified` and why; changes with no application view say no viewable URL applies. Detailed output keeps the walkthrough and adds per-page source tables with relative paths, exact changed lines, file status, change type and concise descriptions. It may add one shared verification/follow-up section. It does not infer permissions from routes, call untested behavior verified, or call a change a Fix without expected-behavior evidence. [Report format](references/report-format.md) has illustrative wording and table rules.

Normal requests read only and stop after the chat report. `start` and project setup write requested Git-local metadata. `--save` writes the requested Markdown path; in-repository generated output needs safe storage and exclusion review. `--verify` may execute focused existing checks and reports Passed, Failed, Not run or Blocked accurately. No application code, index, commit, branch, deployment or remote repository state is changed. If Git, Python, a repository, phase package or saved baseline is missing, fix the prerequisite and repeat the same request. The helper provides Git scope and line evidence; page and role interpretation remains source-reviewed agent work, not a filename classifier.
