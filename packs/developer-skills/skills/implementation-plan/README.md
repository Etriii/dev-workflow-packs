# Implementation Plan

Start from an existing Codex or Claude Markdown plan, a PDF requirements brief with no plan yet, or a task described in chat. Default planning is detailed and sequential; `--light` reduces documentation for one small task, and `--parallel-ready` prepares independent work for later sessions. The skill presents a plan in chat or saves an ignored package. It never implements application changes, creates branches/worktrees, merges or cleans up Git work. Default planning preserves your current branch rather than switching to main.

Skill responses and generated reports are in English, including for Tagalog or Bisaya requests. Original quotations, code, identifiers, and application content keep their source language when needed for accuracy.

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

For the optional `$request-review` → `$plan-review` sequence, provide the full reviewed-requirements Markdown as this skill's source and include the plan-review findings in the same conversation or alongside the file. The short client summary alone does not preserve all acceptance, dependencies and evidence. The skill rechecks current source and asks its own phase-sizing and output questions; prior review or client confirmation does not authorize implementation.

You may put options before the plan path if that reads more naturally. This is an alternative chat request:

```text
$implementation-plan --skills migration,verify-and-stop --max-phases 4 --test-scope full "<plan-file.md>"
```

The named skills must be installed and relevant; the skill reads their instructions before assigning or using them.

The skill inspects the plan and current source before asking. Detailed planning asks you to choose phase sizing; explicit `--light` uses one task and skips this question:

| Choice | Meaning |
|---|---|
| **Compact** | Use the recommended exact count with fewer coherent phases. |
| **Balanced** | Use the recommended exact count with more room for implementation and verification. |
| **Custom maximum** | Supply a positive hard cap, such as 4; the skill proposes and confirms an exact count of at most 4. |

The recommendations include implementation, checks and integration work. A one-phase option appears when that work fits one session. In detailed mode, `--max-phases N` pre-fills Custom maximum but does not skip confirmation. The skill also resolves one planning output, honoring an explicit choice already made and asking otherwise:

| Choice | Effect | Recommendation |
|---|---|---|
| **Present detailed plan in chat** | Return the complete plan in chat without writing a package. | Choose when you need reviewable text only. |
| **Prepare detailed phase package** | Write and check the ignored package, then stop. | Default recommendation, including one-session work. |

Other questions concern only decisions the plan and source cannot settle, such as scope, business rules, acceptance, permissions, or selected skills. Missing answers stop dependent package work. Neither output authorizes application edits, application tests, a commit, push, deployment or production data change. A later implementation requires a separate request naming the package path and one phase ID, or direct use of that package's stored phase prompt.

You can combine this skill with Codex or Claude's built-in Plan mode: finish its questions and use the agreed plan as this skill's input, either in the same conversation or as a saved file. These two output choices are the skill's own question; they do not change the host's built-in menu. While the host remains in read-only Plan mode, the skill can ask and plan but cannot save package files. For a package selection, the host plan must make package creation and checking its only executable steps. The future application phases are content to write into the package, not steps for the host's **Implement plan** action. After the package is created, “go ahead” or “implement the plan” is ambiguous; specify `Implement P01 from <package-path>` in a separate request or invoke the stored prompt directly. Do not invoke `$implementation-plan` for that implementation request.

Normal outputs require feature-specific requirements and observable acceptance, current source evidence and unknowns, responsible components and dependencies, shared business/API/data/permission contracts, failure paths, actual verification commands or missing prerequisites, and stop/recovery conditions. This is mandatory regardless of model, effort setting or terse chat style; only explicit light mode reduces document structure. More text does not prove quality, and instructions cannot guarantee equal correctness across models. Neither output claims unrun implementation proof. Handoffs name the next task's exact reading set; evidence identifies the revision or dirty changes and actual commands it covered, then is revalidated when affected source changes.

Every detailed package has `ORIGINAL_PLAN.md`, `README.md`, `PLAN.md`, `CONTRACTS.md`, `PHASES.md`, `PROMPTS.md`, `RUNBOOK.md`, `ACCEPTANCE.md`, `PROGRESS.md`, `HANDOFF.md`, `BLOCKERS.md`, `COMMIT_MESSAGES.md`, and separate phase files under `prompts/`. Light packages use the smaller layout below. In either profile a supplied Markdown plan is copied byte for byte into `ORIGINAL_PLAN.md`; answers go in `PLAN.md`. For PDF input, the original PDF is copied byte for byte into `SOURCE_DOCUMENT.pdf` and the agreed working plan goes into `ORIGINAL_PLAN.md`. Without a file, the agreed session plan becomes `ORIGINAL_PLAN.md`. Initially, unexecuted checks remain `NOT_RUN`.

