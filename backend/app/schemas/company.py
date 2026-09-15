from backend.app.schemas.base import Name200, RecordId, RecordRead, SchemaModel


class CompanyBase(SchemaModel):
    name: Name200
    owner_id: RecordId


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(SchemaModel):
    name: Name200 | None = None
    owner_id: RecordId | None = None


class CompanyRead(CompanyBase, RecordRead):
    pass
