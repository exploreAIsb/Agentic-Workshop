---
title: 'Human-gated escalation'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The policy says P1 Enterprise tickets escalate to a person, but the agent has no escalation tool and nothing gates it (Epic 2 CAP-5).

**Approach:** Add a local `escalate_to_human` tool to `agent.py`, gated by LangChain's `HumanInTheLoopMiddleware` (with a checkpointer). When the run pauses, `triage(ticket_id, approver)` asks the approver; the default asks yes/no at the terminal, and only "yes" approves. "No" rejects the tool call and the run still completes with its decision. The `approver` parameter lets Epic 3 auto-approve inside the eval only.

</frozen-after-approval>

## Implementation Notes

- The decision schema is read-only and `extra="forbid"`, so escalation is reported on stderr ("Escalated to a person." / "Not escalated."), not as a decision field.
- Each attempt (first and the schema retry) uses a fresh `thread_id`.
- Live: T-1044 on Groq, "yes" → escalated, "no" → not escalated, both complete with access/P1/access-team.
- MLflow 3.x prints harmless `on_interrupt`/`on_resume` tracer callback errors on pause/resume; the trace still records.
- A Groq model flake once produced prose instead of a tool call (400 `output_parse_failed`); not retried, out of scope.
- Files: `agent.py`, `tests/test_escalation.py`, `tests/test_agent.py` (fake agent signature).
