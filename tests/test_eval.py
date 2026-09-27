import importlib.util
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("run_eval", Path(__file__).resolve().parent.parent / "eval" / "run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)

GOOD = {"category": "billing", "priority": "P2", "route": "billing-team", "rationale": "Money at stake."}
EXPECT = {"expected_category": "billing", "expected_priority": "P2"}


def _trace(**starts):
    def search_spans(name):
        return [SimpleNamespace(start_time_ns=starts[name])] if name in starts else []

    return SimpleNamespace(search_spans=search_spans)


def test_dataset_covers_all_20_tickets():
    data = run_eval.load_dataset()
    assert len(data) == 20
    assert data[0] == {"inputs": {"ticket_id": "T-1042"}, "expectations": EXPECT}


def test_valid_schema():
    assert run_eval.valid_schema(outputs=GOOD) is True
    assert run_eval.valid_schema(outputs={**GOOD, "priority": "P9"}) is False
    assert run_eval.valid_schema(outputs={**GOOD, "extra": 1}) is False
    assert run_eval.valid_schema(outputs=None) is False


def test_category_and_priority_match():
    assert run_eval.category_match(outputs=GOOD, expectations=EXPECT) is True
    assert run_eval.category_match(outputs={**GOOD, "category": "bug"}, expectations=EXPECT) is False
    assert run_eval.category_match(outputs=None, expectations=EXPECT) is False
    assert run_eval.priority_match(outputs=GOOD, expectations=EXPECT) is True
    assert run_eval.priority_match(outputs={**GOOD, "priority": "P1"}, expectations=EXPECT) is False


def test_tool_order():
    assert run_eval.tool_order(trace=_trace(get_ticket=1, get_customer_history=2)) is True
    assert run_eval.tool_order(trace=_trace(get_ticket=5, get_customer_history=2)) is False
    assert run_eval.tool_order(trace=_trace(get_ticket=1)) is False
    assert run_eval.tool_order(trace=_trace()) is False


def test_auto_approve_counts():
    before = run_eval.auto_approved
    assert run_eval.auto_approve({"args": {}}) is True
    assert run_eval.auto_approved == before + 1


def test_rate_limit_detection():
    assert run_eval._is_rate_limit(Exception("Error code: 429 - rate_limit_exceeded"))
    assert not run_eval._is_rate_limit(ValueError("bad output"))
