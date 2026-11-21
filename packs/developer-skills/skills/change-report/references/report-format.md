# Report format

## Brief

Use short role sections with page/route bullets, or page sections with applicable roles beside the page. Choose whichever reduces repetition, unless `--group` fixes the choice. A route must come from inspected code. Use hyphens as list markers and separators. Put non-page changes in a small Configuration, Database or Maintenance section. Omit empty sections and stock introductions.

Illustrative wording only, never evidence for a real project:

**Public**

- **Kiosk - /queue-system:** Visitors choose a service and receive a queue number. Reprint ticket prints the same number without creating another.

## Detailed

Keep the same walkthrough. Under each relevant page or workflow, add one small table per repository when multiple repositories contribute:

| File | Lines | Status | Type | Change |
|---|---|---|---|---|
| `pages/Kiosk.vue` | 84–119 | Modified | Improvement | Print the issued ticket |
| `pages/Kiosk.vue` | 123–141 | Modified | Fix | Reprint the existing ticket |

All paths and numbers above are illustrative. Replace them with inspected evidence. Do not add a Project column. For a rename, show `old/path → new/path` in File. For deletion, show baseline line range as `40–72 old`. Use `—` when a binary, line ending only change, or unavailable line location prevents an exact range.

Status: Added, Modified, Renamed, Deleted. Type: New for absent capability; Improvement for useful change to existing capability; Fix only with reliable expected-behavior evidence; Refactor for structure without intended behavior change; Removal for removed behavior or implementation; Unclear when purpose cannot be established. Added tests may support a Fix rather than a New capability. Split different-purpose ranges in one file into separate rows. Explain rows in plain language, not commit-message fragments.

Detailed reports may end with one shared **Verification and follow-up** section. State each actual check and result as Passed, Failed, Not run or Blocked; distinguish prior records from checks executed now. Include required migration/setup, incomplete scope and concrete recommendations only when supported. Code inspection is source evidence, not runtime proof.
