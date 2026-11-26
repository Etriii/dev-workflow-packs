# Implementation Plan

Plan a change from Markdown, PDF or chat, then hand off one complete task at a time. New work uses **Balanced**: small reading sets, shared facts at the revision root and one prompt per phase folder. Choose **Detailed** for the existing comprehensive package, or **Light** for one small task. Planning never implements, runs application tests, commits, creates worktrees or merges.

## Start in agent chat

Use an installed skill in an existing project. Replace every angle-bracket placeholder with the actual source, project, package, task or skill name. These are agent-chat requests, not terminal commands; Claude Code uses /implementation-plan instead of $implementation-plan.

~~~text
$implementation-plan create "Add a compact report picker" --auto-commit
~~~

~~~text
$implementation-plan "<plan-file.md>" --project "<project-path>"
~~~

~~~text
$implementation-plan "<requirements.pdf>" --detailed --max-phases 3 --skills migration,verify-and-stop
~~~

The skill inspects current source, constraints, permission/data effects and actual checks before planning. A PDF must be readable across all relevant pages; otherwise accessible input is required. Markdown/PDF path-like input must exist. Options may precede the path. Quoted non-path task text without create is an alias; bare invocation asks for the task/source.

It honors an existing chat/package selection, otherwise asks which output to prepare. Chat-only writes nothing. A package writes only ignored planning artifacts and, when needed, the narrowly scoped root ignore rule. In read-only host Plan mode, file creation waits; a host plan to create a package authorizes that creation only.

## Profiles, policies and sizing

| Selection | Behavior |
|---|---|
| No profile option on new work | Balanced; smallest coherent split, no mandatory task-count questionnaire. Routine reversible choices follow evidence. |
| --balanced | Explicitly select the compact multi-task contract, including when revising another profile. |
| --detailed | Existing detailed contract: eleven shared documents, original plan and standalone prompts; confirms Compact, Balanced or Custom maximum sizing before output. |
| --light | One coherent task, PLAN.md containing specification, execution, tracking and detailed commit drafts. No sizing question; incompatible with parallel modes except off. |
| --max-phases N | Positive hard cap, including necessary integration; not a requested count. An impossible cap/scope needs resolution, not hidden subphases. |
| --skills a,b | Selected installed skills for later prompts. Read them during planning; do not invoke or install them. |
| --skills-mode auto or all | Auto routes relevant skills; all routes every selected skill without expanding task scope. Missing/conflicting required skills leave only affected work pending. |
| --commits off or scoped | Off leaves changes and drafts; scoped permits verified owned local commits when the selected task is invoked. |
| --auto-commit | Records auto: the later selected task must commit verified owned changes without another commit question. Conflicts with every --commits value. |
| --test-scope focused or full | Focused covers changed behavior and affected integrations; full adds configured suites for changed components. Repository gates still apply. An explicitly requested complete named suite selects full for that suite. |

Profile options conflict with each other. Unknown options, invalid values, missing files, unsafe paths and cross-project revisions fail before writes. No run, --auto or unattended all-task executor exists.

Optional user settings live in ~/.config/implementation-plan/config.json (Windows: beneath the user profile). The [template](assets/config.json) requires schema_version=1 and complete defaults_at_setup/current objects containing only commits, test_scope and skills_mode. New work uses current; missing config means off/focused/auto. Invalid config stops writes. Explicit options override it; setup defaults remain historical. Profile and parallel defaults are not new global config keys. Before planning, the skill discloses effective policies and changes from setup defaults. Existing revisions inherit their saved choices; config edits do not silently change them.

## Balanced package

~~~text
<feature>/<revision>/
  .package.json
  PLAN.md
  PROMPTS.md
  STATUS.md
  DECISIONS.md
  phase-01/
    PROMPT.md
    outputs/                 # created only for actual evidence
  phase-02/
    PROMPT.md
  MERGE_PROMPTS.md            # only for actual isolated integration
~~~

Shared scope/contracts/policies live in PLAN.md. PROMPTS.md links each task, its prerequisites, separate-session eligibility, concurrent partners, isolation and integration owner. STATUS.md has one current state/evidence/next-action summary. DECISIONS.md owns meaningful questions and chosen answers, tagged by task. Each PROMPT.md contains only its task, exact reading set, observable acceptance, actual commands, detailed commit drafts and stop conditions. Logs/rendered outputs belong under the phase that produced them. No empty evidence folders or duplicate handoff/blocker documents are required.

A read-only task expecting no tracked changes records `NO_COMMIT_EXPECTED: <specific reason>` in its prompt instead of a fabricated commit draft. An implementation task still needs a substantive draft; a subject-only message fails even alongside that marker.

Supplied Markdown/PDF snapshots are preserved byte-for-byte with checksums; a chat task does not create an extra copy of PLAN.md. New revisions preserve actual supplied evidence. Balanced reservations use schema 4 with phase mappings such as P01 -> phase-01/PROMPT.md. Detailed/Light retain schema 3 and their existing layouts; schemas 1-3 and legacy docs packages remain readable in place without implicit migration. See the [Balanced contract](references/balanced-planning.md), [Detailed contract](references/package-contract.md) and [Light contract](references/light-planning.md).

