---
title: 'The triage decision schema'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing defines what a triage decision is, so the Epic 2 agent has no structured output type and the Epic 3 `valid_schema` scorer has nothing to validate against (CAP-1).

**Approach:** Add `schema.py` with a pydantic `TriageDecision` model: category, priority, route as independent enums, plus a one-sentence rationale. Unknown fields, missing fields and out-of-range values are rejected with pydantic's clear `ValidationError`. Route is not checked against category (policy logic belongs to Epic 2).

</frozen-after-approval>

## Implementation Notes

- Rationale rule: non-blank, single line (no line breaks). Sentence count is not enforced; that is judged by Epic 3's rationale judge.
- Files: `schema.py`, `tests/test_schema.py`.
