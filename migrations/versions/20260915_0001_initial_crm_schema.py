"""Create the initial CRM schema.

Revision ID: 20260915_0001
Revises:
Create Date: 2026-09-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260915_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

opportunity_stage = postgresql.ENUM(
    "NEW",
    "QUALIFIED",
    "PROPOSAL",
    "NEGOTIATION",
    "WON",
    "LOST",
    name="opportunity_stage",
    create_type=False,
)
task_status = postgresql.ENUM(
    "TODO",
    "IN_PROGRESS",
    "DONE",
    "CANCELED",
    name="task_status",
    create_type=False,
)


def record_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    opportunity_stage.create(bind, checkfirst=False)
    task_status.create(bind, checkfirst=False)

    op.create_table(
        "users",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        *record_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        *record_columns(),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_companies_owner_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
    )
    op.create_index("ix_companies_owner_id", "companies", ["owner_id"])

    op.create_table(
        "contacts",
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        *record_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_contacts_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_contacts"),
    )
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])

    op.create_table(
        "opportunities",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("stage", opportunity_stage, server_default="NEW", nullable=False),
        sa.Column("probability", sa.SmallInteger(), nullable=True),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        *record_columns(),
        sa.CheckConstraint("amount >= 0", name="ck_opportunities_amount_nonnegative"),
        sa.CheckConstraint(
            "probability BETWEEN 0 AND 100",
            name="ck_opportunities_probability_range",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_opportunities_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_opportunities_owner_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_opportunities"),
        sa.UniqueConstraint("id", "company_id", name="uq_opportunities_id_company_id"),
    )
    op.create_index("ix_opportunities_company_id", "opportunities", ["company_id"])
    op.create_index("ix_opportunities_owner_id", "opportunities", ["owner_id"])

    op.create_table(
        "activities",
        sa.Column("summary", sa.String(length=300), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_by_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("opportunity_id", sa.BigInteger(), nullable=True),
        *record_columns(),
        sa.CheckConstraint(
            "opportunity_id IS NULL OR company_id IS NOT NULL",
            name="ck_activities_opportunity_requires_company",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_activities_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id", "company_id"],
            ["opportunities.id", "opportunities.company_id"],
            name="fk_activities_opportunity_id_opportunities",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_id"],
            ["users.id"],
            name="fk_activities_performed_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_activities"),
    )
    op.create_index("ix_activities_company_id", "activities", ["company_id"])
    op.create_index("ix_activities_opportunity_id", "activities", ["opportunity_id"])
    op.create_index("ix_activities_performed_by_id", "activities", ["performed_by_id"])

    op.create_table(
        "tasks",
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_id", sa.BigInteger(), nullable=False),
        sa.Column("status", task_status, server_default="TODO", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("opportunity_id", sa.BigInteger(), nullable=True),
        *record_columns(),
        sa.CheckConstraint(
            "opportunity_id IS NULL OR company_id IS NOT NULL",
            name="ck_tasks_opportunity_requires_company",
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name="fk_tasks_assignee_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_tasks_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id", "company_id"],
            ["opportunities.id", "opportunities.company_id"],
            name="fk_tasks_opportunity_id_opportunities",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
    )
    op.create_index("ix_tasks_assignee_id", "tasks", ["assignee_id"])
    op.create_index("ix_tasks_company_id", "tasks", ["company_id"])
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])
    op.create_index("ix_tasks_opportunity_id", "tasks", ["opportunity_id"])


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("activities")
    op.drop_table("opportunities")
    op.drop_table("contacts")
    op.drop_table("companies")
    op.drop_table("users")

    bind = op.get_bind()
    task_status.drop(bind, checkfirst=False)
    opportunity_stage.drop(bind, checkfirst=False)
