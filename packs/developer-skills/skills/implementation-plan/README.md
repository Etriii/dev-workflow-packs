# Implementation Plan

Start from an existing Codex or Claude Markdown plan, a PDF requirements brief with no plan yet, or a task described in chat. The skill asks planning questions, recommends compact and balanced phase counts, and lets you implement, save a complete phase package, or save it and begin the first phase. A saved package contains shared specifications, separate one-phase prompts, acceptance checks, progress and handoff.

## Start in agent chat

After installing the skill, refresh the agent session and open the target project. Codex uses `$implementation-plan`; Claude Code uses `/implementation-plan`. These are chat requests, not terminal commands. Replace `<plan-file.md>` with the path to your UTF-8 Markdown plan. The path follows the skill name directly; quote paths with spaces.

```text
$implementation-plan "<plan-file.md>" --skills caveman,ultimate-ui-ux
```

In Claude Code, replace `$implementation-plan` with `/implementation-plan`. To start without a file, use `$implementation-plan create "<task-description>"` or invoke it bare and provide the task when asked. A plain non-path task remains a `create` shortcut. A missing path-like argument is reported as a missing file. Use `--project "<project-path>"` if the target project is not the open one; the plan file may be outside that project.

If you have instructions or requirements in a PDF but no plan yet, give its path and the existing application project. Replace `<requirements-file.pdf>` and `<project-path>` with real paths:

```text
$implementation-plan "<requirements-file.pdf>" --project "<project-path>"
```

The skill reads the PDF as source requirements, checks unclear or conflicting details, asks questions, and forms a working plan from the answers. If the PDF already contains a plan, it can use that plan instead. It will not treat a requirements brief as an approved implementation plan.

You may put options before the plan path if that reads more naturally. This is an alternative chat request:

```text
$implementation-plan --skills migration,verify-and-stop --max-phases 4 --test-scope full "<plan-file.md>"
```

The named skills must be installed and relevant; the skill reads their instructions before assigning or using them.

The skill inspects the plan and current source before asking. It **always** asks you to choose phase sizing:

| Choice | Meaning |
|---|---|
| **Compact** | Use the recommended exact count with fewer coherent phases. |
| **Balanced** | Use the recommended exact count with more room for implementation and verification. |
| **Custom maximum** | Supply a positive hard cap, such as 4; the skill proposes and confirms an exact count of at most 4. |

The recommendations include the work and checks that fit each count. A one-phase option appears when the work can reasonably finish in one session. `--max-phases N` pre-fills Custom maximum but does not skip the question. If the cap cannot fit the work, the skill asks you to increase it or narrow the scope. It also **always** asks you to select one action:

| Choice | Effect | Recommended default |
|---|---|---|
| **Implement now** | Implement the selected ready scope and run its checks. No package is created. | When all work and proof fit one session. |
| **Prepare phase package** | Write and check the ignored package without implementing. | When work spans sessions. |
| **Prepare package, then implement** | Write and check the package, then implement only its first ready phase. | Select when you want both durable files and an immediate start. |

Other questions concern only decisions the plan and source cannot settle, such as scope, business rules, acceptance, permissions, or selected skills. Missing answers stop dependent work. A multi-phase implementation stops after its first authorized phase. None of the choices authorizes a push, deployment or production data change.

You can combine this skill with Codex or Claude's built-in Plan mode: finish its questions and use the agreed plan as this skill's input, either in the same conversation or as a saved file. This skill's three choices are its own question; it does not change the host's built-in menu. While the host remains in read-only Plan mode, the skill can ask and plan but waits for execution mode before saving files or implementing.

Every saved package has `ORIGINAL_PLAN.md`, `README.md`, `PLAN.md`, `CONTRACTS.md`, `PHASES.md`, `PROMPTS.md`, `RUNBOOK.md`, `ACCEPTANCE.md`, `PROGRESS.md`, `HANDOFF.md`, `BLOCKERS.md`, `COMMIT_MESSAGES.md`, and a separate file under `prompts/` for each phase. A supplied Markdown plan is copied byte for byte into `ORIGINAL_PLAN.md`; answers go in `PLAN.md`. For PDF input, the original PDF is copied byte for byte into `SOURCE_DOCUMENT.pdf` and the agreed working plan goes into `ORIGINAL_PLAN.md`. Without a file, the agreed session plan becomes `ORIGINAL_PLAN.md`. Initially, unexecuted checks remain `NOT_RUN`.

