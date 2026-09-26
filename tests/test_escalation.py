"""Escalation gate: real create_agent + HumanInTheLoopMiddleware, scripted fake model."""

import asyncio

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool

import agent

DECISION = {"category": "access", "priority": "P1", "route": "access-team", "rationale": "Team locked out."}
ESCALATE = {"name": "escalate_to_human", "args": {"ticket_id": "T-1044", "reason": "P1 Enterprise"}, "id": "c3"}


class ScriptedModel(BaseChatModel):
    calls: list = []
    step: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        message = AIMessage(content="", tool_calls=[self.calls[self.step]])
        self.step += 1
        return ChatResult(generations=[ChatGeneration(message=message)])


def _run(monkeypatch, escalate, approver):
    executed = []

    @tool
    def get_ticket(ticket_id: str) -> dict:
        """Get a ticket."""
        return {"customer_id": "C-1"}

    @tool
    def get_customer_history(customer_id: str) -> dict:
        """Get a customer."""
        return {"plan": "Enterprise"}

    @tool
    def escalate_to_human(ticket_id: str, reason: str) -> str:
        """Escalate."""
        executed.append(ticket_id)
        return "escalated"

    class _Client:
        def __init__(self, *_):
            pass

        async def get_tools(self):
            return [get_ticket, get_customer_history]

    calls = [
        {"name": "get_ticket", "args": {"ticket_id": "T-1044"}, "id": "c1"},
        {"name": "get_customer_history", "args": {"customer_id": "C-1"}, "id": "c2"},
        *([ESCALATE] if escalate else []),
        {"name": "TriageDecision", "args": DECISION, "id": "c4"},
    ]
    monkeypatch.setattr(agent, "MultiServerMCPClient", _Client)
    monkeypatch.setattr(agent, "escalate_to_human", escalate_to_human)
    monkeypatch.setattr(agent, "build_model", lambda: ScriptedModel(calls=calls))
    return asyncio.run(agent.triage("T-1044", approver)), executed


def test_yes_escalates(monkeypatch):
    asked = []
    decision, executed = _run(monkeypatch, True, lambda action: asked.append(action) or True)
    assert executed == ["T-1044"]
    assert asked[0]["args"]["ticket_id"] == "T-1044"
    assert decision == DECISION


def test_no_does_not_escalate_but_completes(monkeypatch):
    decision, executed = _run(monkeypatch, True, lambda action: False)
    assert executed == []
    assert decision == DECISION


def test_no_pause_when_rule_does_not_fire(monkeypatch):
    def never(_):
        pytest.fail("approver must not be asked")

    decision, executed = _run(monkeypatch, False, never)
    assert executed == [] and decision == DECISION


def test_default_approver_only_yes_counts(monkeypatch):
    for answer, expected in [("yes", True), ("Y", True), ("no", False), ("", False), ("maybe", False)]:
        monkeypatch.setattr("builtins.input", lambda _prompt, a=answer: a)
        assert agent.ask_in_terminal({"args": {"ticket_id": "T-1", "reason": "r"}}) is expected
