from typing import Annotated

from pydantic import AwareDatetime, Field, model_validator

from backend.app.models.enums import TaskStatus
from backend.app.schemas.base import Name300, RecordId, RecordRead, SchemaModel

Description = Annotated[str, Field(min_length=1)]


class TaskBase(SchemaModel):
    title: Name300
    description: Description | None = None
    assignee_id: RecordId
    status: TaskStatus = TaskStatus.TODO
    due_at: AwareDatetime
    company_id: RecordId | None = None
    opportunity_id: RecordId | None = None


class TaskCreate(TaskBase):
    @model_validator(mode="after")
    def require_company_for_opportunity(self) -> "TaskCreate":
        if self.opportunity_id is not None and self.company_id is None:
            raise ValueError("company_id is required when opportunity_id is provided")
        return self


class TaskUpdate(SchemaModel):
    title: Name300 | None = None
    description: Description | None = None
    assignee_id: RecordId | None = None
    status: TaskStatus | None = None
    due_at: AwareDatetime | None = None
    company_id: RecordId | None = None
    opportunity_id: RecordId | None = None


class TaskRead(TaskBase, RecordRead):
    pass
