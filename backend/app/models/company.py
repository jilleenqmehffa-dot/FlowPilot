from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, RecordMixin

if TYPE_CHECKING:
    from backend.app.models.activity import Activity
    from backend.app.models.contact import Contact
    from backend.app.models.opportunity import Opportunity
    from backend.app.models.task import Task
    from backend.app.models.user import User


class Company(RecordMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(200))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )

    owner: Mapped[User] = relationship(back_populates="companies")
    contacts: Mapped[list[Contact]] = relationship(
        back_populates="company", passive_deletes="all"
    )
    opportunities: Mapped[list[Opportunity]] = relationship(
        back_populates="company", passive_deletes="all"
    )
    activities: Mapped[list[Activity]] = relationship(
        back_populates="company",
        foreign_keys="Activity.company_id",
        passive_deletes="all",
    )
    tasks: Mapped[list[Task]] = relationship(
        back_populates="company",
        foreign_keys="Task.company_id",
        passive_deletes="all",
    )
