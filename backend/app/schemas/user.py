from backend.app.schemas.base import Email, Name200, RecordRead, SchemaModel


class UserBase(SchemaModel):
    name: Name200
    email: Email


class UserCreate(UserBase):
    pass


class UserUpdate(SchemaModel):
    name: Name200 | None = None
    email: Email | None = None


class UserRead(UserBase, RecordRead):
    pass
