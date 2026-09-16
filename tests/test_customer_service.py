import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from backend.app.core.exceptions import InvalidCustomerError, ResourceNotFoundError
from backend.app.models import Company, Contact, User
from backend.app.repositories import CompanyRepository, ContactRepository
from backend.app.schemas import CompanyCreate, CompanyUpdate, ContactCreate, ContactUpdate
from backend.app.services import CustomerService


class CustomerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = CustomerService(MagicMock(spec=Session))
        self.service.customers = MagicMock(spec=CompanyRepository)
        self.service.contacts = MagicMock(spec=ContactRepository)
        self.service.users = MagicMock()
        self.user = User(id=20, name="Owner", email="owner@example.test")
        self.customer = Company(id=10, name="Customer", owner_id=20)
        self.contact = Contact(
            id=30,
            company_id=10,
            name="Contact",
            email="contact@example.test",
        )
        self.service.users.get.return_value = self.user
        self.service.customers.get.return_value = self.customer
        self.service.customers.get_for_update.return_value = self.customer
        self.service.contacts.get_for_update.return_value = self.contact
        self.service.customers.update.side_effect = self._apply_update
        self.service.contacts.update.side_effect = self._apply_update

    @staticmethod
    def _apply_update(instance, data):
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        return instance

    def test_create_customer_requires_real_owner(self):
        data = CompanyCreate(name="Customer", owner_id=20)
        self.service.customers.create.return_value = self.customer

        self.assertIs(self.service.create_customer(data), self.customer)
        self.service.users.get.assert_called_once_with(20)
        self.service.customers.create.assert_called_once_with(data)

        self.service.users.get.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.service.create_customer(data)

    def test_get_update_assign_delete_customer(self):
        self.service.customers.get_detail.return_value = self.customer
        self.assertIs(self.service.get_customer(10), self.customer)

        result = self.service.update_customer(10, CompanyUpdate(name="Renamed"))
        self.assertEqual(result.name, "Renamed")

        self.assertIs(self.service.assign_owner(10, 20), self.customer)
        self.service.users.get.return_value = User(
            id=21, name="Other", email="other@example.test"
        )
        self.assertEqual(self.service.assign_owner(10, 21).owner_id, 21)

        self.service.delete_customer(10)
        self.service.customers.delete.assert_called_once_with(self.customer)

    def test_customer_mutations_reject_missing_and_null_required_fields(self):
        self.service.customers.get_for_update.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.service.update_customer(11, CompanyUpdate(name="Missing"))

        self.service.customers.get_for_update.return_value = self.customer
        for field in ("name", "owner_id"):
            with self.subTest(field=field), self.assertRaises(InvalidCustomerError):
                self.service.update_customer(10, CompanyUpdate(**{field: None}))

    def test_customer_list_delegates_filters_and_pagination(self):
        self.service.customers.list_customers.return_value = [self.customer]

        self.assertEqual(
            self.service.list_customers(owner_id=20, offset=5, limit=25),
            [self.customer],
        )
        self.service.customers.list_customers.assert_called_once_with(
            owner_id=20,
            offset=5,
            limit=25,
        )

    def test_contact_crud_validates_customer_and_uses_repository(self):
        data = ContactCreate(
            company_id=10,
            name="Contact",
            email="contact@example.test",
        )
        self.service.contacts.create.return_value = self.contact
        self.assertIs(self.service.create_contact(data), self.contact)
        self.service.customers.get_for_update.assert_called_with(10)

        self.service.contacts.get_detail.return_value = self.contact
        self.assertIs(self.service.get_contact(30), self.contact)

        other_customer = Company(id=11, name="Other", owner_id=20)
        self.service.customers.get_for_update.return_value = other_customer
        result = self.service.update_contact(30, ContactUpdate(company_id=11))
        self.assertEqual(result.company_id, 11)

        self.service.delete_contact(30)
        self.service.contacts.delete.assert_called_once_with(self.contact)

    def test_contact_mutations_reject_missing_and_null_required_fields(self):
        self.service.customers.get_for_update.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.service.create_contact(ContactCreate(company_id=11, name="Contact"))

        for field in ("company_id", "name"):
            with self.subTest(field=field), self.assertRaises(InvalidCustomerError):
                self.service.update_contact(30, ContactUpdate(**{field: None}))

    def test_list_contacts_distinguishes_missing_customer_from_empty_list(self):
        self.service.contacts.list_by_company.return_value = [self.contact]
        self.assertEqual(
            self.service.list_contacts(10, offset=5, limit=25),
            [self.contact],
        )
        self.service.contacts.list_by_company.assert_called_once_with(
            10,
            offset=5,
            limit=25,
        )

        self.service.customers.get.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.service.list_contacts(11)


if __name__ == "__main__":
    unittest.main()
