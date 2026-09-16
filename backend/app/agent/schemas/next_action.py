"""Structured output of the next-action model call."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NextAction(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str = Field(description="Short action title")
    description: str = Field(description="Specific instructions for completing the action")
    rationale: str = Field(description="Why this is the best next action")
    priority: Literal["low", "medium", "high", "urgent"]
    due_in_days: int = Field(ge=0, le=30)
    suggested_owner_id: int | None = Field(
        default=None,
        description="CRM user id only when supported by the supplied context",
    )
