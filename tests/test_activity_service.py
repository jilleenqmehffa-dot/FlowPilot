import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from backend.app.core.exceptions import InvalidActivityError, ResourceNotFoundError
from backend.app.models import Activity, Company, Opportunity, User
from backend.app.models.enums import OpportunityStage
from backend.app.repositories import ActivityRepository
from backend.app.schemas import ActivityCreate, ActivityUpdate
from backend.app.services import ActivityService


class ActivityServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ActivityService(MagicMock(spec=Session))
        self.service.activities = MagicMock(spec=ActivityRepository)
        self.service.companies = MagicMock()
        self.service.opportunities = MagicMock()
        self.service.users = MagicMock()
        self.company = Company(id=10, name="Customer", owner_id=20)
        self.user = User(id=20, name="Owner", email="owner@example.test")
        self.opportunity = Opportunity(
            id=30,
            name="Deal",
            company_id=10,
            owner_id=20,
            stage=OpportunityStage.NEW,
        )
        self.activity = Activity(
            id=40,
            summary="Discovery call",
            occurred_at=datetime.now(UTC) - timedelta(minutes=5),
            performed_by_id=20,
            company_id=10,
            opportunity_id=30,
        )
        self.service.companies.get.return_value = self.company
        self.service.opportunities.get.return_value = self.opportunity
        self.service.users.get.return_value = self.user
        self.service.activities.get_for_update.return_value = self.activity
        self.service.activities.update.side_effect = self._apply_update

    @staticmethod
    def _apply_update(activity, data):
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(activity, field, value)
        return activity

    def create_data(self, **changes) -> ActivityCreate:
        values = {
            "summary": "Discovery call",
            "occurred_at": datetime.now(UTC) - timedelta(minutes=1),
            "performed_by_id": 20,
            "company_id": 10,
            "opportunity_id": 30,
        }
        values.update(changes)
        return ActivityCreate(**values)

    def test_create_validates_real_associations_and_uses_repository(self):
        data = self.create_data()
        self.service.activities.create.return_value = self.activity

        result = self.service.create_activity(data)

        self.assertIs(result, self.activity)
        self.service.users.get.assert_called_once_with(20)
        self.service.companies.get.assert_called_once_with(10)
        self.service.opportunities.get.assert_called_once_with(30)
        self.service.activities.create.assert_called_once_with(data)

    def test_create_rejects_missing_associations(self):
        cases = (
            ("users", "user 20"),
            ("companies", "company 10"),
            ("opportunities", "opportunity 30"),
        )
        for repository_name, message in cases:
            with self.subTest(repository=repository_name):
                self.setUp()
                getattr(self.service, repository_name).get.return_value = None
                with self.assertRaisesRegex(ResourceNotFoundError, message):
                    self.service.create_activity(self.create_data())
                self.service.activities.create.assert_not_called()

    def test_create_rejects_company_opportunity_mismatch_and_future_time(self):
        self.opportunity.company_id = 11
        with self.assertRaisesRegex(InvalidActivityError, "does not belong"):
            self.service.create_activity(self.create_data())

        with self.assertRaisesRegex(InvalidActivityError, "future"):
            self.service.create_activity(
                self.create_data(occurred_at=datetime.now(UTC) + timedelta(minutes=1))
            )

    def test_get_activity_uses_detail_query_and_raises_when_missing(self):
        self.service.activities.get_detail.return_value = self.activity
        self.assertIs(self.service.get_activity(40), self.activity)

        self.service.activities.get_detail.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, "activity 41"):
            self.service.get_activity(41)

    def test_update_revalidates_changed_associations(self):
        new_company = Company(id=11, name="Other", owner_id=20)
        self.service.companies.get.return_value = new_company

        with self.assertRaisesRegex(InvalidActivityError, "does not belong"):
            self.service.update_activity(40, ActivityUpdate(company_id=11))
        self.service.activities.update.assert_not_called()

        self.service.opportunities.get.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, "opportunity 31"):
            self.service.update_activity(40, ActivityUpdate(opportunity_id=31))

        self.service.users.get.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, "user 21"):
            self.service.update_activity(40, ActivityUpdate(performed_by_id=21))

    def test_update_allows_clearing_optional_links_and_notes(self):
        result = self.service.update_activity(
            40,
            ActivityUpdate(opportunity_id=None, company_id=None, notes=None),
        )

        self.assertIsNone(result.opportunity_id)
        self.assertIsNone(result.company_id)
        self.assertIsNone(result.notes)

    def test_update_rejects_null_required_fields(self):
        for field in ("summary", "occurred_at", "performed_by_id"):
            with self.subTest(field=field), self.assertRaisesRegex(
                InvalidActivityError, f"{field} cannot be null"
            ):
                self.service.update_activity(40, ActivityUpdate(**{field: None}))

    def test_list_delegates_filters_and_pagination(self):
        self.service.activities.list_filtered.return_value = [self.activity]

        result = self.service.list_activities(
            company_id=10,
            opportunity_id=30,
            performed_by_id=20,
            offset=5,
            limit=25,
        )

        self.assertEqual(result, [self.activity])
        self.service.activities.list_filtered.assert_called_once_with(
            company_id=10,
            opportunity_id=30,
            performed_by_id=20,
            offset=5,
            limit=25,
        )

    def test_delete_uses_locked_lookup_and_repository(self):
        self.service.delete_activity(40)

        self.service.activities.get_for_update.assert_called_once_with(40)
        self.service.activities.delete.assert_called_once_with(self.activity)


if __name__ == "__main__":
    unittest.main()
