# Lightweight planning

Read only when light mode is selected. It reduces documentation and questions for one coherent task; it never weakens authorization, security, compatibility, migration safety, verification or evidence requirements. If the source cannot fit one coherent implementation-and-proof session, settle reduced scope or detailed mode before writing. Do not silently expand or truncate it.

## Output and questions

Skip phase-sizing questions and use P01 only. A positive `--max-phases` remains an upper bound; it does not request extra tasks. Resolve material uncertainties and the chat/package choice, honoring answers already supplied. Chat output contains the compact plan directly. A saved light revision contains `.package.json`, `PLAN.md`, `ORIGINAL_PLAN.md`, and `SOURCE_DOCUMENT.pdf` only when supplied. No separate `prompts/`, status, handoff or commit-message document is required.

Keep the original-source and safe-storage rules from SKILL.md. Reserve using the installed helper's internal `--profile light --phase-count 1`. Do not add profile fields to user-global config.

## One document, complete responsibility

Write these feature-specific responsibilities in `PLAN.md`, combining adjacent sections where natural:

- Objective, scope and exclusions; source evidence and unresolved facts.
- Responsible components, affected contracts and dependencies; data, permission, failure and recovery effects where relevant.
- Observable acceptance and actual verification commands or missing prerequisites.
- Resolved commit, test and skill policies and skill assignments.
- Detailed copyable commit drafts, with unrun checks marked `NOT_RUN`. Preserve the normal commit-only follow-up rule, pointing to this plan's commit-draft section.
- Progress/evidence, blockers, decisions, and immediate handoff with the exact revision path and next action. Initial implementation and tests are `NOT_RUN`.
- A copyable later execution prompt under the exact level-two heading `## P01`. It names project and package, reads the plan, implements only the task, checks applicable acceptance, updates this document, follows saved commit policy and stops. Do not invoke the planning skill inside it.

Use real decisions and commands, not generic headings. The prompt section extends to the next level-two heading or end of file; keep nested headings below it at level three or deeper. `prompt <package> P01` displays this section without executing it. `status <package>` reads the plan as the ledger. Commit bodies remain detailed even in light mode.

## Metadata, revisions and checks

New packages use schema 3. Set `profile: "light"`, `phase_count: 1`, `phases: {"P01": "PLAN.md#P01"}`, `dependencies: {"P01": []}` and normal skill assignments. Preserve the helper's remaining metadata.

Revisions inherit light mode unless explicitly changed. A natural request to expand to detailed mode creates a new revision using internal `--profile detailed` and the confirmed phase count; write the full detailed contract there. Converting a detailed plan to light requires an explicit one-task scope and `--phase-count 1`; carry every retained requirement, source snapshot and valid result forward. Preserve the original revision and label invalidated evidence for recheck.

Run `check --package <exact-path>` and manually review acceptance coverage and the execution prompt. A passing structural check does not establish plan quality, agent adherence or implementation completion.
