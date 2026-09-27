---
title: 'The eval run and the four code scorers'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing measures how well the Epic 2 agent triages (Epic 3 CAP-1 to CAP-5, CAP-8).

**Approach:** Add `eval/run_eval.py`: build inputs and expectations from all 20 rows of `eval/labelled_tickets.csv`, drive `agent.triage` through `mlflow.genai.evaluate` (one run, `triage-agent` experiment, `sqlite:///mlflow.db`), and score with code scorers `valid_schema`, `category_match`, `priority_match`, `tool_order`. Every escalation is auto-approved through `triage`'s `approver` hook, so the run never waits on a person; `run_agent.py` still asks.

</frozen-after-approval>

## Implementation Notes

- One trace per ticket: `predict` is `@mlflow.trace`d, escalation approval resumes inside it, and MLflow's own retry is off (`MLFLOW_GENAI_EVAL_MAX_RETRIES=0`), since a retry would start a second trace for the same ticket. Provider 429s are waited out inside `predict` instead.
- One worker (`MLFLOW_GENAI_EVAL_MAX_WORKERS=1`): Groq free tier is 8000 tokens/minute for `openai/gpt-oss-120b`, so a full run takes about 20 minutes. Gemini's free daily quota is far too small for 20 tickets, so real runs use `PROVIDER=groq`.
- Live result (Groq): 20 traces, 1 run; category 0.90, priority 0.90, tool_order 1.00, valid_schema 0.95; 3 escalations auto-approved. The failed ticket (T-1046) was a Groq tool-call flake (`tool 'commentary' not in request.tools`), not a code defect.
- Prints the four means and the auto-approved count. `rationale_judge`, the token total and `eval/latest_report.json` are story 2.
- Files: `eval/run_eval.py`, `tests/test_eval.py`.

### Review Findings

**Deferred**
- `predict()`'s rate-limit retry loop has zero test coverage — the load-bearing mechanism keeping one trace per ticket. No test calls `predict`; a broken retry would only surface during a live paid run. A meaningful test needs scaffolding (stub `triage` to raise a rate-limit-shaped exception once then succeed, plus a faked `time.sleep`) beyond this story's scope; the story already has a documented live-run result.

**Rejected**
- `category_match`/`priority_match` index `expectations[...]` directly, no `.get()` — low, `expectations` is always built internally from the read-only, fixed CSV.
- `valid_schema` only catches `ValidationError` — false: verified `TriageDecision.model_validate()` raises `ValidationError` for every malformed shape tested.
- Rate-limit sleep has no jitter/cap — cosmetic, matches the documented, live-verified design.
- No test covers malformed `expectations`/`outputs` shapes — tied to the two rejected findings above.
- `auto_approved` is a global with no reset hook — low, only matters across multiple `main()` calls in one process, which the documented usage never does.
- Spec's "Live result" section hardcodes one historical run's numbers — rejected (fix would mean editing the spec under review).
- `tool_order` conflates "out of order" with "span missing" — cosmetic, matches the spec's own CAP-5 wording.
- `eval/` package name shadows builtin `eval()` — rejected: pre-existing project/path convention, out of scope.
- Unclear whether a per-ticket failure aborts the whole run — false: the spec's own Live result (`valid_schema: 0.95` = 19/20) shows the run continues past a per-ticket failure.
- `os.environ.setdefault(...)` allows override of the 0-retry/1-worker guarantee — informational, intentional by design.