`COMMIT_MESSAGES.md` must contain detailed, copyable messages for the planned work, split by repository and distinct feature. Each message has a Conventional Commit subject and a substantive body explaining the intended behavior, why it matters, planned changes, and relevant verification or migration notes. At planning time, label unrun checks `NOT_RUN` and avoid invented file paths or hashes. When implementation happens, update messages from the actual diff and checks. A list of one-line subjects is incomplete. This requirement applies with every commit policy, including the built-in default with commits off. Terse chat styles do not shorten persisted commit messages.

After a separately requested phase is implemented, an explicit follow-up such as `commit it` authorizes that completed scope to be committed even if the package's commit policy is off. The phase prompt and `HANDOFF.md` identify the exact package revision. On every commit-only follow-up, the agent rereads that revision's `COMMIT_MESSAGES.md`, checks its matching draft against the actual repository diff and checks, stages only owned files, and uses a corrected detailed message. It verifies the commit and remaining Git status, then stops. A stale draft does not authorize extra files or unrun-check claims; missing or unreadable drafts are disclosed. If the active package revision cannot be identified, supply its exact path. This follow-up does not run tests or edit application code unless a repository rule or commit hook requires it; it does not enable future automatic commits, push, deploy or start another phase.

Agent chat, after the selected phase has finished (replace `<package-path>` with its exact revision path when the session does not establish it):

```text
Commit the completed work from <package-path>. Use its COMMIT_MESSAGES.md after checking the actual changes and verification.
```

In light packages, the commit drafts, progress and handoff live in named `PLAN.md` sections instead of separate files. Use that plan's commit-draft section for the same commit-only workflow.

## Choose a planning mode

Examples here are agent-chat requests after opening the target project and refreshing the installed skill. Replace task descriptions, `<package-path>` and project paths with actual values. Claude Code uses `/implementation-plan` instead of `$implementation-plan`.

| Selection | Effect | Boundary |
|---|---|---|
| No mode option | Detailed sequential plan or package. | New work preserves the current branch; revisions inherit saved mode. |
| `--light` | One compact task, no task-count question. | Material questions and correctness/verification requirements remain. |
| `--parallel-ready` or `--parallel-ready=analysis` | Dependencies, ownership, eligible groups and task reading sets. | Does not promise safe simultaneous writes in one checkout. |
| `--parallel-ready=worktree` | Also prepares isolated branch/worktree instructions and merge prompts. | Requires Git, committed baselines and identified targets before prompts are ready; no Git mutation during planning. |
| `--parallel-ready=off` | Sequential preparation in a new revision. | Does not clean up existing branches/worktrees or erase evidence. |

### Lightweight tasks

```text
$implementation-plan create "Correct the empty-state message on the requests page" --light
```

To select saved output without another output question:

```text
$implementation-plan create "Correct the empty-state message on the requests page" --light
Prepare the package.
```

The skill reads current source and relevant tests, settles material uncertainties and plans one coherent task. A saved package contains `.package.json`, `PLAN.md`, `ORIGINAL_PLAN.md` and the original PDF only when supplied. `PLAN.md` combines scope, evidence, contracts, acceptance, checks, detailed commit drafts, progress, blockers, handoff and the P01 execution prompt. No separate tracking files or `prompts/` directory are required. `status` reads this plan; `prompt <package> P01` retrieves its execution section. Nothing executes until separately requested. Resume the identified unfinished revision and update its plan's tracking sections.

Light supports selected skills, test/commit policies and a positive maximum; that maximum is a cap and does not add tasks. It conflicts with parallel modes except `off`. Work too broad for one implementation-and-proof unit requires reduced scope or detailed mode before writes. Security, permissions, data preservation, migration safety and verification still apply.

To expand a light package, explicitly request detailed mode in natural language. A new revision preserves the original and confirms the expanded task count:

```text
$implementation-plan revise "<package-path>" "Expand this into a detailed package covering the agreed additional requirements."
```

To reduce a detailed package to an agreed single task, select light and disable inherited parallel preparation:

```text
$implementation-plan revise "<package-path>" "Limit scope to the agreed empty-state correction." --light --parallel-ready=off
```

### Parallel preparation

```text
$implementation-plan "<plan-file.md>" --parallel-ready
```

The agent reads current owners, contracts, tests and dependencies. Each task records prerequisites, concrete ownership, mutable resources, reading set and rationale, alongside groups that can start together. Shared services, migrations, generated files, fixtures and ports can require serialization even with different filenames. Unknown coupling stays sequential; no safe split is a valid result with an explanation. Default planning preserves the current branch; choosing main or another integration branch is explicit.

