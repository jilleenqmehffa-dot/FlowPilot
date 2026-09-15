"""Generic synchronous CRUD operations shared by model repositories."""

from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class BaseRepository(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    """Reusable CRUD operations; transaction commits remain the caller's job."""

    model: type[ModelT]
    max_page_size = 100

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, record_id: int) -> ModelT | None:
        return self.session.get(self.model, record_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        if not 1 <= limit <= self.max_page_size:
            raise ValueError(f"limit must be between 1 and {self.max_page_size}")

        statement = select(self.model).order_by(self.model.id).offset(offset).limit(limit)
        return list(self.session.scalars(statement).all())

    def create(self, data: CreateSchemaT) -> ModelT:
        instance = self.model(**data.model_dump())
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def update(self, instance: ModelT, data: UpdateSchemaT) -> ModelT:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        self.session.delete(instance)
        self.session.flush()
