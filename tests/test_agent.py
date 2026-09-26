import asyncio

import pytest

import agent


def test_default_provider_is_gemini(monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    model = agent.build_model()
    assert type(model).__name__ == "ChatGoogleGenerativeAI"
    assert model.model.endswith("gemini-3.8-flash")


def test_groq_provider_and_model_override(monkeypatch):
    monkeypatch.setenv("PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("MODEL", raising=False)
    model = agent.build_model()
    assert type(model).__name__ == "ChatGroq"
    assert model.model_name == "openai/gpt-oss-120b"
    monkeypatch.setenv("MODEL", "other-model")
    assert agent.build_model().model_name == "other-model"


def test_unknown_provider(monkeypatch):
    monkeypatch.setenv("PROVIDER", "nope")
    with pytest.raises(SystemExit):
        agent.build_model()


class _FakeAgent:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0

    async def ainvoke(self, request):
        self.calls += 1
        return {"structured_response": self.outputs.pop(0)}


def _patch(monkeypatch, fake):
    class _Client:
        def __init__(self, *_):
            pass

        async def get_tools(self):
            return []

    monkeypatch.setattr(agent, "MultiServerMCPClient", _Client)
    monkeypatch.setattr(agent, "build_model", lambda: None)
    monkeypatch.setattr(agent, "create_agent", lambda **_: fake)


GOOD = {"category": "bug", "priority": "P4", "route": "bug-team", "rationale": "Cosmetic issue."}
BAD = {"category": "nope", "priority": "P4", "route": "bug-team", "rationale": "x"}


def test_retries_once_then_succeeds(monkeypatch):
    fake = _FakeAgent([BAD, GOOD])
    _patch(monkeypatch, fake)
    assert asyncio.run(agent.triage("T-1")) == GOOD
    assert fake.calls == 2


def test_second_failure_is_a_clear_error(monkeypatch):
    fake = _FakeAgent([BAD, BAD])
    _patch(monkeypatch, fake)
    with pytest.raises(RuntimeError, match="failed schema validation twice"):
        asyncio.run(agent.triage("T-1"))
    assert fake.calls == 2
