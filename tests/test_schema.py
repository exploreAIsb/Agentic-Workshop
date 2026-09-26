import pytest
from pydantic import ValidationError

from schema import TriageDecision

VALID = {
    "category": "billing",
    "priority": "P2",
    "route": "billing-team",
    "rationale": "Double charge puts money at stake, so P2 under the policy.",
}


def test_valid_decision():
    decision = TriageDecision.model_validate(VALID)
    assert decision.category == "billing"
    assert decision.model_dump() == VALID


def test_valid_json():
    import json

    assert TriageDecision.model_validate_json(json.dumps(VALID)).route == "billing-team"


@pytest.mark.parametrize("field", list(VALID))
def test_missing_field(field):
    bad = {k: v for k, v in VALID.items() if k != field}
    with pytest.raises(ValidationError, match=field):
        TriageDecision.model_validate(bad)


@pytest.mark.parametrize(
    "field,value",
    [
        ("category", "refund"),
        ("priority", "P5"),
        ("priority", "p1"),
        ("route", "sales-team"),
        ("rationale", "   "),
        ("rationale", "Line one.\nLine two."),
        ("rationale", 42),
    ],
)
def test_out_of_range_value(field, value):
    with pytest.raises(ValidationError, match=field):
        TriageDecision.model_validate({**VALID, field: value})


def test_extra_structure_rejected():
    with pytest.raises(ValidationError, match="extra"):
        TriageDecision.model_validate({**VALID, "confidence": 0.9})


def test_route_not_tied_to_category():
    # Pairing is policy logic for Epic 2, not a schema constraint.
    assert TriageDecision.model_validate({**VALID, "route": "bug-team"})
