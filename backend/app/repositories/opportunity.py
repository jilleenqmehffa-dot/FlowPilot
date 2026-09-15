from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from backend.app.models import Opportunity
from backend.app.models.enums import OpportunityStage
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import OpportunityCreate, OpportunityUpdate


class OpportunityRepository(
    BaseRepository[Opportunity, OpportunityCreate, OpportunityUpdate]
):
    model = Opportunity

    def get_for_update(self, opportunity_id: int) -> Opportunity | None:
        statement = (
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .with_for_update()
        )
        return self.session.scalar(statement)

    def get_detail(self, opportunity_id: int) -> Opportunity | None:
        statement = (
            select(Opportunity)
            .options(
                joinedload(Opportunity.company),
                joinedload(Opportunity.owner),
                selectinload(Opportunity.activities),
                selectinload(Opportunity.tasks),
            )
            .where(Opportunity.id == opportunity_id)
        )
        return self.session.scalar(statement)

    def list_pipeline(
        self,
        *,
        owner_id: int | None = None,
        company_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Opportunity]:
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        if not 1 <= limit <= self.max_page_size:
            raise ValueError(f"limit must be between 1 and {self.max_page_size}")

        statement = select(Opportunity).where(
            Opportunity.stage.notin_((OpportunityStage.WON, OpportunityStage.LOST))
        )
        if owner_id is not None:
            statement = statement.where(Opportunity.owner_id == owner_id)
        if company_id is not None:
            statement = statement.where(Opportunity.company_id == company_id)
        statement = (
            statement.order_by(
                Opportunity.stage,
                Opportunity.expected_close_date.asc().nulls_last(),
                Opportunity.id,
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
