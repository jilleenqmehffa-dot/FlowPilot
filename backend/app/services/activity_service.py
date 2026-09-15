"""Activity validation and lifecycle operations."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app.core.exceptions import InvalidActivityError, ResourceNotFoundError
from backend.app.models import Activity, Company, Opportunity, User
from backend.app.repositories import (
    ActivityRepository,
    CompanyRepository,
    OpportunityRepository,
    UserRepository,
)
from backend.app.schemas import ActivityCreate, ActivityUpdate


class ActivityService:
    """Coordinate activity rules without taking ownership of transactions."""

    def __init__(self, session: Session) -> None:
        self.activities = ActivityRepository(session)
        self.companies = CompanyRepository(session)
        self.opportunities = OpportunityRepository(session)
        self.users = UserRepository(session)

    def create_activity(self, data: ActivityCreate) -> Activity:
        self._validate_occurred_at(data.occurred_at)
        self._require_user(data.performed_by_id)
        if data.company_id is not None:
            self._require_company(data.company_id)
        if data.opportunity_id is not None:
            opportunity = self._require_opportunity(data.opportunity_id)
            self._validate_opportunity_company(opportunity, data.company_id)
        return self.activities.create(data)

    def get_activity(self, activity_id: int) -> Activity:
        activity = self.activities.get_detail(activity_id)
        if activity is None:
            raise ResourceNotFoundError("activity", activity_id)
        return activity

    def update_activity(self, activity_id: int, data: ActivityUpdate) -> Activity:
        activity = self._require_activity(activity_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return activity

        self._validate_required_updates(changes)
        if "occurred_at" in changes:
            self._validate_occurred_at(data.occurred_at)
        if "performed_by_id" in changes:
            self._require_user(data.performed_by_id)
        if "company_id" in changes and data.company_id is not None:
            self._require_company(data.company_id)

        company_id = changes.get("company_id", activity.company_id)
        opportunity_id = changes.get("opportunity_id", activity.opportunity_id)
        associations_changed = "company_id" in changes or "opportunity_id" in changes
        if opportunity_id is not None and associations_changed:
            opportunity = self._require_opportunity(opportunity_id)
            self._validate_opportunity_company(opportunity, company_id)

        return self.activities.update(activity, data)

    def delete_activity(self, activity_id: int) -> None:
        activity = self._require_activity(activity_id)
        self.activities.delete(activity)

    def list_activities(
        self,
        *,
        company_id: int | None = None,
        opportunity_id: int | None = None,
        performed_by_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Activity]:
        return self.activities.list_filtered(
            company_id=company_id,
            opportunity_id=opportunity_id,
            performed_by_id=performed_by_id,
            offset=offset,
            limit=limit,
        )

    def _require_activity(self, activity_id: int) -> Activity:
        activity = self.activities.get_for_update(activity_id)
        if activity is None:
            raise ResourceNotFoundError("activity", activity_id)
        return activity

    def _require_company(self, company_id: int) -> Company:
        company = self.companies.get(company_id)
        if company is None:
            raise ResourceNotFoundError("company", company_id)
        return company

    def _require_opportunity(self, opportunity_id: int) -> Opportunity:
        opportunity = self.opportunities.get(opportunity_id)
        if opportunity is None:
            raise ResourceNotFoundError("opportunity", opportunity_id)
        return opportunity

    def _require_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise ResourceNotFoundError("user", user_id)
        return user

    @staticmethod
    def _validate_occurred_at(occurred_at: datetime | None) -> None:
        if occurred_at is None:
            raise InvalidActivityError("occurred_at cannot be null")
        if occurred_at > datetime.now(UTC):
            raise InvalidActivityError("occurred_at cannot be in the future")

    @staticmethod
    def _validate_opportunity_company(
        opportunity: Opportunity,
        company_id: int | None,
    ) -> None:
        if company_id is None:
            raise InvalidActivityError(
                "company_id is required when opportunity_id is provided"
            )
        if opportunity.company_id != company_id:
            raise InvalidActivityError(
                f"opportunity {opportunity.id} does not belong to company {company_id}"
            )

    @staticmethod
    def _validate_required_updates(changes: dict[str, object]) -> None:
        for field in ("summary", "occurred_at", "performed_by_id"):
            if field in changes and changes[field] is None:
                raise InvalidActivityError(f"{field} cannot be null")
