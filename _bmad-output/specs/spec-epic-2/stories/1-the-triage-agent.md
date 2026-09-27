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

### Review Findings

- [x] [Review][Patch] Missing API keys aren't validated — `GROQ_API_KEY`/`GEMINI_API_KEY` pass through as `None` to the provider SDK instead of a clear error [agent.py:41,44]
- [x] [Review][Patch] `create_agent`/`MultiServerMCPClient` wiring has zero assertions — test fakes discard all constructor args/kwargs, so a regression in tools/system_prompt/response_format wiring ships silently [tests/test_agent.py:44-54]
- [x] [Review][Patch] `KeyError` retry branch (missing `structured_response`) is never exercised by a test [tests/test_agent.py:34-41]
- [x] [Review][Patch] `SystemExit` for an unknown `PROVIDER` won't be caught by `except Exception` — inconsistent with the rest of `triage()`'s error contract [agent.py:36]

**Rejected**
- `MultiServerMCPClient` never closed — false: no `close`/`aclose` method exists; the library manages sessions per-call internally.
- Retry doesn't catch broader exceptions (network/API errors) — false: spec explicitly scopes retry to `ValidationError`/missing structured response only, matching the code.
- `escalate_to_human` referenced in the injected policy text with no such tool bound — low, rejected: the model can't invoke an unbound tool; becomes moot once story 2 adds it.
- New imports without a `pyproject.toml` change — false: dependencies were already added in story 1.1.
- `TRIAGE_POLICY.md` read at import time can crash import — low, rejected: required, checked-in, read-only file, unlikely to go missing.
- Groq backup-agent default model reuses the judge's default — low/cosmetic, no demonstrated harm.
- Spec has no AC-to-test capability mapping — rejected (fix would mean editing the spec under review).
