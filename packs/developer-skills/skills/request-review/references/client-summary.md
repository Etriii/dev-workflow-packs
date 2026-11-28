# Client revision summary

Use for `--client` and `--client --detailed`. Render one identified request-review from the current conversation or its full saved handoff. If none is identifiable, request a review first; if ambiguous, ask which. Do not select a new document, investigate the application again, apply new defaults, infer approval or silently change scope. Reuse source wording, request order, exclusions, recorded decisions, evidence limits and unanswered facts. Mark older evidence when it may be stale.

## Wording and layout

Title the output **Revision summary**. A short opening such as “The following revisions describe the proposed deliverables and expected results” is sufficient. Use neutral revision statements, plain professional English and concrete work descriptions. Do not address a client as “you,” write a letter, add conversational commentary, discuss tooling/authorship or claim that a person wrote the document. Preserve original quotations in their source language. Neither client mode adds implementation or sending permission.

Keep each request in its original order, headed `REQ-xx — Short title`. Separate request blocks with Markdown horizontal rules (`---`) and blank lines. Do not replace the blocks with the ordinary review table. Each block contains:

1. **Original request:** verbatim quotation, immediately followed by `— Page 6` for a PDF, using its verified physical page. Omit the filename from this line. If multiple source documents could be confused, identify each source with a short label before its quotations; preserve every quote/page pair for merged requests. For chat use `— Chat feedback`; for Markdown/text use a source label and an inspected section/line when available. Never invent a page; mark `Page not verified` or unreadable wording explicitly. Keep the full source mapping in the underlying review/handoff.
2. **Change type:** Addition, Modification, Removal, Correction, Refactor or Reuse, combining types when necessary. This describes the work, not approval or completion status; it does not change the state schema's type/assessment/readiness values. For already-satisfied requests use Reuse and explain what will be retained rather than inventing work. Preserve excluded/deferred status explicitly rather than presenting it as an included deliverable.
3. **Problem:** one concise paragraph stating the request's underlying issue or need and relevant current behavior. Match the evidence; do not turn a reported issue into a proven cause.
4. **Deliverables:** concrete bullets describing what is planned to change or remain. Retain material roles, access restrictions, historical-data safeguards and dependencies. Keep unconfirmed or conditional work qualified; unavailable facts do not become implementation commitments.
5. **Expected result:** the resulting user-visible or operational behavior, without unsupported benefit claims or implying implementation is complete.
6. **Information needed:** only when necessary, a short direct statement/question identifying the missing fact, source or implementation detail, plus its question reference. For example, “Official monthly report templates — Q-02.” Explain a blocking consequence briefly when it affects scope. Use evidence already recorded; do not delegate agent-owned investigation to the reader or add empty fields.

## Details added during review

Keep the source request separate from solutions added during review. Mark the specific affected deliverable or implementation detail with **(proposed; not specified in the request)** when it is a review default, a developer's answer or an interpretation without recorded client confirmation. A review user's selection is not proof that the client approved it. Only explicit, attributable client evidence establishes client confirmation; do not infer it from silence, a recommendation or the request to produce this summary.

Do not add a “Decisions for confirmation” paragraph or repeat formal labels such as “Team-selected; confirmation pending” below every block. Where proposed details exist, add this note once after all revision blocks and any verification/notes, immediately before the final Q&A:

> Details marked “proposed” were added during review because the original requests did not specify them. Clarify any changes before implementation.

Omit the note when no such details exist. Unknown facts remain concise **Information needed** entries, not defaulted proposals. Keep full provenance in the existing decision record even when the client wording is shorter.

## Detailed version

`--client --detailed` keeps the same wording, fields, source display, proposed markers and short information requests. Add only relevant supporting details beneath each request:

- **Affected routes and files:** a compact `Area | Location | Planned change` table. Separate browser routes from API endpoints; use inspected relative files grouped by repository where needed. Distinguish existing locations from proposed additions/removals. Explicitly mark unverified routes/files and never fabricate them. For jobs, services or configuration, show their actual owners rather than inventing a route.
- **Acceptance checks:** observable checks tied to the deliverables and recorded decisions; do not claim planned checks have passed.
- **Dependencies:** material prerequisites or linked requests when applicable, without repeating the full request.

The ordinary client view omits technical file tables, internal logs and test counts. Both views retain material verification limits and blockers in plain language. Rendering detailed output does not authorize new investigation; missing locations remain unverified unless a separate review is requested.

## Closing questions and answers

Keep **Questions and answers** at the very bottom, following the [complete Q&A rules](review-workflow.md#final-questions-and-answers). Include every recorded question, even resolved, defaulted or out-of-view items, with stable question/request IDs, available options and tradeoffs, recommendation/default when present, and the current answer. Missing source or verification questions remain pending; never fabricate options or answers. If none were raised and none are needed, say so briefly.

Use plain answer wording instead of formal per-request decision paragraphs. For an unanswered applied default, write “No answer received; option 1 was used as the proposed approach.” For a developer's choice, write “Option 1 was chosen during review; not stated in the original request.” For a factual blocker, write “Pending — official template copies are needed.” Preserve the difference between these cases and an explicitly confirmed client answer. A later answer updates the existing record, dependent wording and acceptance checks; keep revision history and do not ask settled questions again.

Client output is a presentation of the review, not the full planning handoff. Saving it needs an explicit save request under the existing artifact rules. “Save this client summary” adds `client-summary.md` alongside the full reviewed requirements, ledger and appropriate source copy in the identified run, using a new revision when required by existing rules. A general “save this review” still preserves the full reviewed requirements and ledger; do not replace them with the client summary or silently remove source filenames from the handoff. An explicit project-document destination follows its existing ownership rules instead.