`COMMIT_MESSAGES.md` must contain detailed, copyable messages for the planned work, split by repository and distinct feature. Each message has a Conventional Commit subject and a substantive body explaining the intended behavior, why it matters, planned changes, and relevant verification or migration notes. At planning time, label unrun checks `NOT_RUN` and avoid invented file paths or hashes. When implementation happens, update messages from the actual diff and checks. A list of one-line subjects is incomplete. This requirement applies with every commit policy, including the default with commits off. Terse chat styles do not shorten persisted commit messages.

## Commands and options

The examples below are independent chat requests. Use the exact path returned by `create` or `revise` in place of `<package>`.

```text
$implementation-plan create "<task-description>" --project "<project-path>" --max-phases 5 --skills caveman,ultimate-ui-ux --skills-mode auto
$implementation-plan create "<task-description>" --project "<project-path>" --auto-commit
$implementation-plan "<plan-file.md>" --commits scoped --test-scope full
$implementation-plan revise <package> "<change-description>" --max-phases 6
$implementation-plan revise <package> "<change-description>" --commits off
$implementation-plan skills <package>
$implementation-plan skills <package> --add migration,verify-and-stop --skills-mode auto
$implementation-plan skills <package> --remove ultimate-ui-ux --skills-mode all
$implementation-plan prompt <package> P01
$implementation-plan check <package>
$implementation-plan status <package>
$implementation-plan status
$implementation-plan help
```

`revise` and changing `skills` requests save a new revision, preserve earlier files and valid evidence, and report the new path. Omitted options inherit prior values. `skills` without changes, `prompt`, `check`, `status`, and `help` are read-only. Unknown phase IDs and invalid option combinations are errors. Adding and removing the same skill in one request is invalid. `status` without a path lists recognized packages in the current project; it does not select one for editing.

`--max-phases N` proposes the Custom maximum hard cap. The skill confirms it and the resulting exact phase count before acting. The package store records both values and rejects a count above the cap. `--skills name1,name2` selects skills. The default `--skills-mode auto` reads their instructions and assigns them to relevant phases. `--skills-mode all` places all selected skills in every prompt; conflicts and missing skills are reported rather than silently resolved. The skill does not install selected skills. `--commits off` is the default: prompts may draft messages but do not authorize commits. `--commits scoped` permits owned local commits after selected implementation and required checks pass, subject to repository rules. `--auto-commit` requires a local commit of only verified, owned implementation changes without another commit question, after the selected implementation passes its required checks. The actual commit must have a Conventional Commit subject, a blank line and a substantive body explaining what changed, why, and which checks actually ran; subject-only messages fail this requirement. It records `auto` in the package and carries into later invoked phase prompts; package creation or revision alone never commits. The agent inspects the Git diff, stages only owned paths, and verifies the committed message, changed paths and remaining status. Failed checks, missing prerequisites or no owned changes mean no commit; the agent reports the reason. To turn auto-commit off in a package revision, use `--commits off`. Do not combine `--auto-commit` with `--commits`, even `scoped`. No policy authorizes a push, deployment or another phase.

`--test-scope focused` is the default. It runs relevant tests for the changed behavior and affected integrations. `--test-scope full` also requires the complete configured suite for each component changed in the selected implementation phase. If you specifically need the entire backend suite, say so in the request; the package records that named suite in its runbook and prompts. The agent finds the project's actual test command and reports any missing prerequisite or unsuccessful run. Preparing a package records the requirement without running application tests. Read-only package commands run none. A full suite is never reported as passed when it was skipped or interrupted.

Package choices save under `<project-root>/.implementation-plans/<feature>-implementation/<UTC-run-id>/`. Each revision has a unique run directory. The skill adds `/.implementation-plans/` to the root `.gitignore` when needed and verifies exclusion before saving. It leaves existing `docs/` content untouched. Earlier packages under `docs/` remain readable; revisions of them use the new root and link back to the old path without moving it. Tracked output is refused without automatic untracking. In a non-Git project exclusion is unverified. Resume an identified draft revision after interruption; never overwrite or discard an earlier one. A failed storage check stops saving and reports the exact reason.

`check` confirms the package structure and rejects subject-only commit lists or commit blocks without bodies. The author must still review whether each body covers its repository and logical feature in useful detail, along with requirement coverage, dependencies, links, prompt scope and evidence claims. A passing check does not prove implementation, native agent adherence or runtime behavior. With Prepare phase package, invoke the exact stored prompt from `prompt <package> P01` in a later request when work on that phase is intended; it stops at that phase.

