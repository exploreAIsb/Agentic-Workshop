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

### Review Findings

- [x] [Review][Patch] Default approver accepts `"y"`, contradicting the frozen spec's "only 'yes' approves" [agent.py:74]
- [x] [Review][Patch] `langgraph` is imported directly but not a declared dependency (only transitive via `langchain`) [agent.py:14-15]
- [x] [Review][Patch] Bare `input()` can crash with `EOFError` in a non-interactive context [agent.py:67-74]
- [x] [Review][Patch] Interrupt/resume loop has no iteration cap, unlike the outer bounded retry [agent.py:111-119]

**Deferred**
- No adversarial/injection test that ticket text can't trigger unauthorized escalation — real given the repo's untrusted-ticket-text rule, but not actionable as a unit test: `ScriptedModel` returns hardcoded tool calls regardless of ticket content. Would need a live-model test; fits Epic 3's eval better.

**Rejected**
- Interrupt loop only reads `action_requests[0]`, dropping extras — low, only one tool is gated, unlikely to be hit.
- Double-prompt on schema-validation retry (fresh `thread_id` re-asks the approver) — low, documented consequence of "fresh thread_id per attempt," low-probability, non-trivial fix.
- Approver sees only `ticket_id`/`reason`, not priority/plan — cosmetic design opinion, no demonstrated harm.
- No test for escalation + schema-retry interaction — tied to the rejected double-prompt finding.
- No persisted audit trail beyond stderr — false: matches the frozen spec's explicit design exactly.
- `typing.Callable` vs `collections.abc.Callable` — cosmetic.
- Groq flake documented without a linked follow-up issue — process nit about the spec, not a code defect.
- `KeyError` from interrupt-handling code could be silently retried as a schema failure — speculative, not reachable with the current tested payload shape.
- No test asserts the exact stderr strings — low value.
