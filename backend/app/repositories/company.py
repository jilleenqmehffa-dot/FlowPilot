from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from backend.app.models import Company
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import CompanyCreate, CompanyUpdate


class CompanyRepository(BaseRepository[Company, CompanyCreate, CompanyUpdate]):
    model = Company

    def get_for_update(self, company_id: int) -> Company | None:
        statement = select(Company).where(Company.id == company_id).with_for_update()
        return self.session.scalar(statement)

    def get_detail(self, company_id: int) -> Company | None:
        statement = (
            select(Company)
            .options(
                joinedload(Company.owner),
                selectinload(Company.contacts),
                selectinload(Company.opportunities),
                selectinload(Company.activities),
                selectinload(Company.tasks),
            )
            .where(Company.id == company_id)
        )
        return self.session.scalar(statement)

    def list_customers(
        self,
        *,
        owner_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Company]:
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        if not 1 <= limit <= self.max_page_size:
            raise ValueError(f"limit must be between 1 and {self.max_page_size}")

        statement = select(Company)
        if owner_id is not None:
            statement = statement.where(Company.owner_id == owner_id)
        statement = statement.order_by(Company.name, Company.id).offset(offset).limit(limit)
        return list(self.session.scalars(statement).all())