## Install

### Direct npx installation

Prerequisites: Node.js 22.20+ with npm/npx, network access for npm/GitHub, and Git for repository fallback. These are installer requirements. At runtime, this skill's bundled helper needs Python 3.11+ and Git for exclusion verification inside a Git project; the target application has its own requirements. PDF input also needs a PDF reader available to the agent for content inspection. The helper only validates and copies PDF bytes; it does not extract text or perform OCR. If the document cannot be read reliably, provide an accessible text copy before planning.

PowerShell, starting in the target application folder; replace `<project-path>` with your existing project path. Run the lines separately:

```powershell
Set-Location '<project-path>'
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill implementation-plan --agent codex claude-code --copy
```

This is project scope for Codex and Claude Code. For one agent, use `--agent codex` or `--agent claude-code`. Review the CLI's destination summary; expected copies include `.agents/skills/implementation-plan/SKILL.md`, its `scripts/` and `references/`, and the corresponding Claude skill location when selected. Refresh the agent session, then invoke the skill separately in chat. The remote command reads published files; local changes are available only from a local source until they are pushed. For a complete local checkout, replace `<collection-root>` with its path as the npx source:

```powershell
npx skills@1.7.4 add '<collection-root>' --skill implementation-plan --agent codex claude-code --copy
```

This local-source command also starts from the target application folder. It installs the current local checkout, not a remote snapshot. A missing remote skill name means it has not been published there; do not silently switch sources. See the [npx guide](../../../../docs/NPX_INSTALLATION.md) for updates and removal. Use the installer that owns an existing copy.

### Optional recorded/offline Python installation

First obtain the complete collection by the [ZIP or Git instructions](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use). Find its inner root containing `tools/` and `packs/`; `tools/install_skills.py` is a local script there, not a global command. Python 3.11+ is required. PowerShell, starting in that collection root, preview and install in separate commands; replace `<project-path>` with the target project:

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project '<project-path>' --skills implementation-plan --dry-run
```

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project '<project-path>' --skills implementation-plan
```

The preview changes nothing. The second command writes recorded project copies and retains installer ownership, backups and Markdown history. `--agent both` is specific to the Python installer; npx uses `--agent codex claude-code`. A prior Python-managed copy must be updated or removed through the Python installer, not implicitly migrated by npx. Installation itself creates no implementation package.

Read the [agent instructions](SKILL.md), [pack catalog](../../SKILL_CATALOG.md) and [collection installation guide](../../../../INSTALL.md).

## Update an installed copy

For an existing **npx-managed project copy**, have Node.js 22.20+ with npm/npx, network access to npm and the recorded source, and Git for repository fallback. Save local edits first. PowerShell: replace `D:\My App` with the application where this skill is installed, then start there:

```powershell
Set-Location 'D:\My App'
```

Update only `implementation-plan` in that project:

```powershell
npx skills@1.7.4 update implementation-plan --project
```

For an existing **npx-managed global copy**, choose this alternative from any PowerShell folder. The project command cannot find a global copy:

```powershell
npx skills@1.7.4 update implementation-plan --global
```

To retain copied Codex and Claude Code destinations, choose this selected global reinstall from any PowerShell folder instead of `update`. It uses the published repository's default branch; if the existing copy came from a local or pinned source, use that original source/ref instead:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill implementation-plan --agent codex claude-code -g --copy
```

Check the CLI summary and installed destination. For `update`, look for updated, current, skipped or failed status; a skipped update is not success. Verify the intended installed file at the reported destination (for Codex project copies):

```powershell
Test-Path '.agents/skills/implementation-plan/SKILL.md'
```

For a Codex global copy, verify from any PowerShell folder:

```powershell
Test-Path (Join-Path $env:USERPROFILE '.agents/skills/implementation-plan/SKILL.md')
```

For Claude Code, check `.claude/skills/implementation-plan/SKILL.md` in the project or beneath `$env:USERPROFILE` for a global copy. Refresh the agent session before invoking the skill in chat. The updater does not forward explicit `--agent` or `--copy`. For copied global destinations use the selected `add` command above; for a project copy, repeat the matching `add` command in Install with its original source and scope. Python-managed copies use the [recorded replacement workflow](../../../../INSTALL.md#existing-copies-and-replacement), not this npx command. See [global scope, source and removal details](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).
