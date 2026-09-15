from typing import Annotated

from pydantic import Field

from backend.app.schemas.base import Email, Name200, RecordId, RecordRead, SchemaModel

Phone = Annotated[str, Field(min_length=1, max_length=50)]


class ContactBase(SchemaModel):
    company_id: RecordId
    name: Name200
    email: Email | None = None
    phone: Phone | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(SchemaModel):
    company_id: RecordId | None = None
    name: Name200 | None = None
    email: Email | None = None
    phone: Phone | None = None


class ContactRead(ContactBase, RecordRead):
    pass
