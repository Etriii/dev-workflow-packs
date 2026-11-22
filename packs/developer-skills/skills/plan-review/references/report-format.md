# Plan-review report format

## Default review

Group by the client's familiar application areas or roles, not by code layer. Keep source request IDs when supplied; otherwise use clear request titles. For each distinct request, show:

- **Request:** The behavior or outcome sought, with important conditions.
- **Current finding:** What the available evidence confirms, what already works, and what remains unknown. Omit this line only when it adds nothing.
- **Proposed solution:** The recommended behavior, including a narrower or no-change option when justified.
- **Work to plan:** The concrete application work or investigation needed. Do not imply it has been implemented.
- **Why and expected benefit:** How the solution addresses the request and who should benefit. Mark projected benefits as expected, not measured.
- **Decision or blocker:** Only a material client choice, missing fact or prerequisite. Label recommendations and previously applied defaults honestly.

Give a verified application-relative page URL when a viewable route is known; include access restrictions. If a route cannot be verified, say so. For non-page work, name the job, integration or configuration instead. A complete plan adds a compact phase reference for each request; reviewed requirements without phases say phase assignment is pending. Do not repeat generic status labels or empty fields. End with **Overall summary**: what is recommended, what is already satisfied or excluded, what blocks planning, and the next authorized step. Keep this section short enough to forward with the report.

## Detailed review

Keep the same readable request sections and conclusions. Add source wording or references when needed for traceability, exact inspected relative file paths and lines, evidence level, mapping of request IDs to plan phases, dependencies and ordering defects, meaningful alternatives and tradeoffs, access/data effects, observable acceptance checks, and verification limits. A table may compact repeated mappings; it must not replace plain-language solution and value. Distinguish a planned check from one actually run. For proposed new files or uninspected lines, do not invent line numbers. Finish with the same overall summary.

## Client summary (`--summary`)

Use the identified review without new investigation. State the reviewed source and date or say the evidence is current-conversation only. Group by the same client-facing categories. For each included request, give the request, recommended solution, planned outcome and reason in short prose. Retain material limits, access conditions, proposed decisions and blockers. State whether anything is already satisfied, deferred or excluded. End with **Decision needed** and **Next step**; if no decision is open, say the scope is ready for implementation planning. Do not claim a reviewed scope is approved unless approval was explicitly given. Do not include machine paths, source tables, speculative delivery dates or unverified claims. Mark prior evidence that may be stale. The summary is copyable client communication, not permission to send it or implement it.

Illustrative wording only, never evidence for a real application:

**Queue tickets**

- **Request:** Let visitors reprint an issued ticket without receiving a new number.
- **Current finding:** The current ticket view has a print action; preservation of the issued number after refresh is unverified.
- **Proposed solution:** Reprint the stored ticket from the existing queue page at `/queue-system`.
- **Work to plan:** Confirm ticket persistence, then reuse the saved ticket for reprints and add a check that no new queue entry is created.
- **Why and expected benefit:** Visitors can replace a lost paper ticket while retaining their place in the queue.
- **Decision or blocker:** Confirm how long an issued ticket remains available for reprint.

**Overall summary:** The reprint flow is reasonable to plan after ticket retention is decided. Persistence still needs verification; no implementation has been approved or completed.
