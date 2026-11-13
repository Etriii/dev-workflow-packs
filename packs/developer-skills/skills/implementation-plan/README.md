# Implementation Plan

Create a complete, source-grounded implementation package with shared specifications, separate one-phase prompts, acceptance checks, progress and handoff. A saved package is a plan; use a selected prompt in a later agent request to implement its phase.

## Start in agent chat

After installing the skill, refresh the agent session and open the target project. Codex uses `$implementation-plan`; Claude Code uses `/implementation-plan`. These are chat requests, not terminal commands. Replace `D:\My App`, the feature name, and package paths with your actual values.

```text
$implementation-plan create "Hiring and workforce management" --project "D:\My App" --max-phases 5 --skills caveman,ultimate-ui-ux --skills-mode auto
```

The project path is optional when the target project is open. Bare `$implementation-plan` asks for a task and saves nothing. `$implementation-plan "Hiring and workforce management"` is the `create` shortcut. Without `--max-phases`, the agent chooses the fewest coherent phases. The positive integer cap is strict; the agent asks if the agreed scope cannot fit. The skill inspects actual source and instructions before writing. It asks only for material decisions missing from that evidence.

Every saved package has `README.md`, `PLAN.md`, `CONTRACTS.md`, `PHASES.md`, `PROMPTS.md`, `RUNBOOK.md`, `ACCEPTANCE.md`, `PROGRESS.md`, `HANDOFF.md`, `BLOCKERS.md`, `COMMIT_MESSAGES.md`, and a separate file under `prompts/` for each phase. Initially, unexecuted checks remain `NOT_RUN`. One prompt executes one phase when later pasted; package creation does not implement it.

## Commands and options

The examples below are independent chat requests. Use the exact path returned by `create` or `revise` in place of `<package>`.

```text
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

`--skills name1,name2` selects skills. The default `--skills-mode auto` reads their instructions and assigns them to the phases where they fit. `--skills-mode all` places all selected skills in every prompt; conflicts and missing skills are reported rather than silently resolved. The skill does not install selected skills. `--commits off` is the default: prompts may draft messages but do not authorize commits. `--commits scoped` makes a later phase-prompt invocation authorize only that phase's owned local commits after required checks pass. It never authorizes a push or deployment. Both options can be used on creation or revision.

The package lives under `<project-root>/docs/<feature>-implementation/<UTC-run-id>/`. Each revision has a unique run directory. If the skill creates an absent `docs/` directory, it adds `/docs/` to the root `.gitignore`; if `docs/` already exists or has tracked files, it ignores only the new feature folder. Existing documentation stays intact. The skill verifies Git exclusion before saving; tracked output is refused without automatic untracking. In a non-Git project it reports exclusion as unverified. Resume an identified draft revision after interruption; never overwrite or discard an earlier one. A failed storage check stops saving and reports the exact reason.

`check` confirms the package structure and requires a separate author review of requirement coverage, dependencies, links, prompt scope and evidence claims. A passing check does not prove implementation, native agent adherence or runtime behavior. Invoke the exact stored prompt from `prompt <package> P01` when work on that phase is intended; it stops at that phase.

## Install

### Direct npx installation

Prerequisites: Node.js 22.20+ with npm/npx, network access for npm/GitHub, and Git for repository fallback. These are installer requirements. At runtime, this skill's bundled helper needs Python 3.11+ and Git for exclusion verification inside a Git project; the target application has its own requirements.

PowerShell, starting in the target application folder; replace `D:\My App` with your project path. Run the lines separately:

```powershell
Set-Location 'D:\My App'
npx skills@1.7.4 add https://github.com/Etriii/agent-skills --skill implementation-plan --agent codex claude-code --copy
```

This is project scope for Codex and Claude Code. For one agent, use `--agent codex` or `--agent claude-code`. Review the CLI's destination summary; expected copies include `.agents/skills/implementation-plan/SKILL.md`, its `scripts/` and `references/`, and the corresponding Claude skill location when selected. Refresh the agent session, then invoke the skill separately in chat. The remote command reads published files. Until this new skill is published, use the actual local collection root as the npx source:

```powershell
npx skills@1.7.4 add 'D:\ACollectionOfDevelopedSystems\ActiveDevelopment\agent-skills' --skill implementation-plan --agent codex claude-code --copy
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
