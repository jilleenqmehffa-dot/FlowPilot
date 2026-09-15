import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    InvalidOpportunityTransitionError,
    OpportunityOwnerConflictError,
    ResourceNotFoundError,
)
from backend.app.models import Company, Opportunity, User
from backend.app.models.enums import OpportunityStage
from backend.app.repositories import OpportunityRepository
from backend.app.schemas import OpportunityCreate
from backend.app.services import OpportunityService


class OpportunityServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = OpportunityService(MagicMock(spec=Session))
        self.service.opportunities = MagicMock(spec=OpportunityRepository)
        self.service.companies = MagicMock()
        self.service.users = MagicMock()
        self.company = Company(id=10, name="Customer", owner_id=1)
        self.user = User(id=20, name="Owner", email="owner@example.test")
        self.opportunity = Opportunity(
            id=30,
            name="Deal",
            company_id=10,
            owner_id=20,
            stage=OpportunityStage.NEW,
        )
        self.service.companies.get.return_value = self.company
        self.service.users.get.return_value = self.user
        self.service.opportunities.get_for_update.return_value = self.opportunity
        self.service.opportunities.update.side_effect = self._apply_update

    @staticmethod
    def _apply_update(opportunity, data):
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(opportunity, field, value)
        return opportunity

    def test_create_validates_company_and_owner(self):
        data = OpportunityCreate(name="Deal", company_id=10, owner_id=20)
        self.service.opportunities.create.return_value = self.opportunity

        result = self.service.create_opportunity(data)

        self.assertIs(result, self.opportunity)
        self.service.companies.get.assert_called_once_with(10)
        self.service.users.get.assert_called_once_with(20)
        self.service.opportunities.create.assert_called_once_with(data)

    def test_create_rejects_missing_related_records(self):
        data = OpportunityCreate(name="Deal", company_id=10, owner_id=20)
        self.service.companies.get.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, "company 10"):
            self.service.create_opportunity(data)

        self.service.companies.get.return_value = self.company
        self.service.users.get.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, "user 20"):
            self.service.create_opportunity(data)
        self.service.opportunities.create.assert_not_called()

    def test_create_rejects_terminal_initial_stage(self):
        data = OpportunityCreate(
            name="Deal",
            company_id=10,
            owner_id=20,
            stage=OpportunityStage.WON,
        )

        with self.assertRaisesRegex(InvalidOpportunityTransitionError, "cannot start"):
            self.service.create_opportunity(data)

        self.service.companies.get.assert_not_called()
        self.service.opportunities.create.assert_not_called()

    def test_change_stage_handles_active_terminal_and_noop_transitions(self):
        result = self.service.change_stage(30, OpportunityStage.QUALIFIED)
        self.assertIs(result.stage, OpportunityStage.QUALIFIED)

        self.service.opportunities.update.reset_mock()
        result = self.service.change_stage(30, OpportunityStage.QUALIFIED)
        self.assertIs(result, self.opportunity)
        self.service.opportunities.update.assert_not_called()

        with self.assertRaisesRegex(InvalidOpportunityTransitionError, "mark_as_won"):
            self.service.change_stage(30, OpportunityStage.WON)

        self.opportunity.stage = OpportunityStage.LOST
        with self.assertRaisesRegex(InvalidOpportunityTransitionError, "reopened"):
            self.service.change_stage(30, OpportunityStage.PROPOSAL)

    def test_terminal_transitions_are_idempotent_and_cannot_cross(self):
        self.assertIs(
            self.service.mark_as_won(30).stage,
            OpportunityStage.WON,
        )
        self.service.opportunities.update.reset_mock()
        self.assertIs(self.service.mark_as_won(30), self.opportunity)
        self.service.opportunities.update.assert_not_called()

        with self.assertRaises(InvalidOpportunityTransitionError):
            self.service.mark_as_lost(30)

    def test_reopen_only_accepts_terminal_opportunities_and_active_targets(self):
        with self.assertRaisesRegex(InvalidOpportunityTransitionError, "only won or lost"):
            self.service.reopen_opportunity(30)

        self.opportunity.stage = OpportunityStage.LOST
        result = self.service.reopen_opportunity(30, OpportunityStage.QUALIFIED)
        self.assertIs(result.stage, OpportunityStage.QUALIFIED)

        self.opportunity.stage = OpportunityStage.LOST
        with self.assertRaisesRegex(InvalidOpportunityTransitionError, "non-terminal"):
            self.service.reopen_opportunity(30, OpportunityStage.WON)

    def test_assign_owner_is_idempotent_and_reassign_requires_change(self):
        self.assertIs(self.service.assign_owner(30, 20), self.opportunity)
        self.service.opportunities.update.assert_not_called()

        self.service.users.get.return_value = User(
            id=21, name="New Owner", email="new@example.test"
        )
        result = self.service.reassign_owner(30, 21)
        self.assertEqual(result.owner_id, 21)

        with self.assertRaises(OpportunityOwnerConflictError):
            self.service.reassign_owner(30, 21)

    def test_detail_and_pipeline_queries_are_delegated(self):
        self.service.opportunities.get_detail.return_value = self.opportunity
        self.service.opportunities.list_pipeline.return_value = [self.opportunity]

        self.assertIs(self.service.get_opportunity_detail(30), self.opportunity)
        result = self.service.get_pipeline(owner_id=20, limit=25)

        self.assertEqual(result, [self.opportunity])
        self.service.opportunities.list_pipeline.assert_called_once_with(
            owner_id=20,
            company_id=None,
            offset=0,
            limit=25,
        )

        self.service.opportunities.get_detail.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, "opportunity 31"):
            self.service.get_opportunity_detail(31)


if __name__ == "__main__":
    unittest.main()
