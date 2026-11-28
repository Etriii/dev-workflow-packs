# Request Review

Review informal development feedback or a requirements PDF against the current application. The review preserves original wording and source references, checks current behavior and access, asks focused questions, and produces a categorized review, short scope summary or neutral client revision summary. It does not edit the application by default. See [agent instructions](SKILL.md), [output rules](references/review-workflow.md), [client-summary rules](references/client-summary.md), and the [collection command guide](../../../../docs/SKILL_COMMANDS.md).

Skill responses and generated reports are in English, including for Tagalog or Bisaya requests. Original quotations, code, identifiers, and application content keep their source language when needed for accuracy.

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

These are chat requests, never terminal commands. Open the target application; identify an external related repository naturally if needed. A bare invocation uses clearly supplied requests or an attachment. If there is none, the agent asks for the request and does not select unrelated earlier content. A missing path-like document is an error. Quote file paths with spaces. Options may precede or follow a document in new reviews. Unknown/duplicate flags, competing documents, and `--summary` combined with new input or `--detailed` are invalid. `--client` uses an already identified review; new input and `--summary` cannot be combined with it. A natural “help” request prints these main forms briefly.

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

```text
$request-review --client
```

```text
$request-review --client --detailed
```

Use `/request-review` with the same arguments in Claude Code. Existing accessible `.md` and `.txt` requirements are also accepted for new reviews; attached PDFs work when the host exposes them. A PDF plus additional chat instructions is one review, with both sources mapped. The agent inventories all relevant PDF pages and uses available text extraction, rendering, visual inspection or OCR; unreadable passages remain blockers. `--detailed` changes the report depth only. `--summary` uses an identified recorded review, applies eligible unanswered defaults and does not reassess code. `--client` and `--client --detailed` reuse recorded scope, evidence and answers without investigating again or applying new defaults. If no review or several plausible reviews exist, the agent asks for one or which one. Presentation/depth persists on natural follow-ups until changed; “show the details” in client mode retains client wording. Explicit `--client` selects the ordinary client view, `--client --detailed` selects its detailed view, and `--summary` selects the scope summary. The two client flags work in either order. To review a new document, use the ordinary document invocation first, then request client output.

The review reads application code, guards/policies, tests, configuration and safe local evidence as relevant. It verifies routes, roles and current behavior rather than trusting page names. Ordinary default output is grouped by application area, each beginning with a four-column table: `ID — Request summary | Original request — verbatim | Finding | Recommendation / readiness`. In the original-request cell, every PDF quotation is immediately followed by its filename and physical page: `“Exact source wording.” — requirements.pdf, page 6`. Ordinary default, detailed and saved full reviews use the same placement; client output has its own block layout below. Request headings contain the ID and English summary; application routes appear in page/access details. A differing printed page label is recorded separately. Merged requests retain each original passage with its own source/page citation. Chat quotations end with `— chat feedback`; Markdown/text quotations identify their filename and an inspected section or line when available. An unknown PDF page is explicitly marked `Source page not verified`. Quotations keep their original language; excerpts and omissions are marked, material conditions are retained, and unavailable wording or pages are never invented.

Each finding explains current behavior, its gap or match against the request, and the evidence level and limits. Each recommendation explains proposed behavior, material safeguards and unresolved decisions, with readiness when useful. A status alone is insufficient; an already-satisfied request can stay brief when its matching behavior and verification are clear. Supporting details keyed by ID retain page/access, type, concise file tables and decisions. `--detailed` keeps that overview and adds narrow inspected lines, expanded evidence, rationale, data/access effects, acceptance, dependencies and remaining investigation. Neither report claims suggested edits were made. Both ask material questions after source inspection and distinguish source, runtime and deployed evidence. A concise example (fictional):

**Announcements**

| ID — Request summary | Original request — verbatim | Finding | Recommendation / readiness |
|---|---|---|---|
| REQ-01 — Hide expired notices from the active PACD banner | “Expired notices remain on PACD.” — requirements.pdf, page 4 | The source query does not filter expiry, so expired notices can remain in the active banner. Source inspected; runtime not checked. | Filter active notices and retain archive access. Q-01: Default applied. Ready to plan; browser verification remains pending. |

```text
REQ-01 - Supporting details
Page: PACD dashboard - /pacd/dashboard
Access: Signed-in PACD staff, assigned division only.
Type: Bug report
File | Proposed action | Purpose
app/Notices.php | Proposed modification | Fix active filtering
```

