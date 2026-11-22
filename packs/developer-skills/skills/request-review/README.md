# Request Review

Review informal development feedback or a requirements PDF against the current application. The review preserves original wording and source references, checks current behavior and access, asks focused questions, and produces a categorized review or short scope summary. It does not edit the application by default. See [agent instructions](SKILL.md), [output rules](references/review-workflow.md), and the [collection command guide](../../../../docs/SKILL_COMMANDS.md).

## Install

Installer prerequisites: Node.js 22.20+ with npm/npx; network access for a remote source; Git for repository fallback. Runtime: an agent with readable application source and any supplied documents. Python 3.11+ is needed only for the optional state helper or recorded installer. PDF inspection may require host PDF tools, rendering or OCR; unavailable methods must be reported. No other skill is required for basic review. On Windows, use PowerShell.

**Direct project install, PowerShell from the target application folder.** Replace `D:\My App` with that folder. `--agent codex claude-code` selects both agents; choose one agent name if only one is wanted. `--copy` installs copies in project agent destinations.

```powershell
Set-Location 'D:\My App'
```

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill request-review --agent codex claude-code --copy
```

Review the CLI selection/destination summary and any prompt. Verify the selected copies:

```powershell
Test-Path '.agents/skills/request-review/SKILL.md'
```

```powershell
Test-Path '.claude/skills/request-review/SKILL.md'
```

Refresh both agent sessions, open the application, then invoke `$request-review` in Codex chat or `/request-review` in Claude Code chat. Installation does not run a review. **Alternative global copied install**, PowerShell from any folder, uses `-g --copy` and the same selected source/ref:

```powershell
npx skills@1.7.4 add https://github.com/Etriii/dev-workflow-packs --skill request-review --agent codex claude-code -g --copy
```

Verify global destinations shown by the CLI, normally under the profile's `.agents/skills/request-review/` and `.claude/skills/request-review/`, then refresh sessions. Remote commands use published files. Until this skill is published at that source, use the complete local checkout as the `add` source or the optional Python route; unpushed edits are not remotely available. Preserve the original source/ref when replacing a copy. See [npx source alternatives](../../../../docs/NPX_INSTALLATION.md#troubleshooting).

For an unpublished local checkout, this is a **project install alternative** from the application folder. Replace `D:\Tools\dev-workflow-packs` with the complete checkout root containing `packs/`:

```powershell
npx skills@1.7.4 add 'D:\Tools\dev-workflow-packs' --skill request-review --agent codex claude-code --copy
```

**Optional recorded/offline Python install.** First [download and extract the complete ZIP or clone the repository](../../../../INSTALL.md#optional-local-copy-for-python-and-offline-use). Find its inner root containing `tools/` and `packs/`; `tools/install_skills.py` is a local file. PowerShell from that collection root, replacing both example paths, preview first:

```powershell
Set-Location 'D:\Tools\dev-workflow-packs'
```

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project 'D:\My App' --skills request-review --dry-run
```

Then run the changing command separately after checking the preview:

```powershell
python tools/install_skills.py --pack developer-skills --agent both --project 'D:\My App' --skills request-review
```

