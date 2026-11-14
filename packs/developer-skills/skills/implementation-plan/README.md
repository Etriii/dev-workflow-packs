# Implementation Plan

Start from an existing Codex or Claude Markdown plan, a PDF requirements brief with no plan yet, or a task described in chat. The skill asks planning questions, recommends compact and balanced phase counts, and lets you implement, save a complete phase package, or save it and begin the first phase. A saved package contains shared specifications, separate one-phase prompts, acceptance checks, progress and handoff.

## Start in agent chat

After installing the skill, refresh the agent session and open the target project. Codex uses `$implementation-plan`; Claude Code uses `/implementation-plan`. These are chat requests, not terminal commands. Replace the example path with your own UTF-8 Markdown plan file. The path follows the skill name directly; quote paths with spaces.

```text
$implementation-plan "D:\My App\docs\hiring-plan.md" --skills caveman,ultimate-ui-ux
```

In Claude Code, replace `$implementation-plan` with `/implementation-plan`. To start without a file, use `$implementation-plan create "Hiring and workforce management"` or invoke it bare and provide the task when asked. A plain non-path task remains a `create` shortcut. A missing path-like argument is reported as a missing file. Use `--project "D:\My App"` if the target project is not the open one; the plan file may be outside that project.

If you have instructions or requirements in a PDF but no plan yet, give its path and the existing application project. Replace both example paths:

```text
$implementation-plan "D:\Requirements\programmer-instructions.pdf" --project "D:\My App"
```

The skill reads the PDF as source requirements, checks unclear or conflicting details, asks questions, and forms a working plan from the answers. If the PDF already contains a plan, it can use that plan instead. It will not treat a requirements brief as an approved implementation plan.

You may put options before the plan path if that reads more naturally. This is an alternative chat request:

```text
$implementation-plan --skills migration,verify-and-stop --max-phases 4 --test-scope full "D:\My App\docs\hiring-plan.md"
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

## Commands and options

The examples below are independent chat requests. Use the exact path returned by `create` or `revise` in place of `<package>`.

```text
$implementation-plan create "Hiring and workforce management" --project "D:\My App" --max-phases 5 --skills caveman,ultimate-ui-ux --skills-mode auto
$implementation-plan revise <package> "Add a separate migration gate" --max-phases 6
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

`--max-phases N` proposes the Custom maximum hard cap. The skill confirms it and the resulting exact phase count before acting. The package store records both values and rejects a count above the cap. `--skills name1,name2` selects skills. The default `--skills-mode auto` reads their instructions and assigns them to relevant phases. `--skills-mode all` places all selected skills in every prompt; conflicts and missing skills are reported rather than silently resolved. The skill does not install selected skills. `--commits off` is the default: prompts may draft messages but do not authorize commits. `--commits scoped` authorizes only owned local commits after selected implementation and required checks pass, subject to repository rules. It never authorizes a push or deployment.

`--test-scope focused` is the default. It runs relevant tests for the changed behavior and affected integrations. `--test-scope full` also requires the complete configured suite for each component changed in the selected implementation phase. If you specifically need the entire backend suite, say so in the request; the package records that named suite in its runbook and prompts. The agent finds the project's actual test command and reports any missing prerequisite or unsuccessful run. Preparing a package records the requirement without running application tests. Read-only package commands run none. A full suite is never reported as passed when it was skipped or interrupted.

Package choices save under `<project-root>/.implementation-plans/<feature>-implementation/<UTC-run-id>/`. Each revision has a unique run directory. The skill adds `/.implementation-plans/` to the root `.gitignore` when needed and verifies exclusion before saving. It leaves existing `docs/` content untouched. Earlier packages under `docs/` remain readable; revisions of them use the new root and link back to the old path without moving it. Tracked output is refused without automatic untracking. In a non-Git project exclusion is unverified. Resume an identified draft revision after interruption; never overwrite or discard an earlier one. A failed storage check stops saving and reports the exact reason.

`check` confirms the package structure and requires a separate author review of requirement coverage, dependencies, links, prompt scope and evidence claims. A passing check does not prove implementation, native agent adherence or runtime behavior. With Prepare phase package, invoke the exact stored prompt from `prompt <package> P01` in a later request when work on that phase is intended; it stops at that phase.

## Install

### Direct npx installation

Prerequisites: Node.js 22.20+ with npm/npx, network access for npm/GitHub, and Git for repository fallback. These are installer requirements. At runtime, this skill's bundled helper needs Python 3.11+ and Git for exclusion verification inside a Git project; the target application has its own requirements. PDF input also needs a PDF reader available to the agent for content inspection. The helper only validates and copies PDF bytes; it does not extract text or perform OCR. If the document cannot be read reliably, provide an accessible text copy before planning.

PowerShell, starting in the target application folder; replace `D:\My App` with your project path. Run the lines separately:

```powershell
Set-Location 'D:\My App'
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill implementation-plan --agent codex claude-code --copy
```

This is project scope for Codex and Claude Code. For one agent, use `--agent codex` or `--agent claude-code`. Review the CLI's destination summary; expected copies include `.agents/skills/implementation-plan/SKILL.md`, its `scripts/` and `references/`, and the corresponding Claude skill location when selected. Refresh the agent session, then invoke the skill separately in chat. The remote command reads published files; local changes are available only from a local source until they are pushed. For the current local checkout, use its actual path as the npx source:

```powershell
npx skills@1.7.4 add 'D:\ACollectionOfDevelopedSystems\ActiveDevelopment\dev-workflow-packs' --skill implementation-plan --agent codex claude-code --copy
```

This local-source command also starts from the target application folder. It installs the current local checkout, not a remote snapshot. A missing remote skill name means it has not been published there; do not silently switch sources. See the [npx guide](../../../../docs/NPX_INSTALLATION.md) for updates and removal. Use the installer that owns an existing copy.

### Optional recorded/offline Python installation

First obtain the complete collection by the [ZIP or Git instructions](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use). Find its inner root containing `tools/` and `packs/`; `tools/install_skills.py` is a local script there, not a global command. Python 3.11+ is required. PowerShell, starting in that collection root, preview and install in separate commands; replace `D:\My App` with the target project:

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project 'D:\My App' --skills implementation-plan --dry-run
```

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project 'D:\My App' --skills implementation-plan
```

The preview changes nothing. The second command writes recorded project copies and retains installer ownership, backups and Markdown history. `--agent both` is specific to the Python installer; npx uses `--agent codex claude-code`. A prior Python-managed copy must be updated or removed through the Python installer, not implicitly migrated by npx. Installation itself creates no implementation package.

Read the [agent instructions](SKILL.md), [pack catalog](../../SKILL_CATALOG.md) and [collection installation guide](../../../../INSTALL.md).
