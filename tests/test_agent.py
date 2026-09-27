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
    with pytest.raises(ValueError, match="Unknown PROVIDER"):
        agent.build_model()


def test_missing_gemini_api_key(monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        agent.build_model()


def test_missing_groq_api_key(monkeypatch):
    monkeypatch.setenv("PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        agent.build_model()


class _FakeAgent:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0

    async def ainvoke(self, request, config=None):
        self.calls += 1
        return self.outputs.pop(0)


def _patch(monkeypatch, fake, captured=None):
    class _Client:
        def __init__(self, *args):
            if captured is not None:
                captured["client_args"] = args

        async def get_tools(self):
            return []

    def _fake_create_agent(**kwargs):
        if captured is not None:
            captured["create_agent_kwargs"] = kwargs
        return fake

    monkeypatch.setattr(agent, "MultiServerMCPClient", _Client)
    monkeypatch.setattr(agent, "build_model", lambda: None)
    monkeypatch.setattr(agent, "create_agent", _fake_create_agent)


GOOD = {"category": "bug", "priority": "P4", "route": "bug-team", "rationale": "Cosmetic issue."}
BAD = {"category": "nope", "priority": "P4", "route": "bug-team", "rationale": "x"}


def test_retries_once_then_succeeds(monkeypatch):
    fake = _FakeAgent([{"structured_response": BAD}, {"structured_response": GOOD}])
    _patch(monkeypatch, fake)
    assert asyncio.run(agent.triage("T-1")) == GOOD
    assert fake.calls == 2


def test_second_failure_is_a_clear_error(monkeypatch):
    fake = _FakeAgent([{"structured_response": BAD}, {"structured_response": BAD}])
    _patch(monkeypatch, fake)
    with pytest.raises(RuntimeError, match="failed schema validation twice"):
        asyncio.run(agent.triage("T-1"))
    assert fake.calls == 2


def test_retries_once_on_missing_structured_response(monkeypatch):
    """A response missing the `structured_response` key (KeyError) is retried,
    same as a schema-validation failure."""
    fake = _FakeAgent([{}, {"structured_response": GOOD}])
    _patch(monkeypatch, fake)
    assert asyncio.run(agent.triage("T-1")) == GOOD
    assert fake.calls == 2


def test_second_missing_structured_response_is_a_clear_error(monkeypatch):
    fake = _FakeAgent([{}, {}])
    _patch(monkeypatch, fake)
    with pytest.raises(RuntimeError, match="failed schema validation twice"):
        asyncio.run(agent.triage("T-1"))
    assert fake.calls == 2


def test_agent_wiring(monkeypatch):
    """create_agent and MultiServerMCPClient must receive the tools, policy
    instructions and structured-output schema the spec calls for."""
    from langchain.agents.structured_output import ToolStrategy

    from schema import TriageDecision

    fake = _FakeAgent([{"structured_response": GOOD}])
    captured = {}
    _patch(monkeypatch, fake, captured)
    asyncio.run(agent.triage("T-1"))

    (connections,) = captured["client_args"]
    assert connections["triage"]["transport"] == "stdio"
    assert connections["triage"]["args"][-1].endswith("mcp/triage_server.py")

    kwargs = captured["create_agent_kwargs"]
    assert kwargs["system_prompt"] == agent.INSTRUCTIONS
    assert kwargs["tools"] == [agent.escalate_to_human]
    assert isinstance(kwargs["response_format"], ToolStrategy)
    assert kwargs["response_format"].schema_specs[0].schema is TriageDecision
