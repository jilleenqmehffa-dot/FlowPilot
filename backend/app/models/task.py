from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, RecordMixin
from backend.app.models.enums import TaskStatus

if TYPE_CHECKING:
    from backend.app.models.company import Company
    from backend.app.models.opportunity import Opportunity
    from backend.app.models.user import User


class Task(RecordMixin, Base):
    """A scheduled action; overdue tasks retain their original due_at."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "opportunity_id IS NULL OR company_id IS NOT NULL",
            name="opportunity_requires_company",
        ),
        ForeignKeyConstraint(
            ["opportunity_id", "company_id"],
            ["opportunities.id", "opportunities.company_id"],
            ondelete="RESTRICT",
        ),
    )

    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    assignee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", validate_strings=True),
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    opportunity_id: Mapped[int | None] = mapped_column(BigInteger, index=True)

    assignee: Mapped[User] = relationship(back_populates="tasks")
    company: Mapped[Company | None] = relationship(
        back_populates="tasks", foreign_keys=[company_id]
    )
    opportunity: Mapped[Opportunity | None] = relationship(
        back_populates="tasks", foreign_keys=[opportunity_id]
    )