Python uses `--agent both`; npx uses `--agent codex claude-code`. The Python installer records ownership, backups and Markdown operation history. Use the installer that owns an existing copy for update/removal; npx does not migrate Python ownership. See [replacement alternatives](../../../../INSTALL.md#existing-copies-and-replacement) and [removal](../../../../UNINSTALL.md).

### Update alternatives

Save local edits to installed copies first. For an **npx-managed project copy**, PowerShell from the application folder, with Node.js 22.20+, npm/npx, network, the recorded source and Git for fallback:

```powershell
Set-Location 'D:\My App'
```

```powershell
npx skills@1.7.4 update request-review --project
```

For an **npx-managed global copy**, PowerShell from any folder with the same prerequisites:

```powershell
npx skills@1.7.4 update request-review --global
```

For copied global agent destinations, use the global `add ... -g --copy` alternative above with the **original** source/ref. If originally pinned or local, substitute that source/ref. `update` does not forward `--agent` or `--copy`; for a copied project destination, repeat the original project `add` selection. Review CLI status (updated/current/skipped/failed), verify actual destination files and refresh agent sessions. Python-managed copies use their [recorded replacement route](../../../../INSTALL.md#existing-copies-and-replacement). See [npx updates](../../../../docs/NPX_INSTALLATION.md#updates-and-removal).

## Agent-chat interface

These are chat requests, never terminal commands. Open the target application; identify an external related repository naturally if needed. A bare invocation uses clearly supplied requests or an attachment. If there is none, the agent asks for the request and does not select unrelated earlier content. A missing path-like document is an error. Quote file paths with spaces. Options may precede or follow a document. Unknown flags, competing documents, and `--summary` combined with new input or `--detailed` are invalid. A natural “help” request prints these main forms briefly.

```text
$request-review
Expired notices remain on PACD. Make its banner look like the staff banner.
```

```text
$request-review "requirements.pdf"
```

```text
$request-review --detailed
Expired notices remain on PACD. Make its banner look like the staff banner.
```

```text
$request-review "requirements with spaces.pdf" --detailed
```

```text
$request-review --summary
```

Use `/request-review` with the same arguments in Claude Code. Existing accessible `.md` and `.txt` requirements are also accepted; attached PDFs work when the host exposes them. A PDF plus additional chat instructions is one review, with both sources mapped. The agent inventories all relevant PDF pages and uses available text extraction, rendering, visual inspection or OCR; unreadable passages remain blockers. `--detailed` changes the report depth only. `--summary` uses an identified recorded review, applies eligible unanswered defaults and does not reassess code; if no review or several plausible reviews exist, the agent asks which one. Display depth persists until changed.

The review reads application code, guards/policies, tests, configuration and safe local evidence as relevant. It verifies routes, roles and current behavior rather than trusting page names. Default output is grouped by application area with English request, finding, recommendation, concise file table and decisions. Detailed adds original wording/source references, narrow inspected lines, rationale, data/access effects, acceptance, dependencies and remaining investigation. Neither report claims suggested edits were made. Both ask material questions after source inspection and distinguish source, runtime and deployed evidence. A concise example (fictional):

```text
Announcements

REQ-01 - Expired notices
Request: Hide expired notices from the active PACD banner.
Page: PACD dashboard - /pacd/dashboard
Access: Signed-in PACD staff, assigned division only.
Type: Bug report
Finding: The source query does not filter expiry; runtime not checked.
Recommendation: Filter active notices and keep the archive available.
File | Proposed action | Purpose
app/Notices.php | Modify | Fix active filtering
Decision: Keep expired notices in archive - Default applied.
```

The detailed form of that fictional review also includes `Original: “Expired announcements appear on PACD” - requirements.pdf, page 4`, the inspected source range, a proposed filtering acceptance check and a separate browser verification gap. A fictional confirmation summary is:

```text
Announcements
- PACD dashboard - /pacd/dashboard; signed-in PACD staff in their assigned division: Hide expired notices from the active banner and keep them in the archive.
Defaults applied: Keep expired notices in archive.
```

A material question appears in **both** review depths. For example, after inspecting the existing archive:

```text
Where should expired notices remain available?
1. Archive only - Recommended, Default. Preserves existing history without active-banner clutter.
2. Active banner with an Expired label. Keeps visibility but mixes active and expired items.
3. Hide from both views. Removes them from normal navigation.
Custom answer is welcome.
```

If unanswered after a reasonable opportunity, the review records option 1 as **Default applied**. It never records a preselected UI choice as a submitted answer. “Use option 2” later records **Selected by user** and updates acceptance checks. A factual unknown, such as an unreadable PDF line, remains unresolved.

## Follow-ups, saving and planning

These are independent or sequential **agent-chat** examples, using the identified current review:

```text
Show the details.
Summarize only REQ-01 and REQ-04.
Leave account management out and summarize again.
Change REQ-03 to option 2.
Use your recommendations for the questions shown.
Save this review.
Use this reviewed scope with implementation-plan.
Implement REQ-01 and REQ-03.
```

Natural filtering preserves excluded IDs and their source history. The agent explains if an exclusion leaves a required dependency. Answers are reused; a later explicit answer overrides an applied default. “Confirmed” confirms scope, “prepare a plan” permits planning, and an explicit implementation request permits only the identified implementation scope under project rules. “Fix it” concerns established fixes, not every optional recommendation. No review default authorizes edits, emails, commits, pushes or deployment.

Normal review creates no files. “Save this review” or a fresh-session handoff writes `reviewed-requirements.md`, `review-state.json` and an appropriate byte-preserved PDF under a unique `.request-reviews/YYYYMMDDTHHMMSSZ-<unique-id>/` in the target workspace. It preserves revisions and source mappings; an explicit project document path follows that document's ownership instead. Generated runs are Git-ignored by a narrowly scoped rule after safety checks. An interrupted identified run resumes; a changed decision gets a new linked revision. Missing tools or unreadable pages are reported and dependent facts remain unresolved. A saved handoff is reviewed requirements, not an approved implementation plan.

For a new session, point `implementation-plan` at the saved Markdown:

```text
$implementation-plan ".request-reviews/20261122T120000Z-example/reviewed-requirements.md"
```

Replace the example run folder with the actual returned path; Claude Code uses `/implementation-plan`. In the same conversation, “Use this reviewed scope with implementation-plan” passes full recorded requirements, evidence and decisions. That skill must be installed separately and still asks its own phase-sizing and action questions. If unavailable, the full Markdown handoff remains usable later. Optional `bug-investigation` can deepen a defect investigation; `change-report` can describe changes after authorized implementation. Neither is a prerequisite.

### Optional terminal state check

Python 3.11+ can validate a saved ledger's IDs, source coverage, decision provenance, file references and full Markdown handoff. PowerShell from the target application folder; replace `<installed-skill-dir>` and `<run-folder>` with real paths:

```powershell
python '<installed-skill-dir>/scripts/review_state.py' validate '<run-folder>/review-state.json' --check-files --handoff '<run-folder>/reviewed-requirements.md'
```

The `parse` helper checks document-path and option tokens when syntax is ambiguous; use it only with a real accessible document. PowerShell from the target application folder, replacing the installed directory and PDF path:

```powershell
python '<installed-skill-dir>/scripts/review_state.py' parse -- --detailed 'requirements.pdf'
```

`validate` without `--check-files` checks the ledger only; without `--handoff` it does not check Markdown coverage. This helper does not translate requests, inspect PDF pixels, determine root causes, prove access, or judge acceptance semantics. The agent must compare the Markdown handoff with the source and ledger before planning. No terminal helper command is a chat option.
