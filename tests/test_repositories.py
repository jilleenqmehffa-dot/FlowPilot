import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from backend.app.models import Activity, Company, Contact, Opportunity, Task, User
from backend.app.repositories import (
    ActivityRepository,
    CompanyRepository,
    ContactRepository,
    OpportunityRepository,
    TaskRepository,
    UserRepository,
)
from backend.app.schemas import UserCreate, UserUpdate


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)
        self.repository = UserRepository(self.session)

    def test_model_repositories_are_paired_with_models(self):
        pairs = (
            (ActivityRepository, Activity),
            (CompanyRepository, Company),
            (ContactRepository, Contact),
            (OpportunityRepository, Opportunity),
            (TaskRepository, Task),
            (UserRepository, User),
        )
        for repository, model in pairs:
            with self.subTest(repository=repository.__name__):
                self.assertIs(repository.model, model)

    def test_get_uses_session_identity_lookup(self):
        user = User(id=1, name="Owner", email="owner@example.test")
        self.session.get.return_value = user

        result = self.repository.get(1)

        self.assertIs(result, user)
        self.session.get.assert_called_once_with(User, 1)

    def test_list_is_ordered_and_paginated(self):
        users = [User(id=3, name="Owner", email="owner@example.test")]
        self.session.scalars.return_value.all.return_value = users

        result = self.repository.list(offset=20, limit=10)

        self.assertEqual(result, users)
        statement = self.session.scalars.call_args.args[0]
        self.assertIn("ORDER BY users.id", str(statement))
        self.assertEqual(statement.compile().params, {"param_1": 10, "param_2": 20})

    def test_list_rejects_invalid_pagination(self):
        for arguments in ({"offset": -1}, {"limit": 0}, {"limit": 101}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.repository.list(**arguments)
        self.session.scalars.assert_not_called()

    def test_create_flushes_and_refreshes_without_committing(self):
        result = self.repository.create(
            UserCreate(name="Owner", email="owner@example.test")
        )

        self.assertIsInstance(result, User)
        self.assertEqual(result.name, "Owner")
        self.session.add.assert_called_once_with(result)
        self.session.flush.assert_called_once_with()
        self.session.refresh.assert_called_once_with(result)
        self.session.commit.assert_not_called()

    def test_update_only_applies_fields_present_in_payload(self):
        user = User(id=1, name="Before", email="owner@example.test")

        result = self.repository.update(user, UserUpdate(name="After"))

        self.assertIs(result, user)
        self.assertEqual(user.name, "After")
        self.assertEqual(user.email, "owner@example.test")
        self.session.flush.assert_called_once_with()
        self.session.refresh.assert_called_once_with(user)
        self.session.commit.assert_not_called()

    def test_delete_flushes_without_committing(self):
        user = User(id=1, name="Owner", email="owner@example.test")

        self.repository.delete(user)

        self.session.delete.assert_called_once_with(user)
        self.session.flush.assert_called_once_with()
        self.session.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