The detailed form keeps the same original quotation, source/page citation and overview, then adds the inspected source range, rationale and a proposed filtering acceptance check. A summary replaces source/file tables with concise category bullets describing intended behavior and route/access restrictions. It retains request IDs and source citations immediately after each request description, for example `REQ-01 — Hide expired notices from the active PACD banner — requirements.pdf, page 4`. It still ends with the complete Q&A described below.

### Requests by change type

Ordinary default, detailed, summary and saved full reviews add a compact **Requests by change type** table near the bottom, after request details, verification and notes and immediately before the final Q&A. The columns contain request IDs only. Each request gets one row in original order; an ID appears in every applicable column on that same row. A fictional example:

| Additions | Revisions | Removals |
|---|---|---|
| REQ-03 | — | — |
| — | REQ-22 | REQ-22 |
| REQ-32 | REQ-32 | — |

This makes mixed changes visible without moving the full requests or ranking their implementation order. Additions introduce capabilities; Revisions change existing behavior, presentation or structure, including corrections/refactors; Removals retire active functionality. Classification follows the reviewed behavior and scope, not merely the request's type field or whether a source file is added/deleted.

Already-satisfied requests with no planned change and excluded/deferred requests are identified on short **No change needed** or **Excluded/deferred** ID lines below the table. Unclear classifications remain on a **Needs classification** line with relevant question references; they are not forced into a column. Missing details do not prevent grouping when the kind of change is clear. Every displayed request is accounted for, and filtered views retain their selected scope. When no included work can be grouped, the review says so rather than inventing rows. Client summaries keep their agreed block layout unless this index is explicitly requested there. No new command, investigation, state schema, approval or file write is introduced.

### Questions, answers and verification needs

Reuse the review's existing questions and decision records. Requests stay in original source order; a request needing input stays in place with its uncertainty and a question reference in the recommendation/readiness cell, such as `Needs clarification — Q-01`, `Needs your verification — Q-02` or `Source needed — Q-03`. Category headings may repeat to preserve that order. New questions use stable `Q-01` IDs; resumed reviews retain their existing decision IDs. No extra input queue or table column is added.

Every default, detailed and summary review ends with **Questions and answers**, after verification, notes and other closing material. It lists all questions raised during that review together, including earlier host prompts, answered questions, applied defaults, and pending requests for facts, sources or user verification. Order entries by affected request order, then question order. Each entry references its request IDs, gives the question, meaningful options with tradeoffs, recommendation/default and rationale when available, and the current answer with provenance. Missing facts have no default; ask for the exact information or evidence needed. Agent-owned investigation stays an evidence limit rather than becoming homework for the user.

For example, a review containing the notice request and a later REQ-02 about an unavailable report template could close as follows. The template request remains in its original position above with `Source needed — Q-02`:

```text
Verification: Notice query inspected; runtime and report-format compliance not verified.
Notes: Changes are proposed scope only; implementation is not authorized.

Requests by change type

| Additions | Revisions | Removals |
|---|---|---|
| — | REQ-01 | — |
| — | REQ-02 | — |

Questions and answers

Q-01 — REQ-01: Where should expired notices remain available?
1. Archive only — Recommended / Default. Preserves history without active-banner clutter.
2. Active banner with an Expired label. Keeps visibility but mixes active and expired items.
3. Hide from both views. Removes them from normal navigation.
Custom answer is welcome.
Rationale: The existing archive already supports retrieval.
Answer: Default applied — option 1; no explicit user answer received after the question was presented and time allowed.

Q-02 — REQ-02: Can you provide the official report template or an accessible copy?
Answer: Pending. The template is needed to verify columns, totals, layout and signature blocks. No factual default applies.
```

The three-question limit applies only to each interactive prompt, never to the final list. A question first presented in the closing section remains pending until there has been a reasonable answer opportunity; recommendations are not silently defaulted before presentation. A preselected UI choice is not a submitted answer. “Q-01: Use option 2” later records **Selected by user**, updates acceptance checks, and retains the prior default in revision history. Providing a factual answer does not prove uninspected evidence. Filtered follow-ups still include the full Q&A, labeling questions about excluded or out-of-view requests without restoring their scope. Resolved questions stay listed with their current answers instead of being asked again; unresolved user questions cannot be left only in notes or replaced by default-only bullets. If none exist, the closing section says so briefly.

## Client revision summary

