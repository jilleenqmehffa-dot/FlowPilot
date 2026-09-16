"""Structured CRM context passed to the deal-analysis model."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from backend.app.models.enums import OpportunityStage, TaskStatus


class ActivityContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    summary: str
    notes: str | None
    occurred_at: datetime
    performed_by_id: int


class TaskContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    description: str | None
    status: TaskStatus
    due_at: datetime
    assignee_id: int


class CRMContext(BaseModel):
    """A compact, serializable snapshot of one deal and its customer history."""

    model_config = ConfigDict(frozen=True)

    opportunity_id: int
    opportunity_name: str
    company_id: int
    company_name: str
    owner_id: int
    owner_name: str
    amount: Decimal | None
    stage: OpportunityStage
    probability: int | None
    expected_close_date: date | None
    recent_activities: tuple[ActivityContext, ...]
    open_tasks: tuple[TaskContext, ...]
