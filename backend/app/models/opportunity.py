from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, RecordMixin
from backend.app.models.enums import OpportunityStage

if TYPE_CHECKING:
    from backend.app.models.activity import Activity
    from backend.app.models.company import Company
    from backend.app.models.task import Task
    from backend.app.models.user import User


class Opportunity(RecordMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_nonnegative"),
        CheckConstraint("probability BETWEEN 0 AND 100", name="probability_range"),
        # Required target key for the company-consistent composite foreign keys.
        UniqueConstraint("id", "company_id", name="uq_opportunities_id_company_id"),
    )

    name: Mapped[str] = mapped_column(String(200))
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    stage: Mapped[OpportunityStage] = mapped_column(
        Enum(OpportunityStage, name="opportunity_stage", validate_strings=True),
        default=OpportunityStage.NEW,
        server_default=OpportunityStage.NEW.value,
    )
    probability: Mapped[int | None] = mapped_column(SmallInteger)
    expected_close_date: Mapped[date | None] = mapped_column(Date)

    company: Mapped[Company] = relationship(back_populates="opportunities")
    owner: Mapped[User] = relationship(back_populates="opportunities")
    activities: Mapped[list[Activity]] = relationship(
        back_populates="opportunity",
        foreign_keys="Activity.opportunity_id",
        passive_deletes="all",
    )
    tasks: Mapped[list[Task]] = relationship(
        back_populates="opportunity",
        foreign_keys="Task.opportunity_id",
        passive_deletes="all",
    )
