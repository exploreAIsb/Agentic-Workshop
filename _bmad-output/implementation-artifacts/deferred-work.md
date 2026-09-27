## Deferred from: code review of story-2-human-gated-escalation (2026-09-26)

- No adversarial/injection test that ticket text can't trigger unauthorized escalation. Real given the repo's rule that ticket text is untrusted data, and this story adds a new tool-invoking capability (`escalate_to_human`). Not actionable as a unit test today: `tests/test_escalation.py`'s `ScriptedModel` returns hardcoded tool calls regardless of ticket content, so it can't exercise prompt-injection resistance. Would need a live-model test — fits Epic 3's eval better than this story's unit tests.