For later isolated execution:

```text
$implementation-plan "<plan-file.md>" --parallel-ready=worktree --commits scoped
```

Worktree mode records repository, actual base commit, branch and separate directory, integration target, checks and evidence ownership. It prepares instructions only. Later explicitly invoked workers check live state, create only their owned isolation, verify package access, implement their task, run checks and stop. Existing branches/directories and unrelated changes are preserved. Ignored packages do not follow Git branches: use the canonical package read-only or a verified copy. Workers save separate evidence under `evidence/<phase-id>/`; one coordinator updates canonical progress, handoff and shared commit drafts. Coupled cross-repository work stays sequential unless coherently split; each merge operation targets one repository.

The example permits verified owned local worker commits after a later invocation. Use `--auto-commit` instead when those commits should be required automatically; it conflicts with `--commits`. With commits off, worker results await an explicit commit request and cannot merge while uncommitted. Parallel preparation does not start sessions, install a scheduler, guarantee semantic independence or claim token/time savings. Revisions inherit policies and revalidate affected evidence.

To return to sequential preparation:

```text
$implementation-plan revise "<package-path>" "Prepare the remaining scope sequentially." --parallel-ready=off
```

This saves a revision with phase dependencies and valid history, reporting outstanding branch/evidence recovery separately. It does not run cleanup.

### One Markdown file for merge requests

When isolated work exists, all merge prompts live in **one** file beside implementation prompts:

```text
prompts/
  P01_<OBJECTIVE>.md
  P02_<OBJECTIVE>.md
  P03_<OBJECTIVE>.md
  MERGE_PROMPTS.md
```

The file has shared rules, exact `## M01`, `## M02` headings, descriptive objectives, prerequisites, source branches, target/repository identities, checks, recovery and cleanup rules. Markdown separators distinguish operations. Each section contains a separately copyable agent-chat request with the actual package path. PROMPTS.md links to the sections without duplicated bodies. Integration belongs to identified phases and counts in sizing; merge prompts do not hide extra implementation phases. No safe split means no merge file.

Display one section read-only:

```text
$implementation-plan prompt "<package-path>" M01
```

After the named workers commit their verified work, invoke that section outside the planning skill. Replace the path with its exact revision:

```text
Execute only M01 from "<package-path>/prompts/MERGE_PROMPTS.md". Read its shared rules and selected section, verify live prerequisites, integrate only its named committed work, run required checks, preserve evidence, perform eligible owned cleanup, record the outcome and stop.
```

This explicit request authorizes that local integration, a necessary merge commit and eligible owned cleanup. Displaying a section does not. The executing agent checks source hashes against worker proof, dependencies, target branch/HEAD, a clean checkout and absence of another Git operation. It revalidates target changes since planning, integrates named refs serially and runs combined checks. It does not commit dirty worker results, push, deploy, start another task or silently fix application failures.

Conflicts, missing prerequisites, stale evidence and failed checks stop further merges/cleanup with `MERGE_PENDING` and an exact recovery point. Retry recognizes integrated commits and completes outstanding proof. Only verified integration permits cleanup: preserve durable evidence and needed ignored/untracked deliverables, confirm source commits are target ancestors and identities are task-owned, then remove clean owned worktrees and delete merged owned branches with `git branch -d`. No force deletion or pre-existing work removal. Cleanup failures are recorded separately; verify Git registration and directory existence independently. Repository rules and branch protection still apply.

See [light planning](references/light-planning.md), [parallel planning and metadata](references/parallel-planning.md) and the [detailed package contract](references/package-contract.md) for authoring and recovery rules.

## Optional one-time settings

The skill works without a config file: commits are `off`, test scope is `focused`, and skill assignment mode is `auto`. To set personal defaults for **new** work, copy the installed skill's [`assets/config.json`](assets/config.json) to `~/.config/implementation-plan/config.json` (on Windows, `$HOME\.config\implementation-plan\config.json`). Keep this file outside the installed skill so an update cannot replace your settings. It applies across projects for this user; project instructions and explicit requests still take precedence. This setup is optional and does not install or run the skill.

PowerShell, starting in any folder: replace `<installed-skill-dir>` with the installed `implementation-plan` folder reported by your installer. Run these commands once; the copy step preserves an existing config:

```powershell
$settingsDir = Join-Path $HOME '.config/implementation-plan'
New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $settingsDir 'config.json'))) { Copy-Item -LiteralPath '<installed-skill-dir>\assets\config.json' -Destination (Join-Path $settingsDir 'config.json') }
```

