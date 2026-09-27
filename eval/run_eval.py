"""Evaluate the triage agent over eval/labelled_tickets.csv with MLflow (Epic 3).

Usage: uv run python eval/run_eval.py   (PROVIDER=groq to run the agent on Groq)
"""

import asyncio
import csv
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# One ticket at a time, and no MLflow-level retry: a retry would re-run predict as a second trace.
os.environ.setdefault("MLFLOW_GENAI_EVAL_MAX_WORKERS", "1")
os.environ.setdefault("MLFLOW_GENAI_EVAL_MAX_RETRIES", "0")

import mlflow  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from mlflow.genai.scorers import scorer  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from agent import triage  # noqa: E402
from schema import TriageDecision  # noqa: E402

LABELS = ROOT / "eval" / "labelled_tickets.csv"

RATE_LIMIT_ATTEMPTS = 6

_lock = threading.Lock()
auto_approved = 0


def _is_rate_limit(exc: BaseException) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return "429" in text or "rate limit" in text or "ratelimit" in text or "resource_exhausted" in text


def auto_approve(action: dict) -> bool:
    """Approve every escalation so the eval never waits on a person."""
    global auto_approved
    with _lock:
        auto_approved += 1
    return True


@mlflow.trace(name="triage_ticket", span_type="AGENT")
def predict(ticket_id: str) -> dict:
    """One ticket, one trace: an approved escalation resumes inside this same call.

    Provider rate limits (429) are waited out here, inside the trace, rather than by a retry that
    would start a second trace for the same ticket.
    """
    for attempt in range(1, RATE_LIMIT_ATTEMPTS + 1):
        try:
            return asyncio.run(triage(ticket_id, approver=auto_approve))
        except Exception as exc:
            if not _is_rate_limit(exc) or attempt == RATE_LIMIT_ATTEMPTS:
                raise
            time.sleep(20 * attempt)


@scorer
def valid_schema(outputs) -> bool:
    try:
        TriageDecision.model_validate(outputs)
    except ValidationError:
        return False
    return True


@scorer
def category_match(outputs, expectations) -> bool:
    return isinstance(outputs, dict) and outputs.get("category") == expectations["expected_category"]


@scorer
def priority_match(outputs, expectations) -> bool:
    return isinstance(outputs, dict) and outputs.get("priority") == expectations["expected_priority"]


@scorer
def tool_order(trace) -> bool:
    first = lambda name: min((s.start_time_ns for s in trace.search_spans(name=name)), default=None)  # noqa: E731
    ticket, customer = first("get_ticket"), first("get_customer_history")
    return ticket is not None and customer is not None and ticket < customer


def load_dataset() -> list[dict]:
    with open(LABELS, newline="", encoding="utf-8") as f:
        return [
            {
                "inputs": {"ticket_id": row["ticket_id"]},
                "expectations": {
                    "expected_category": row["expected_category"],
                    "expected_priority": row["expected_priority"],
                },
            }
            for row in csv.DictReader(f)
        ]


def main() -> None:
    load_dotenv()
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("triage-agent")
    mlflow.langchain.autolog()

    result = mlflow.genai.evaluate(
        data=load_dataset(),
        predict_fn=predict,
        scorers=[valid_schema, category_match, priority_match, tool_order],
    )
    for name, value in sorted(result.metrics.items()):
        print(f"{name}: {value:.2f}")
    print(f"escalations auto-approved: {auto_approved}")


if __name__ == "__main__":
    main()