Use `$request-review --client` after identifying a completed or partial review in the conversation or its full saved handoff. It reads that review's original requests, scope, evidence, questions and answers; it does not start a new investigation, apply defaults, grant approval, send messages, write files or implement changes. If the available review is incomplete or older, its missing information and relevant evidence limits remain visible. No plan-review installation is required to render this view; a separate solution/readiness investigation still uses plan-review when explicitly requested.

The output is titled **Revision summary**, with neutral revision statements instead of a letter addressed to the client. Every request stays in source order with a short `REQ-xx — Title`, separated by horizontal rules and blank lines. Each block contains **Original request**, **Change type**, **Problem**, **Deliverables**, **Expected result**, and a short **Information needed** only when necessary. Change type is Addition, Modification, Removal, Correction, Refactor or Reuse, with combinations allowed; it is separate from approval and completion. Already-satisfied requests explain what will be retained, and excluded/deferred work is labeled rather than promised as an included deliverable.

PDF original wording ends with the verified physical page only, for example `“Exact wording.” — Page 6`. Source labels outside the quotation line disambiguate multiple documents; all original mappings remain in the full review. Chat has `— Chat feedback`; Markdown/text identifies an inspected source section/line when available. Missing pages or unreadable text are marked, never invented. Source language and material role/access, data-preservation and dependency conditions are retained.

Mark the specific detail added during review with **(proposed; not specified in the request)**, including developer-selected answers and applied defaults that lack explicit client confirmation. Do not infer client approval from the review user's answer or from silence. Omit formal per-request “Decisions for confirmation” paragraphs. When proposed details exist, use the one clarification note shown below, after the revision blocks and any verification/notes and before the complete bottom Q&A. Otherwise omit it. Information requests stay short and factual; unresolved facts never become defaults. A fictional excerpt:

```text
Revision summary

The following revisions describe the proposed deliverables and expected results.

REQ-01 — Expired notices

Original request: “Expired notices remain on PACD.” — Page 4
Change type: Correction
Problem: The inspected query does not filter expiry; runtime behavior remains unverified.
Deliverables:
- Filter expired notices from the active PACD banner.
- Keep expired notices in the archive (proposed; not specified in the request).
- Retain the existing PACD role and assigned-division access restrictions.
Expected result: Active banners show current notices while earlier notices remain accessible in the archive.

---

REQ-02 — Official monthly report format

Original request: “Follow the official monthly report template.” — Page 7
Change type: Modification
Problem: Format compliance cannot be verified without the official template.
Deliverables:
- Compare the existing monthly report with the supplied template.
- Revise confirmed format differences once the template is available.
Expected result: The monthly report follows the supplied official format.
Information needed: Official monthly report template — Q-02. Exact format changes remain undetermined.

Details marked “proposed” were added during review because the original requests did not specify them. Clarify any changes before implementation.

Questions and answers

Q-01 — REQ-01: Where should expired notices remain available?
1. Archive only — Recommended / Default. Keeps history outside the active banner.
2. Active with an Expired label. Keeps expired notices in the active view.
Answer: No answer received; option 1 was used as the proposed approach.

Q-02 — REQ-02: Which official template defines the monthly report format?
Answer: Pending — the official template copy is needed. No factual default applies.
```

`$request-review --client --detailed` uses exactly the same wording and proposed markers, adding **Affected routes and files**, **Acceptance checks**, and material **Dependencies** under each request. It reads already recorded locations; missing locations remain unverified instead of triggering a new investigation. For the same fictional notice request, the additions could be:

| Area | Location | Planned change |
|---|---|---|
| Application route | `/pacd/dashboard` | Retain PACD and division access while filtering active notices. |
| Backend file | `app/Notices.php` | Proposed modification to the expiry filter. |

Acceptance checks: Expired notices are absent from the active banner; archive access and assigned-division restrictions remain enforced. These are planned checks, not executed results. Include actual repository owners, proposed additions/removals, jobs or configuration when relevant; do not fabricate locations. Both client views keep material verification limits and information needed, while the ordinary view omits technical file tables, internal logs and test counts.

The complete **Questions and answers** section remains last in both client views, including resolved/defaulted questions, available options and pending source/verification questions. Use plain answer wording while retaining exact provenance in the ledger: “Option 1 was chosen during review; not stated in the original request” for a developer choice, or “No answer received; option 1 was used as the proposed approach” for a default. A verified client answer is identified only when supported by attributable evidence. This wording does not record new client confirmation. Replies by question/request ID resume the same review, update dependent text/checks and preserve answer revisions; a partial review remains partial.

