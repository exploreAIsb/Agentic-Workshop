---
title: 'The triage agent'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `run_agent.py` has no agent behind it, so no ticket can be triaged (Epic 2 CAP-1 to CAP-4 and CAP-6).

**Approach:** Add `agent.py` exposing `async triage(ticket_id) -> dict`: a `create_agent` agent over the `mcp/triage_server.py` tools (stdio, `langchain-mcp-adapters`), `TRIAGE_POLICY.md` as instructions, `TriageDecision` as structured output, one retry then a clear error, provider chosen by `PROVIDER`/`MODEL`. Ticket text is treated as data.

</frozen-after-approval>

## Implementation Notes

- Structured output uses `ToolStrategy(TriageDecision)`: Groq rejects the default JSON mode when tools are bound.
- Retry: one extra attempt on `ValidationError`/missing structured response, then `RuntimeError`.
- Verified live: T-1042 → billing/P2/billing-team on Gemini and Groq; T-1099 → bug/P4; trace shows `get_ticket` then `get_customer_history` with the returned `customer_id`.
- `run_agent.py` unchanged; `escalate_to_human` is story 2.
- Files: `agent.py`, `tests/test_agent.py`.