Edit only `current` to choose `commits: off|scoped|auto`, `test_scope: focused|full`, and `skills_mode: auto|all`. To enable auto-commit in later phase prompts, change `"commits": "off"` under `current` to `"commits": "auto"`. Leave `defaults_at_setup` as the original reference; it never controls behavior or changes on skill updates. The file requires `schema_version: 1` and all three keys in both objects. Invalid JSON, missing or unknown keys, and unsupported values stop new package work before writes; fix the file or remove it to restore built-in defaults. The skill shows one short line before new planning, such as `Commits auto (was off) | Tests focused | Skills auto`. Explicit request options override `current` for that request. A configured `auto` applies only to a later, separately invoked phase prompt; planning and package preparation never commit.

Each package stores its resolved settings in `.package.json` and its prompts. Changing this config affects new work only; existing packages and their prompts keep their saved policy. Use `revise <package> "<change-description>" --commits off` (or another explicit planning option) to change an existing package in a new revision. The config is not a new chat command, and read-only `prompt`, `check`, `status`, `skills`, and `help` do not change it.

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
$implementation-plan prompt <package> M01
$implementation-plan check <package>
$implementation-plan status <package>
$implementation-plan status
$implementation-plan help
```

`revise` and changing `skills` requests save a new revision, preserve earlier files and valid evidence, and report the new path. Omitted options inherit prior values, including profile and parallel mode. `skills` changes only skill selection/assignment mode. `skills` without changes, `prompt`, `check`, `status`, and `help` are read-only. Unknown phase/merge IDs, conflicting options, invalid enum values, missing/path-like inputs and cross-project revisions are errors. Adding and removing the same skill in one request is invalid. `status` without a path lists recognized packages in the current project; it does not select one for editing.

`--max-phases N` proposes the Custom maximum hard cap in detailed mode; light mode keeps one task within the supplied cap. Detailed mode confirms the cap and resulting exact count before acting. The package store records both values and rejects a count above the cap. `--skills name1,name2` selects skills for later phase prompts. With no config, `--skills-mode auto` is the default: it reads selected skill instructions and assigns them to relevant phases. `--skills-mode all` places all selected skills in every prompt; conflicts and missing skills are reported rather than silently resolved. The planning skill does not install or invoke selected skills. With no config, `--commits off` is the default: later phase prompts may draft messages but do not authorize commits. `--commits scoped` permits owned local commits when a later phase is separately invoked and its required checks pass, subject to repository rules. `--auto-commit` records `auto` in the package so a later invoked phase prompt requires a local commit of only verified, owned changes after its checks pass. That commit must have a Conventional Commit subject, a blank line and a substantive body explaining what changed, why, and which checks actually ran; subject-only messages fail this requirement. The later agent inspects the Git diff, stages only owned paths, and verifies the committed message, changed paths and remaining status. Failed checks, missing prerequisites or no owned changes mean no commit; the agent reports the reason. Planning, package creation and revision never commit, including with `--auto-commit`. To turn auto-commit off in a package revision, use `--commits off`. Do not combine `--auto-commit` with `--commits`, even `scoped`; an option matching the config is allowed but redundant. No policy authorizes a push, deployment or another phase.

With no config, `--test-scope focused` is the default for later implementation prompts: they require relevant tests for changed behavior and affected integrations. `--test-scope full` also requires the complete configured suite for each component changed in the selected phase. If you specifically need the entire backend suite, say so in the request; the package records that named suite in its runbook and prompts. The planning skill identifies actual project commands when available and records missing prerequisites. It does not run application tests. A full suite is never reported as passed when it was skipped or interrupted.

Package choices save under `<project-root>/.implementation-plans/YYYYMMDDTHHMMSSZ-<feature>/<UTC-run-id>/`. The UTC timestamp makes new feature folders sort by creation time in a file browser; for example, `20261120T063718Z-queue-and-operations/`. Each revision has a unique run directory and stays in its feature folder. The skill adds `/.implementation-plans/` to the root `.gitignore` when needed and verifies exclusion before saving. It leaves existing `docs/` content and older feature folders untouched; revisions of earlier packages link back to their original path without moving it. Tracked output is refused without automatic untracking. In a non-Git project exclusion is unverified. Resume an identified draft revision after interruption; never overwrite or discard an earlier one. A failed storage check stops saving and reports the exact reason.

`check` confirms profile-specific files, graph consistency, ownership/resource separation, worktree baselines/identities, and merge-section mapping. It rejects subject-only commit lists or commit blocks without bodies in COMMIT_MESSAGES.md or the light plan. The author must still review whether each body covers its repository and logical feature in useful detail, along with requirement coverage, dependencies, links, prompt scope and evidence claims. A passing check does not prove implementation, native agent adherence or runtime behavior. After package preparation, request one specific phase in a separate turn using its exact path and ID, such as `Implement P01 from <package-path>`, or invoke the exact stored prompt returned by `prompt <package> P01`. Both routes stop at that phase; `$implementation-plan` itself remains planning-only.

## Bundled helper commands

The agent normally runs `scripts/package_store.py` from the installed skill. These are terminal helper commands, not additional chat flags. They require Python 3.11+ and Git on PATH; the helper uses Git to establish roots even when the selected directory is not a repository. No external Python package is required. It reserves storage and checks authored content; it does not generate finished plans or execute worker/merge prompts.

PowerShell, starting in any folder: replace `<installed-skill-dir>`, `<project-path>`, `<feature-name>` and `<package-path>` with actual paths/name. This changing command reserves a light draft and may append the root ignore rule; it does not write its PLAN.md:

```powershell
python -B '<installed-skill-dir>/scripts/package_store.py' start --project '<project-path>' --feature '<feature-name>' --profile light --phase-count 1
```

This alternative reserves a detailed worktree-planning draft without creating branches:

```powershell
python -B '<installed-skill-dir>/scripts/package_store.py' start --project '<project-path>' --feature '<feature-name>' --phase-count 3 --parallel-ready=worktree
```

The confirmed task count replaces `3`. Additional `start` arguments are `--max-phases N`, `--skills name1,name2`, `--skills-mode auto|all`, `--commits off|scoped|auto`, `--test-scope focused|full`, `--previous <exact-package-path>`, `--source-plan <Markdown-path>` or `--source-document <PDF-path>` (mutually exclusive), `--profile detailed|light`, and `--parallel-ready[=off|analysis|worktree]`. Bare helper `--parallel-ready` selects analysis. Chat `--light` maps to helper `--profile light`; chat `--auto-commit` maps to helper `--commits auto`. Do not transfer these flags between interfaces. New reservations default to detailed/off and the existing user-config policies; revisions inherit unspecified policies, selection, sizing, profile and mode. Explicit overrides apply to the new revision. Light needs one task with parallel off; nonpositive counts, exceeded caps, invalid policies/names and unsafe storage fail. No helper dry-run or merge executor exists.

Read-only examples, same shell and folder rules:

```powershell
python -B '<installed-skill-dir>/scripts/package_store.py' list --project '<project-path>'
```

```powershell
python -B '<installed-skill-dir>/scripts/package_store.py' check --package '<package-path>'
```

```powershell
python -B '<installed-skill-dir>/scripts/package_store.py' status --package '<package-path>'
```

```powershell
python -B '<installed-skill-dir>/scripts/package_store.py' skills --package '<package-path>'
```

```powershell
python -B '<installed-skill-dir>/scripts/package_store.py' prompt --package '<package-path>' --phase M01
```

The historical helper argument `--phase` accepts either a Pxx or Mxx ID. Prompt retrieval requires a ready package with no validation errors; unknown IDs fail. `check` returns nonzero for structural errors, including missing documents, dependency cycles, overlapping grouped owners/resources, invalid baselines/worktree identities or merge-section mappings. `status` includes the saved ledger and consistency errors without treating them as implementation proof. Fix an identified unfinished draft, recheck, and mark ready only after semantic review. Use a new revision for changes to an established plan. These read-only commands do not change package files, Git state or user config.

## Install

### Direct npx installation

Prerequisites: Node.js 22.20+ with npm/npx, network access for npm/GitHub, and Git for repository fallback. These are installer requirements. At runtime, this skill's bundled helper needs Python 3.11+ and Git for exclusion verification inside a Git project; the target application has its own requirements. PDF input also needs a PDF reader available to the agent for content inspection. The helper only validates and copies PDF bytes; it does not extract text or perform OCR. If the document cannot be read reliably, provide an accessible text copy before planning.

PowerShell, starting in the target application folder; replace `<project-path>` with your existing project path. Run the lines separately:

```powershell
Set-Location '<project-path>'
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill implementation-plan --agent codex claude-code --copy
```

This is project scope for Codex and Claude Code. For one agent, use `--agent codex` or `--agent claude-code`. Review the CLI's destination summary; expected copies include `.agents/skills/implementation-plan/SKILL.md`, its `scripts/`, `references/`, and `assets/config.json`, and the corresponding Claude skill location when selected. Refresh the agent session, then invoke the skill separately in chat. The remote command reads published files; local changes are available only from a local source until they are pushed. For a complete local checkout, replace `<collection-root>` with its path as the npx source:

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
