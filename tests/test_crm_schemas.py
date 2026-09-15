import unittest
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import ValidationError

from backend.app.models import Company, Opportunity, User
from backend.app.models.enums import OpportunityStage, TaskStatus
from backend.app.schemas import (
    ActivityCreate,
    CompanyRead,
    ContactCreate,
    OpportunityCreate,
    OpportunityRead,
    OpportunityUpdate,
    TaskCreate,
    UserCreate,
    UserRead,
    UserUpdate,
)


class CRMSchemaTests(unittest.TestCase):
    def test_create_schemas_validate_lengths_ids_and_email(self):
        user = UserCreate(name="Owner", email="owner@example.test")
        self.assertEqual(user.email, "owner@example.test")

        invalid_payloads = (
            (UserCreate, {"name": "", "email": "owner@example.test"}),
            (UserCreate, {"name": "Owner", "email": "invalid"}),
            (ContactCreate, {"company_id": 0, "name": "Buyer"}),
        )
        for schema, payload in invalid_payloads:
            with self.subTest(schema=schema.__name__), self.assertRaises(ValidationError):
                schema.model_validate(payload)

    def test_opportunity_constraints_and_defaults(self):
        opportunity = OpportunityCreate(
            name="Deal",
            company_id=1,
            owner_id=2,
            amount=Decimal("123.45"),
        )
        self.assertIs(opportunity.stage, OpportunityStage.NEW)
        self.assertIsNone(opportunity.probability)

        for payload in (
            {"name": "Deal", "company_id": 1, "owner_id": 2, "amount": -1},
            {"name": "Deal", "company_id": 1, "owner_id": 2, "probability": 101},
            {"name": "Deal", "company_id": 1, "owner_id": 2, "amount": "1.999"},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                OpportunityCreate.model_validate(payload)

    def test_activity_and_task_require_timezone_aware_datetimes(self):
        aware = datetime.now(UTC)
        activity = ActivityCreate(
            summary="Discovery call",
            occurred_at=aware,
            performed_by_id=1,
        )
        task = TaskCreate(title="Follow up", assignee_id=1, due_at=aware)
        self.assertEqual(activity.occurred_at, aware)
        self.assertIs(task.status, TaskStatus.TODO)

        with self.assertRaises(ValidationError):
            ActivityCreate(summary="Call", occurred_at=datetime.now(), performed_by_id=1)
        with self.assertRaises(ValidationError):
            TaskCreate(title="Follow up", assignee_id=1, due_at=datetime.now())

        with self.assertRaisesRegex(ValidationError, "company_id is required"):
            ActivityCreate(
                summary="Call",
                occurred_at=aware,
                performed_by_id=1,
                opportunity_id=2,
            )
        with self.assertRaisesRegex(ValidationError, "company_id is required"):
            TaskCreate(title="Follow up", assignee_id=1, due_at=aware, opportunity_id=2)

    def test_update_schemas_support_partial_payloads(self):
        update = OpportunityUpdate(probability=75)
        self.assertEqual(update.model_dump(exclude_unset=True), {"probability": 75})
        self.assertEqual(UserUpdate().model_dump(exclude_unset=True), {})

    def test_read_schemas_are_created_from_orm_objects(self):
        timestamp = datetime.now(UTC)
        user = User(id=1, name="Owner", email="owner@example.test")
        user.created_at = timestamp
        user.updated_at = timestamp
        company = Company(id=2, name="Customer", owner_id=1)
        company.created_at = timestamp
        company.updated_at = timestamp
        opportunity = Opportunity(
            id=3,
            name="Deal",
            company_id=2,
            owner_id=1,
            amount=Decimal("500.00"),
            stage=OpportunityStage.QUALIFIED,
        )
        opportunity.created_at = timestamp
        opportunity.updated_at = timestamp

        self.assertEqual(UserRead.model_validate(user).id, 1)
        self.assertEqual(CompanyRead.model_validate(company).owner_id, 1)
        result = OpportunityRead.model_validate(opportunity)
        self.assertEqual(result.amount, Decimal("500.00"))
        self.assertIs(result.stage, OpportunityStage.QUALIFIED)


if __name__ == "__main__":
    unittest.main()
