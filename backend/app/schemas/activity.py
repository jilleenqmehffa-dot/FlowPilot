from datetime import datetime
from typing import Annotated

from pydantic import AwareDatetime, Field, model_validator

from backend.app.schemas.base import Name300, RecordId, RecordRead, SchemaModel

Notes = Annotated[str, Field(min_length=1)]


class ActivityBase(SchemaModel):
    summary: Name300
    notes: Notes | None = None
    occurred_at: AwareDatetime
    performed_by_id: RecordId
    company_id: RecordId | None = None
    opportunity_id: RecordId | None = None


class ActivityCreate(ActivityBase):
    @model_validator(mode="after")
    def require_company_for_opportunity(self) -> "ActivityCreate":
        if self.opportunity_id is not None and self.company_id is None:
            raise ValueError("company_id is required when opportunity_id is provided")
        return self


class ActivityUpdate(SchemaModel):
    summary: Name300 | None = None
    notes: Notes | None = None
    occurred_at: AwareDatetime | None = None
    performed_by_id: RecordId | None = None
    company_id: RecordId | None = None
    opportunity_id: RecordId | None = None


class ActivityRead(ActivityBase, RecordRead):
    pass