To save this presentation explicitly:

```text
Save this client summary.
```

This adds `client-summary.md` alongside the full `reviewed-requirements.md`, `review-state.json` and appropriate source copy under the existing safe run/revision rules. A general “save this review” still saves the full handoff, and an explicit project-document destination follows its ownership rules. The client summary alone is not a planning handoff. Rendering stops after the revision summary and Q&A; implementation, sending and committing require separate authorization.

## Follow-ups, saving and planning

These are independent or sequential **agent-chat** examples, using the identified current review:

```text
Show the details.
Summarize only REQ-01 and REQ-04.
Leave account management out and summarize again.
Change REQ-03 to option 2.
Q-01: Use option 2.
REQ-02: Use the report template at "official-template.pdf".
Use your recommendations for the questions shown.
Save this review.
Review this scope with plan-review before implementation planning.
Use this reviewed scope with implementation-plan.
Implement REQ-01 and REQ-03.
```

Natural filtering preserves excluded IDs and their source history. The agent explains if an exclusion leaves a required dependency. Answers are reused; a later explicit answer overrides an applied default. “Confirmed” confirms scope, “prepare a plan” permits planning, and an explicit implementation request permits only the identified implementation scope under project rules. “Fix it” concerns established fixes, not every optional recommendation. No review default authorizes edits, emails, commits, pushes or deployment.

Normal review creates no files. “Save this review” or a fresh-session handoff writes `reviewed-requirements.md`, `review-state.json` and an appropriate byte-preserved PDF under a unique `.request-reviews/YYYYMMDDTHHMMSSZ-<unique-id>/` in the target workspace. It preserves revisions and source mappings; an explicit project document path follows that document's ownership instead. Generated runs are Git-ignored by a narrowly scoped rule after safety checks. An interrupted identified run resumes; a changed decision gets a new linked revision. Missing tools or unreadable pages are reported and dependent facts remain unresolved. A saved handoff is reviewed requirements, not an approved implementation plan.

For a client-facing solution and readiness review before planning, optionally point `plan-review` at the full saved Markdown in a new session:

```text
$plan-review ".request-reviews/20261122T120000Z-example/reviewed-requirements.md"
```

It explains each request, proposed solution, work to plan, rationale and expected benefit, and offers `--detailed` and a later `--summary` for client communication. In the same conversation, “Review this scope with plan-review before implementation planning” passes the full current review. This step is optional and does not create the implementation plan or authorize implementation.

For the implementation plan, point `implementation-plan` at the saved Markdown and include any plan-review findings:

```text
$implementation-plan ".request-reviews/20261122T120000Z-example/reviewed-requirements.md"
```

Replace the example run folder with the actual returned path; Claude Code uses `/plan-review` or `/implementation-plan` respectively. In the same conversation, “Use this reviewed scope with implementation-plan” passes full recorded requirements, evidence, decisions and any plan-review findings. These skills must be installed separately; implementation-plan still asks its own phase-sizing and action questions. If unavailable, the full Markdown handoff remains usable later. Optional `bug-investigation` can deepen a defect investigation; `change-report` can describe changes after authorized implementation. Neither is a prerequisite.

### Optional terminal state check

Python 3.11+ can validate a saved ledger's IDs, source coverage, decision provenance, file references and full Markdown handoff. PowerShell from the target application folder; replace `<installed-skill-dir>` and `<run-folder>` with real paths:

```powershell
python '<installed-skill-dir>/scripts/review_state.py' validate '<run-folder>/review-state.json' --check-files --handoff '<run-folder>/reviewed-requirements.md'
```

The `parse` helper checks document-path and option tokens when syntax is ambiguous. For a document invocation, use a real accessible document. PowerShell from the target application folder, replacing the installed directory and PDF path:

```powershell
python '<installed-skill-dir>/scripts/review_state.py' parse -- --detailed 'requirements.pdf'
```

Client syntax can be checked without a document path, from the same folder and with the same installed-directory replacement:

```powershell
python '<installed-skill-dir>/scripts/review_state.py' parse -- --client --detailed
```

This checks syntax only; it cannot identify the conversation's review or generate client output. It accepts either client-flag order and rejects the conflicting inputs described above.

`validate` without `--check-files` checks the ledger only; without `--handoff` it does not check Markdown coverage. This helper does not translate requests, inspect PDF pixels, determine root causes, prove access, or judge acceptance semantics. The agent must compare the Markdown handoff with the source and ledger before planning. No terminal helper command is a chat option.
