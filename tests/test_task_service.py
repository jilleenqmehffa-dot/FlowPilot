import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    InvalidTaskError,
    InvalidTaskTransitionError,
    ResourceNotFoundError,
)
from backend.app.models import Company, Opportunity, Task, User
from backend.app.models.enums import OpportunityStage, TaskStatus
from backend.app.repositories import TaskRepository
from backend.app.schemas import TaskCreate, TaskUpdate
from backend.app.services import TaskService


class TaskServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TaskService(MagicMock(spec=Session))
        self.service.tasks = MagicMock(spec=TaskRepository)
        self.service.companies = MagicMock()
        self.service.opportunities = MagicMock()
        self.service.users = MagicMock()
        self.user = User(id=20, name="Owner", email="owner@example.test")
        self.company = Company(id=10, name="Customer", owner_id=20)
        self.opportunity = Opportunity(
            id=30,
            name="Deal",
            company_id=10,
            owner_id=20,
            stage=OpportunityStage.NEW,
        )
        self.task = Task(
            id=40,
            title="Follow up",
            assignee_id=20,
            status=TaskStatus.TODO,
            due_at=datetime.now(UTC) + timedelta(days=1),
            company_id=10,
            opportunity_id=30,
        )
        self.service.users.get.return_value = self.user
        self.service.companies.get.return_value = self.company
        self.service.opportunities.get.return_value = self.opportunity
        self.service.tasks.get_for_update.return_value = self.task
        self.service.tasks.update.side_effect = self._apply_update

    def _apply_update(self, task: Task, data: TaskUpdate) -> Task:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        return task

    def create_data(self, **changes) -> TaskCreate:
        values = {
            "title": "Follow up",
            "assignee_id": 20,
            "due_at": datetime.now(UTC) + timedelta(days=1),
            "company_id": 10,
            "opportunity_id": 30,
        }
        values.update(changes)
        return TaskCreate(**values)

    def test_create_validates_associations_and_uses_repository(self):
        data = self.create_data()
        self.service.tasks.create.return_value = self.task

        self.assertIs(self.service.create_task(data), self.task)

        self.service.users.get.assert_called_once_with(20)
        self.service.companies.get.assert_called_once_with(10)
        self.service.opportunities.get.assert_called_once_with(30)
        self.service.tasks.create.assert_called_once_with(data)

    def test_create_rejects_missing_or_inconsistent_associations(self):
        self.service.users.get.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.service.create_task(self.create_data())

        self.service.users.get.return_value = self.user
        self.service.companies.get.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.service.create_task(self.create_data())

        self.service.companies.get.return_value = self.company
        self.opportunity.company_id = 11
        with self.assertRaises(InvalidTaskError):
            self.service.create_task(self.create_data())
        self.service.tasks.create.assert_not_called()

    def test_get_task_uses_detail_query_and_raises_when_missing(self):
        self.service.tasks.get_detail.return_value = self.task
        self.assertIs(self.service.get_task(40), self.task)

        self.service.tasks.get_detail.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            self.service.get_task(41)

    def test_update_revalidates_links_and_allows_clearing_optional_fields(self):
        result = self.service.update_task(
            40,
            TaskUpdate(description=None, company_id=None, opportunity_id=None),
        )

        self.assertIs(result, self.task)
        self.assertIsNone(result.company_id)
        self.assertIsNone(result.opportunity_id)

        self.task.company_id = 10
        self.task.opportunity_id = 30
        self.opportunity.company_id = 10
        with self.assertRaises(InvalidTaskError):
            self.service.update_task(40, TaskUpdate(company_id=11))

    def test_update_rejects_null_required_fields(self):
        for field in ("title", "assignee_id", "status", "due_at"):
            with self.subTest(field=field), self.assertRaises(InvalidTaskError):
                self.service.update_task(40, TaskUpdate(**{field: None}))

    def test_lifecycle_transitions_are_validated_and_idempotent(self):
        self.assertEqual(self.service.start_task(40).status, TaskStatus.IN_PROGRESS)
        self.assertIs(self.service.start_task(40), self.task)
        self.assertEqual(self.service.complete_task(40).status, TaskStatus.DONE)
        self.assertIs(self.service.complete_task(40), self.task)

        with self.assertRaises(InvalidTaskTransitionError):
            self.service.cancel_task(40)

        self.assertEqual(self.service.reopen_task(40).status, TaskStatus.TODO)

    def test_assign_list_and_delete_delegate_to_repository(self):
        self.assertIs(self.service.assign_task(40, 20), self.task)
        self.service.tasks.update.assert_not_called()

        replacement = User(id=21, name="Other", email="other@example.test")
        self.service.users.get.return_value = replacement
        self.assertEqual(self.service.assign_task(40, 21).assignee_id, 21)

        self.service.tasks.list_filtered.return_value = [self.task]
        self.assertEqual(
            self.service.list_tasks(assignee_id=21, status=TaskStatus.TODO),
            [self.task],
        )
        self.service.tasks.list_filtered.assert_called_once_with(
            assignee_id=21,
            company_id=None,
            opportunity_id=None,
            status=TaskStatus.TODO,
            offset=0,
            limit=100,
        )

        self.service.delete_task(40)
        self.service.tasks.delete.assert_called_once_with(self.task)


if __name__ == "__main__":
    unittest.main()
