## Deferred from: code review of story-2-human-gated-escalation (2026-09-26)

- No adversarial/injection test that ticket text can't trigger unauthorized escalation. Real given the repo's rule that ticket text is untrusted data, and this story adds a new tool-invoking capability (`escalate_to_human`). Not actionable as a unit test today: `tests/test_escalation.py`'s `ScriptedModel` returns hardcoded tool calls regardless of ticket content, so it can't exercise prompt-injection resistance. Would need a live-model test — fits Epic 3's eval better than this story's unit tests.

## Deferred from: code review of story-1-the-eval-run-and-the-four-code-scorers (2026-09-26)

- `predict()`'s rate-limit retry loop (`eval/run_eval.py`) has zero test coverage. It's the load-bearing mechanism keeping one MLflow trace per ticket (per the story's own Implementation Notes: "Provider 429s are waited out inside `predict` instead" of a retry that would start a second trace). No test calls `predict`; a broken retry would only surface during a live ~20-minute paid run against Groq/Gemini, not in `pytest`. A meaningful test needs scaffolding: stub `agent.triage` to raise a rate-limit-shaped exception once then succeed, plus a faked `time.sleep` to avoid a slow test.
