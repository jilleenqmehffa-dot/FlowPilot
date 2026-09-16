"""Customer accounts and their contacts business operations."""

from sqlalchemy.orm import Session

from backend.app.core.exceptions import InvalidCustomerError, ResourceNotFoundError
from backend.app.models import Company, Contact, User
from backend.app.repositories import CompanyRepository, ContactRepository, UserRepository
from backend.app.schemas import (
    CompanyCreate,
    CompanyUpdate,
    ContactCreate,
    ContactUpdate,
)


class CustomerService:
    """Treat companies as customer accounts and coordinate their contacts."""

    def __init__(self, session: Session) -> None:
        self.customers = CompanyRepository(session)
        self.contacts = ContactRepository(session)
        self.users = UserRepository(session)

    def create_customer(self, data: CompanyCreate) -> Company:
        self._require_user(data.owner_id)
        return self.customers.create(data)

    def get_customer(self, customer_id: int) -> Company:
        customer = self.customers.get_detail(customer_id)
        if customer is None:
            raise ResourceNotFoundError("customer", customer_id)
        return customer

    def update_customer(self, customer_id: int, data: CompanyUpdate) -> Company:
        customer = self._require_customer(customer_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return customer
        self._reject_null_required_fields(changes, ("name", "owner_id"))
        if "owner_id" in changes:
            self._require_user(data.owner_id)
        return self.customers.update(customer, data)

    def assign_owner(self, customer_id: int, owner_id: int) -> Company:
        self._require_user(owner_id)
        customer = self._require_customer(customer_id)
        if customer.owner_id == owner_id:
            return customer
        return self.customers.update(customer, CompanyUpdate(owner_id=owner_id))

    def delete_customer(self, customer_id: int) -> None:
        customer = self._require_customer(customer_id)
        self.customers.delete(customer)

    def list_customers(
        self,
        *,
        owner_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Company]:
        return self.customers.list_customers(
            owner_id=owner_id,
            offset=offset,
            limit=limit,
        )

    def create_contact(self, data: ContactCreate) -> Contact:
        self._require_customer(data.company_id)
        return self.contacts.create(data)

    def add_contact(self, data: ContactCreate) -> Contact:
        """Alias for callers that express contact creation as an account action."""

        return self.create_contact(data)

    def get_contact(self, contact_id: int) -> Contact:
        contact = self.contacts.get_detail(contact_id)
        if contact is None:
            raise ResourceNotFoundError("contact", contact_id)
        return contact

    def update_contact(self, contact_id: int, data: ContactUpdate) -> Contact:
        contact = self._require_contact(contact_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return contact
        self._reject_null_required_fields(changes, ("company_id", "name"))
        if "company_id" in changes:
            self._require_customer(data.company_id)
        return self.contacts.update(contact, data)

    def delete_contact(self, contact_id: int) -> None:
        contact = self._require_contact(contact_id)
        self.contacts.delete(contact)

    def list_contacts(
        self,
        customer_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Contact]:
        self._require_customer_exists(customer_id)
        return self.contacts.list_by_company(
            customer_id,
            offset=offset,
            limit=limit,
        )

    def _require_customer(self, customer_id: int) -> Company:
        customer = self.customers.get_for_update(customer_id)
        if customer is None:
            raise ResourceNotFoundError("customer", customer_id)
        return customer

    def _require_customer_exists(self, customer_id: int) -> Company:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise ResourceNotFoundError("customer", customer_id)
        return customer

    def _require_contact(self, contact_id: int) -> Contact:
        contact = self.contacts.get_for_update(contact_id)
        if contact is None:
            raise ResourceNotFoundError("contact", contact_id)
        return contact

    def _require_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise ResourceNotFoundError("user", user_id)
        return user

    @staticmethod
    def _reject_null_required_fields(
        changes: dict[str, object],
        required_fields: tuple[str, ...],
    ) -> None:
        for field in required_fields:
            if field in changes and changes[field] is None:
                raise InvalidCustomerError(f"{field} cannot be null")
