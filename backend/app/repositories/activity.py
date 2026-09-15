from sqlalchemy import select
from sqlalchemy.orm import joinedload

from backend.app.models import Activity
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import ActivityCreate, ActivityUpdate


class ActivityRepository(BaseRepository[Activity, ActivityCreate, ActivityUpdate]):
    model = Activity

    def get_for_update(self, activity_id: int) -> Activity | None:
        statement = select(Activity).where(Activity.id == activity_id).with_for_update()
        return self.session.scalar(statement)

    def get_detail(self, activity_id: int) -> Activity | None:
        statement = (
            select(Activity)
            .options(
                joinedload(Activity.performed_by),
                joinedload(Activity.company),
                joinedload(Activity.opportunity),
            )
            .where(Activity.id == activity_id)
        )
        return self.session.scalar(statement)

    def list_filtered(
        self,
        *,
        company_id: int | None = None,
        opportunity_id: int | None = None,
        performed_by_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Activity]:
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        if not 1 <= limit <= self.max_page_size:
            raise ValueError(f"limit must be between 1 and {self.max_page_size}")

        statement = select(Activity)
        if company_id is not None:
            statement = statement.where(Activity.company_id == company_id)
        if opportunity_id is not None:
            statement = statement.where(Activity.opportunity_id == opportunity_id)
        if performed_by_id is not None:
            statement = statement.where(Activity.performed_by_id == performed_by_id)
        statement = (
            statement.order_by(Activity.occurred_at.desc(), Activity.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
