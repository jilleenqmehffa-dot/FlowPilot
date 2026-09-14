from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.enums import OpportunityStage, TaskStatus


class RecordMixin:
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


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


class Contact(RecordMixin, Base):
    __tablename__ = "contacts"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))

    company: Mapped[Company] = relationship(back_populates="contacts")


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
    # Only this relationship writes opportunity_id; company writes company_id.
    # The composite FK checks that the two explicit assignments agree.
    opportunity: Mapped[Opportunity | None] = relationship(
        back_populates="activities", foreign_keys=[opportunity_id]
    )


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
