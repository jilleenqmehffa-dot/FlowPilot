"""Structured output of the deal-analysis model call."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DealAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    summary: str = Field(description="A concise summary of the current deal situation")
    health: Literal["healthy", "at_risk", "critical"]
    win_probability: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    reasoning: str = Field(description="Reasoning grounded only in the supplied CRM data")
