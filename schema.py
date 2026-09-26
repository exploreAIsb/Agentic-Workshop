"""The triage decision schema (Epic 1, CAP-1)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Category = Literal["billing", "bug", "access", "performance", "how-to"]
Priority = Literal["P1", "P2", "P3", "P4"]
Route = Literal[
    "billing-team", "bug-team", "access-team", "performance-team", "how-to-team"
]


class TriageDecision(BaseModel):
    """One triage decision: category, priority, route and a one-sentence rationale."""

    model_config = ConfigDict(extra="forbid", strict=True)

    category: Category
    priority: Priority
    route: Route
    rationale: str

    @field_validator("rationale")
    @classmethod
    def _one_line_rationale(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must not be blank")
        if "\n" in value or "\r" in value:
            raise ValueError("rationale must be a single sentence on one line")
        return value
