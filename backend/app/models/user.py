from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, RecordMixin

if TYPE_CHECKING:
    from backend.app.models.activity import Activity
    from backend.app.models.company import Company
    from backend.app.models.opportunity import Opportunity
    from backend.app.models.task import Task


class User(RecordMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True)

    companies: Mapped[list[Company]] = relationship(
        back_populates="owner", passive_deletes="all"
    )
    opportunities: Mapped[list[Opportunity]] = relationship(
        back_populates="owner", passive_deletes="all"
    )
    activities: Mapped[list[Activity]] = relationship(
        back_populates="performed_by", passive_deletes="all"
    )
    tasks: Mapped[list[Task]] = relationship(
        back_populates="assignee", passive_deletes="all"
    )
