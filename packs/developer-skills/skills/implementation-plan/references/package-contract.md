# Implementation package contract

The package records a plan, not completed work. Make every file specific to the feature and current repository. Scale detail to complexity while preserving these document owners. Do not fill documents with copied headings or invented test results.

| File | Owns |
|---|---|
| `ORIGINAL_PLAN.md` | Unchanged snapshot of a supplied plan, or the agreed session plan when no file was supplied. Preserve source wording; record later clarifications in `PLAN.md`. |
| `README.md` | Purpose, how to use one phase prompt, file ownership and repository boundaries. |
| `PLAN.md` | Goal, approved decisions, exclusions, current source evidence and requirement-to-phase coverage. |
| `CONTRACTS.md` | Shared business, API, data, permission and failure invariants that phases must preserve. |
| `PHASES.md` | Ordered tasks, dependencies, deliverables, acceptance ownership and selected-skill assignments with reasons. |
| `PROMPTS.md` | Index linking each executable `prompts/Pxx_*.md`; no duplicated prompt bodies. |
| `RUNBOOK.md` | Shared preflight, verification, Git, recovery and stop rules. |
| `ACCEPTANCE.md` | Stable observable criteria, including failure and forbidden paths where relevant. |
| `PROGRESS.md` | Sole status, evidence, decision, blocker and commit-outcome ledger. Begin with no implementation proof unless current source provides it. |
| `HANDOFF.md` | Immediate next action, unresolved issues and recovery point; link to PROGRESS.md for history. |
| `BLOCKERS.md` | Actual blocking decisions and dependency impact, with prospective cases clearly labeled as examples. |
| `COMMIT_MESSAGES.md` | Drafts tied to repository and real changes; no fabricated validation or commit hashes. |

The phase list must match the user's confirmed exact count; an optional maximum remains a separate cap. Each phase prompt names only its phase, project path and package path, prerequisites, relevant source and package sections, deliverables, acceptance checks, tracking updates and stop condition. Keep the prompt self-contained enough to start in a fresh session while linking shared detail rather than duplicating whole specifications. Use descriptive user-facing objectives; retain phase IDs only where technically needed.

Record the source evidence used during planning and its limits. Do not edit `ORIGINAL_PLAN.md` to incorporate answers; keep the source file's original bytes when one was supplied. The store checks its snapshot hash. A plan created from chat is recorded there before deriving the package documents. Unrun tests are `NOT_RUN`; later requirements are `DUE_LATER` only with their owner phase. Completion requires actual implementation and required proof, not a checked box, generated prompt, or prepared commit message. A revision links to its predecessor, retains valid results and marks invalidated evidence for recheck.

If a selected skill is unavailable, list its exact name, affected prompts and installation prerequisite. The output still may be saved as a draft; do not label affected prompts ready. In `all` mode, every prompt includes all selected skills, but their instructions remain limited by selected-phase scope and repository policy. Detect scope or workflow conflicts before saying a prompt is ready.

The helper verifies safe storage and basic files. The author must also check local Markdown links, coverage of every requirement, one owner for each acceptance case, dependency order, appropriate skill assignment, and no hidden commit authorization. Do not label an unchecked item passed.
