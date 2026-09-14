from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, RecordMixin

if TYPE_CHECKING:
    from backend.app.models.company import Company
    from backend.app.models.opportunity import Opportunity
    from backend.app.models.user import User


class Activity(RecordMixin, Base):
    """A completed customer interaction, with an explicit occurrence time."""

    __tablename__ = "activities"
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

    summary: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    performed_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    opportunity_id: Mapped[int | None] = mapped_column(BigInteger, index=True)

    performed_by: Mapped[User] = relationship(back_populates="activities")
    company: Mapped[Company | None] = relationship(
        back_populates="activities", foreign_keys=[company_id]
    )
    opportunity: Mapped[Opportunity | None] = relationship(
        back_populates="activities", foreign_keys=[opportunity_id]
    )
