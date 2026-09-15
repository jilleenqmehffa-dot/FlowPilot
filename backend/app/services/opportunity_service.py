"""Opportunity lifecycle and pipeline business operations."""

from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    InvalidOpportunityTransitionError,
    OpportunityOwnerConflictError,
    ResourceNotFoundError,
)
from backend.app.models import Company, Opportunity, User
from backend.app.models.enums import OpportunityStage
from backend.app.repositories import (
    CompanyRepository,
    OpportunityRepository,
    UserRepository,
)
from backend.app.schemas import OpportunityCreate, OpportunityUpdate

TERMINAL_STAGES = frozenset({OpportunityStage.WON, OpportunityStage.LOST})
ACTIVE_STAGES = frozenset(stage for stage in OpportunityStage if stage not in TERMINAL_STAGES)


class OpportunityService:
    """Coordinate opportunity rules without taking ownership of transactions."""

    def __init__(self, session: Session) -> None:
        self.opportunities = OpportunityRepository(session)
        self.companies = CompanyRepository(session)
        self.users = UserRepository(session)

    def create_opportunity(self, data: OpportunityCreate) -> Opportunity:
        if data.stage in TERMINAL_STAGES:
            raise InvalidOpportunityTransitionError(
                "a new opportunity cannot start in a terminal stage"
            )
        self._require_company(data.company_id)
        self._require_user(data.owner_id)
        return self.opportunities.create(data)

    def change_stage(
        self,
        opportunity_id: int,
        stage: OpportunityStage,
    ) -> Opportunity:
        target_stage = OpportunityStage(stage)
        if target_stage in TERMINAL_STAGES:
            raise InvalidOpportunityTransitionError(
                "use mark_as_won or mark_as_lost to enter a terminal stage"
            )

        opportunity = self._get_for_update(opportunity_id)
        if opportunity.stage in TERMINAL_STAGES:
            raise InvalidOpportunityTransitionError(
                "a won or lost opportunity must be reopened before changing stage"
            )
        if opportunity.stage == target_stage:
            return opportunity
        return self.opportunities.update(
            opportunity,
            OpportunityUpdate(stage=target_stage),
        )

    def assign_owner(self, opportunity_id: int, owner_id: int) -> Opportunity:
        """Idempotently ensure that an opportunity has the requested owner."""

        self._require_user(owner_id)
        opportunity = self._get_for_update(opportunity_id)
        if opportunity.owner_id == owner_id:
            return opportunity
        return self.opportunities.update(
            opportunity,
            OpportunityUpdate(owner_id=owner_id),
        )

    def reassign_owner(self, opportunity_id: int, owner_id: int) -> Opportunity:
        opportunity = self._get_for_update(opportunity_id)
        if opportunity.owner_id == owner_id:
            raise OpportunityOwnerConflictError(
                f"opportunity {opportunity_id} is already assigned to user {owner_id}"
            )
        self._require_user(owner_id)
        return self.opportunities.update(
            opportunity,
            OpportunityUpdate(owner_id=owner_id),
        )

    def mark_as_won(self, opportunity_id: int) -> Opportunity:
        return self._mark_as_terminal(opportunity_id, OpportunityStage.WON)

    def mark_as_lost(self, opportunity_id: int) -> Opportunity:
        return self._mark_as_terminal(opportunity_id, OpportunityStage.LOST)

    def reopen_opportunity(
        self,
        opportunity_id: int,
        stage: OpportunityStage = OpportunityStage.NEW,
    ) -> Opportunity:
        target_stage = OpportunityStage(stage)
        if target_stage not in ACTIVE_STAGES:
            raise InvalidOpportunityTransitionError(
                "a reopened opportunity must use a non-terminal stage"
            )

        opportunity = self._get_for_update(opportunity_id)
        if opportunity.stage not in TERMINAL_STAGES:
            raise InvalidOpportunityTransitionError(
                "only won or lost opportunities can be reopened"
            )
        return self.opportunities.update(
            opportunity,
            OpportunityUpdate(stage=target_stage),
        )

    def get_opportunity_detail(self, opportunity_id: int) -> Opportunity:
        opportunity = self.opportunities.get_detail(opportunity_id)
        if opportunity is None:
            raise ResourceNotFoundError("opportunity", opportunity_id)
        return opportunity

    def get_pipeline(
        self,
        *,
        owner_id: int | None = None,
        company_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Opportunity]:
        return self.opportunities.list_pipeline(
            owner_id=owner_id,
            company_id=company_id,
            offset=offset,
            limit=limit,
        )

    def _mark_as_terminal(
        self,
        opportunity_id: int,
        target_stage: OpportunityStage,
    ) -> Opportunity:
        opportunity = self._get_for_update(opportunity_id)
        if opportunity.stage == target_stage:
            return opportunity
        if opportunity.stage in TERMINAL_STAGES:
            raise InvalidOpportunityTransitionError(
                f"cannot change {opportunity.stage.value} directly to {target_stage.value}"
            )
        return self.opportunities.update(
            opportunity,
            OpportunityUpdate(stage=target_stage),
        )

    def _get_for_update(self, opportunity_id: int) -> Opportunity:
        opportunity = self.opportunities.get_for_update(opportunity_id)
        if opportunity is None:
            raise ResourceNotFoundError("opportunity", opportunity_id)
        return opportunity

    def _require_company(self, company_id: int) -> Company:
        company = self.companies.get(company_id)
        if company is None:
            raise ResourceNotFoundError("company", company_id)
        return company

    def _require_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise ResourceNotFoundError("user", user_id)
        return user