## Execute a selected task

A ready package is checked planning output, not passing application proof. Later request one exact task:

~~~text
Implement P01 from "<exact-package-path>". Complete its owned implementation and checks, follow its saved commit policy, record decisions and return the recommended next move with its copyable prompt.
~~~

The selected task inspects live source/Git, validates prerequisites, reads only relevant sections and completes its feature slice. It resolves clear in-scope implementation failures and routine reversible choices rather than repeatedly asking to continue. It can continue independent authorized steps while one gate is unavailable. It cannot claim completion with missing required proof or silently repair unrelated features. Material unresolved public behavior, security, destructive data, billing and hard-to-reverse choices still need an answer when existing authorization does not cover them.

Meaningful choices are recorded with the question, alternatives, recommended/chosen answer, reason, prior behavior/source identity, changed owners, actual checks and status. Planning records PROPOSED; only execution can record APPLIED. Each decision has exactly two copyable requests: **Change** selects a real alternative (editable for another listed/custom answer), and **Undo** restores recorded prior behavior with current-source/dependency checks. They preserve unrelated work and respect data-recovery limits; no blanket reset or unconditional whole-commit revert. Invoking a request authorizes that decision's bounded local changes only.

~~~text
Change decision P01-D01 from "<exact-package-path>/DECISIONS.md" to the alternative recorded in its Change prompt. Inspect current dependencies, make only the decision change, verify it and update the record.
~~~

~~~text
Undo decision P01-D01 from "<exact-package-path>/DECISIONS.md" using its recorded prior behavior and Undo prompt. Preserve later unrelated work, verify restoration and record its actual result.
~~~

These illustrate the natural-language actions; generated prompts contain real IDs, paths and a concrete choice. They are not helper commands. Detailed creates a decision log only when needed; Light uses a Decisions section in its plan. Parallel workers keep decisions/results under their owning outputs; one coordinator updates shared status and decision records.

Each result reports completed behavior, actual proof, decision IDs and remaining gates, then one recommended next move plus a ready-to-paste prompt. The move may be another ready task, integration, recovery or a final read-only review. Recommendation does not execute it. Balanced checks the shared and existing worker decision logs for duplicate/task-qualified IDs, a literal proposed/applied/changed/reverted Status field and exactly two addressed recovery prompts under Change and Undo headings. It never applies or undoes a decision itself. See the [completion and decision contract](references/execution.md).

With auto commits, only passing owned changes are committed locally with a Conventional Commit subject, blank line and substantive body describing behavior, reason and actual checks. Failures, missing required proof or no owned changes prevent a commit. A later explicit commit-only request rereads the exact draft (Balanced: owning PROMPT.md; Detailed: COMMIT_MESSAGES.md; Light: plan section), inspects actual diffs/results and commits only that scope. It refreshes recorded commit/current state without creating another package revision or rerunning checks solely for committing unless a repository rule/hook requires it. No task authorizes a push, deployment, production mutation or another task.

## Separate sessions and parallel work

Balanced assesses independence by default. Inside Git it prepares worktree instructions for safe groups; outside Git it records analysis only. No safe split is valid and adds no merge file. Separate sessions can still be sequential; concurrent eligibility needs inspected ownership, dependencies, contracts and isolated mutable resources.

~~~text
$implementation-plan create "Improve independent PDF and workbook renderers" --parallel-ready=worktree --auto-commit
~~~

Bare --parallel-ready selects analysis only; =worktree requires Git; =off disables preparation in a revision. Detailed defaults to sequential unless selected. Light conflicts with analysis/worktree. These modes prepare instructions; planning never creates branches/worktrees, starts workers or merges. Safe groups have disjoint owners and isolated ports/databases/fixtures; unknown coupling stays sequential.

Invoked worker prompts create their named owned worktrees from actual committed baselines, verify ignored-package access, implement/test and follow saved commit policy. Shared root documents have one writer; workers store task results under phase-NN/outputs/. Off leaves integration pending; auto never authorizes unverified commits.

All named merge requests live in one file: Balanced uses root MERGE_PROMPTS.md; legacy Detailed uses prompts/MERGE_PROMPTS.md. A later request is:

~~~text
Execute only M01 from "<exact-package-path>/MERGE_PROMPTS.md". Read its shared rules, integrate the named verified commits, run combined checks, preserve evidence, clean up eligible owned worktrees and branches, record the result and stop.
~~~

One owner integrates serially. Invoking a merge section authorizes only named local integration and guarded cleanup, including a necessary merge commit; displaying it does nothing. It does not commit dirty workers or start another operation. Failed proof, uncertain conflicts or unknown ownership leave recoverable state. Successful cleanup requires clean task-owned worktrees, preserved ignored/untracked deliverables and all source commits reachable from the target; use safe merged-branch deletion, never force deletion. Resume recognizes landed commits and completes outstanding checks instead of replaying merges. See the [parallel contract](references/parallel-planning.md).

