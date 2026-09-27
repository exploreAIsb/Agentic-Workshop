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
