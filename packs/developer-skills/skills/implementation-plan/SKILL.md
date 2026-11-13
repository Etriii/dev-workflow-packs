---
name: implementation-plan
description: Create and revise a complete phased implementation package with scoped prompts, progress tracking, skill assignment, and safe ignored storage.
---

# Implementation Plan

Create a source-grounded planning package, modeled on the document ownership of BALE's HIRING_AND_WORKFORCE package. This skill plans implementation; a later invocation of a generated phase prompt is a separate request. Read [the package contract](references/package-contract.md) before drafting or revising files.

## Chat commands

- `create "<task>" [--project PATH] [--max-phases N] [--skills name1,name2] [--skills-mode auto|all] [--commits off|scoped]`: inspect the project, settle material requirements, and save a package. `$implementation-plan "<task>"` is an alias. Bare invocation asks for the task and creates nothing.
- `revise <package-path> "<changes>" [same planning options]`: preserve the old revision and generate a new one. Read its current evidence and carry forward valid decisions, phase identity, status, and handoff. Inherit unspecified options. A different `--project` is invalid.
- `skills <package-path>`: list selected skills and their assignments. `--add name1,name2`, `--remove name1,name2`, and/or `--skills-mode auto|all` create a revision; adding and removing the same name is invalid. Leave other package options unchanged.
- `prompt <package-path> <phase-id>`: show the exact stored copyable prompt. This is read-only and does not execute it.
- `check <package-path>`: inspect structural and semantic consistency; do not edit. Report missing coverage, dependencies, stale references, unavailable skills and evidence limits.
- `status [package-path]`: with a path, show recorded phase states, actual evidence and next action; without one, list recognized packages in the current project. Do not infer implementation from a planning document.
- `help`: explain these commands without creating files.

Commands are agent-chat requests, not a shell CLI. Reject unknown options or conflicting values before saving. `--max-phases` must be a positive integer and is a hard upper bound, including integrated verification. Choose the fewest coherent phases when omitted. Do not omit requirements or hide additional phases as subphases to fit a cap; ask for a changed cap or scope if needed. `--skills-mode auto` and `--commits off` are defaults. No `run`, `--auto`, or all-phase executor exists.

## Create or revise

1. Resolve the target project and applicable instructions. Trace current behavior, owners, public contracts, tests, Git roots and relevant existing plans. Distinguish implemented, missing, conflicting and unknown behavior. Ask only for material product, data, security or hard-to-reverse choices that cannot be derived from source.
2. Build a requirement-to-phase and acceptance map. Assign dependencies before consumers and put integrated proof at the end. Preserve exact accepted decisions; do not imply the package is approved or implementation is complete. If revising, map old to new phases and carry actual proof forward only while it remains valid.
3. Inspect each named skill's installed `SKILL.md` and necessary references. Do not invoke it during planning. In `auto` mode put it in relevant phase prompts with a one-line reason in PHASES.md and `.package.json`; general style skills can appear everywhere, UI skills only where UI changes are in scope. In `all` mode include all selected skills in every prompt. Surface incompatible instructions or unavailable skills, and mark affected prompts pending rather than inventing behavior or installing a skill. Use host-appropriate `$name` (Codex) or `/name` (Claude Code) lines at the start of prompts.
4. Resolve the installed skill directory containing this `SKILL.md`. Use its bundled [package store](scripts/package_store.py) with Python 3.11+ to reserve a safe revision: `python <installed-skill-dir>/scripts/package_store.py start --project <project> --feature <feature> [options]`. For a revision pass `--previous <exact-package-path>` and the inherited options. The helper returns the exact output path. Do not copy the BALE package's domain content or paths.
5. Write all 11 shared documents and separate phase prompts according to the package contract. Then update that revision's `.package.json` `phases` map (`P01` to prompt filename) and `skill_assignments` map (skill name to phase IDs and reason), keeping other metadata intact. Leave status `draft` until manual semantic review and helper checks pass; then set `ready`. Use only the selected revision path. Preserve earlier revisions and unrelated work.
6. Run `python <installed-skill-dir>/scripts/package_store.py check --package <exact-package-path>` and review links, feature/acceptance coverage, phase dependencies, prompt scopes, skill routing, commit language, status, UTF-8 and final newlines. For pathless `status`, use the helper's `list --project <project>` command; its `status`, `skills`, and `prompt` commands accept `--package`. The helper's structural pass does not prove content quality or agent adherence. Report the path, phase count, selected skill placements, Git exclusion result and remaining prerequisites.

## Execution boundary

Each generated prompt covers exactly one phase and stops there. With `--commits off`, it may prepare messages but must not authorize a commit. With `--commits scoped`, its invocation authorizes only owned local commits after implementation and required checks pass, subject to repository instructions and later user limits. No prompt authorizes a push, deployment, production data change or another phase. A package maintenance request does not invoke a phase prompt.

## Generated artifacts

Place packages under `<project-root>/docs/<descriptive-feature>-implementation/`, with each revision in an exclusively created `YYYYMMDDTHHMMSSZ-<unique-id>/` directory. The stable feature folder is skill-owned; `.implementation-plan.json` marks ownership, and each revision has `.package.json`. Preserve previous revisions and resume an identified unfinished revision instead of creating an empty replacement. Reject linked paths, traversal, tracked output and unrelated same-name folders.

Before writing package content, resolve the repository root and inspect `.gitignore`. If `docs/` is absent and has no tracked contents, create it and ensure `/docs/` is ignored. If it exists or has tracked contents, add only `/<docs>/<feature-folder>/` as needed. Preserve existing bytes and line endings, verify effective exclusion with `git check-ignore`, and never untrack files automatically. The helper performs these operations; do not bypass a failure. Outside Git, use the selected project directory and disclose that Git exclusion is unverified. Skill installation files are never a package destination.