## Inspect, revise and resume

Each action below is agent chat, with actual paths replacing placeholders:

~~~text
$implementation-plan status
~~~

~~~text
$implementation-plan status "<package-path>"
~~~

~~~text
$implementation-plan status "<package-path>" --history
~~~

~~~text
$implementation-plan check "<package-path>"
~~~

~~~text
$implementation-plan prompt "<package-path>" P01
~~~

~~~text
$implementation-plan prompt "<package-path>" M01
~~~

~~~text
$implementation-plan skills "<package-path>"
~~~

~~~text
$implementation-plan skills "<package-path>" --add migration --remove ultimate-ui-ux --skills-mode auto
~~~

~~~text
$implementation-plan revise "<package-path>" "Keep existing acceptance and use the compact layout" --balanced
~~~

~~~text
$implementation-plan revise "<package-path>" "Keep the same scope and disable parallel preparation" --parallel-ready=off --commits off
~~~

~~~text
$implementation-plan help
~~~

Status without a path lists recognized project packages; it does not choose one for mutation. With a path it reports recorded current states and dependency eligibility, always requiring live preflight before starting. --history includes the saved ledger, not every log. Check reports structural errors and requires manual semantic review. Prompt displays only the named ready Pxx/Mxx. Unknown IDs, drafts or validation errors prevent execution-prompt retrieval. Help and unchanged skills/status/check/prompt requests are read-only.

Revise and changing skills requests create a new revision, retaining prior content/evidence and inherited policies except explicit changes. Skills changes only selection/assignment. A different --project, add/remove overlap or conflicting profile/commit flags is invalid. A profile conversion preserves all retained requirements and valid proof. Ordinary current-state, decision-outcome and commit updates do not generate new revisions. Resume the identified unfinished run; never guess the latest or replace it with an empty package.

## Terminal helper

Runtime prerequisites: Python 3.11+; Git for exclusion checking in Git projects and for worktree planning. PowerShell, starting in any folder: replace <installed-skill-dir>, <project-path>, <feature-name> and <package-path>. These are separate terminal commands, not agent-chat options.

Reserve a Balanced draft (writes metadata/supplied snapshots and may add the root ignore rule; does not write finished documents):

~~~powershell
python -B '<installed-skill-dir>/scripts/package_store.py' start --project '<project-path>' --feature '<feature-name>' --phase-count 2
~~~

The exact chosen count replaces 2. Helper start additionally supports --max-phases N, --skills a,b, --skills-mode auto|all, --commits off|scoped|auto, --test-scope focused|full, --previous <package>, --source-plan <Markdown> or --source-document <PDF>, --profile balanced|detailed|light and --parallel-ready[=off|analysis|worktree]. Sources conflict. Chat --balanced/--detailed/--light map to helper --profile; chat --auto-commit maps to helper --commits auto. Do not transfer flags between interfaces. Invalid options/config, missing Git for explicit worktrees and unsafe storage stop before writes. No helper dry-run, task executor or merge executor exists.

Read-only terminal commands:

~~~powershell
python -B '<installed-skill-dir>/scripts/package_store.py' list --project '<project-path>'
~~~

~~~powershell
python -B '<installed-skill-dir>/scripts/package_store.py' check --package '<package-path>'
~~~

~~~powershell
python -B '<installed-skill-dir>/scripts/package_store.py' status --package '<package-path>'
~~~

~~~powershell
python -B '<installed-skill-dir>/scripts/package_store.py' status --package '<package-path>' --history
~~~

~~~powershell
python -B '<installed-skill-dir>/scripts/package_store.py' skills --package '<package-path>'
~~~

~~~powershell
python -B '<installed-skill-dir>/scripts/package_store.py' prompt --package '<package-path>' --phase P01
~~~

The historical helper --phase accepts Pxx or Mxx. Check returns nonzero for structural errors: required files, links, task mappings/current states, graphs, draft bodies, ownership/resources or worktree/merge metadata. This does not certify plan quality, decision safety, native agent adherence or runtime behavior. Fix the identified draft, review semantics and check before marking ready. All read-only helper actions preserve package/Git/config state.

## Install

### Direct npx installation

Prerequisites: Node.js 22.20+ with npm/npx, network access for npm/GitHub, and Git for repository fallback. These are installer requirements. At runtime, this skill's bundled helper needs Python 3.11+ and Git for exclusion verification inside a Git project; the target application has its own requirements. PDF input also needs a PDF reader available to the agent for content inspection. The helper only validates and copies PDF bytes; it does not extract text or perform OCR. If the document cannot be read reliably, provide an accessible text copy before planning.

PowerShell, starting in the target application folder; replace `<project-path>` with your existing project path. Run the lines separately:

```powershell
Set-Location '<project-path>'
```

```powershell
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
