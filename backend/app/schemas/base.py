"""Shared types and fields for CRM API schemas."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


RecordId = Annotated[int, Field(gt=0)]
Name200 = Annotated[str, Field(min_length=1, max_length=200)]
Name300 = Annotated[str, Field(min_length=1, max_length=300)]
Email = Annotated[
    str,
    Field(
        min_length=3,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class SchemaModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RecordRead(SchemaModel):
    id: RecordId
    created_at: datetime
    updated_at: datetime
