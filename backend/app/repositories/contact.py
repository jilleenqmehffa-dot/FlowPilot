from sqlalchemy import select
from sqlalchemy.orm import joinedload

from backend.app.models import Contact
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import ContactCreate, ContactUpdate


class ContactRepository(BaseRepository[Contact, ContactCreate, ContactUpdate]):
    model = Contact

    def get_for_update(self, contact_id: int) -> Contact | None:
        statement = select(Contact).where(Contact.id == contact_id).with_for_update()
        return self.session.scalar(statement)

    def get_detail(self, contact_id: int) -> Contact | None:
        statement = (
            select(Contact)
            .options(joinedload(Contact.company))
            .where(Contact.id == contact_id)
        )
        return self.session.scalar(statement)

    def list_by_company(
        self,
        company_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Contact]:
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        if not 1 <= limit <= self.max_page_size:
            raise ValueError(f"limit must be between 1 and {self.max_page_size}")

        statement = (
            select(Contact)
            .where(Contact.company_id == company_id)
            .order_by(Contact.name, Contact.id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
