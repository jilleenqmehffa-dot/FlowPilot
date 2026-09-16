"""Task validation, assignment, and lifecycle operations."""

from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    InvalidTaskError,
    InvalidTaskTransitionError,
    ResourceNotFoundError,
)
from backend.app.models import Company, Opportunity, Task, User
from backend.app.models.enums import TaskStatus
from backend.app.repositories import (
    CompanyRepository,
    OpportunityRepository,
    TaskRepository,
    UserRepository,
)
from backend.app.schemas import TaskCreate, TaskUpdate

ACTIVE_STATUSES = frozenset({TaskStatus.TODO, TaskStatus.IN_PROGRESS})
TERMINAL_STATUSES = frozenset({TaskStatus.DONE, TaskStatus.CANCELED})


class TaskService:
    """Coordinate task rules without taking ownership of transactions."""

    def __init__(self, session: Session) -> None:
        self.tasks = TaskRepository(session)
        self.companies = CompanyRepository(session)
        self.opportunities = OpportunityRepository(session)
        self.users = UserRepository(session)

    def create_task(self, data: TaskCreate) -> Task:
        self._require_user(data.assignee_id)
        if data.company_id is not None:
            self._require_company(data.company_id)
        if data.opportunity_id is not None:
            opportunity = self._require_opportunity(data.opportunity_id)
            self._validate_opportunity_company(opportunity, data.company_id)
        return self.tasks.create(data)

    def get_task(self, task_id: int) -> Task:
        task = self.tasks.get_detail(task_id)
        if task is None:
            raise ResourceNotFoundError("task", task_id)
        return task

    def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        task = self._require_task(task_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return task

        self._validate_required_updates(changes)
        if "assignee_id" in changes:
            self._require_user(data.assignee_id)
        if "company_id" in changes and data.company_id is not None:
            self._require_company(data.company_id)

        company_id = changes.get("company_id", task.company_id)
        opportunity_id = changes.get("opportunity_id", task.opportunity_id)
        associations_changed = "company_id" in changes or "opportunity_id" in changes
        if opportunity_id is not None and associations_changed:
            opportunity = self._require_opportunity(opportunity_id)
            self._validate_opportunity_company(opportunity, company_id)

        if "status" in changes:
            self._validate_status_transition(task.status, data.status)
        return self.tasks.update(task, data)

    def delete_task(self, task_id: int) -> None:
        task = self._require_task(task_id)
        self.tasks.delete(task)

    def list_tasks(
        self,
        *,
        assignee_id: int | None = None,
        company_id: int | None = None,
        opportunity_id: int | None = None,
        status: TaskStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        return self.tasks.list_filtered(
            assignee_id=assignee_id,
            company_id=company_id,
            opportunity_id=opportunity_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    def assign_task(self, task_id: int, assignee_id: int) -> Task:
        self._require_user(assignee_id)
        task = self._require_task(task_id)
        if task.assignee_id == assignee_id:
            return task
        return self.tasks.update(task, TaskUpdate(assignee_id=assignee_id))

    def start_task(self, task_id: int) -> Task:
        return self._change_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: int) -> Task:
        return self._change_status(task_id, TaskStatus.DONE)

    def cancel_task(self, task_id: int) -> Task:
        return self._change_status(task_id, TaskStatus.CANCELED)

    def reopen_task(self, task_id: int) -> Task:
        return self._change_status(task_id, TaskStatus.TODO)

    def _change_status(self, task_id: int, target_status: TaskStatus) -> Task:
        task = self._require_task(task_id)
        if task.status == target_status:
            return task
        self._validate_status_transition(task.status, target_status)
        return self.tasks.update(task, TaskUpdate(status=target_status))

    def _require_task(self, task_id: int) -> Task:
        task = self.tasks.get_for_update(task_id)
        if task is None:
            raise ResourceNotFoundError("task", task_id)
        return task

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
    def _validate_opportunity_company(
        opportunity: Opportunity,
        company_id: int | None,
    ) -> None:
        if company_id is None:
            raise InvalidTaskError(
                "company_id is required when opportunity_id is provided"
            )
        if opportunity.company_id != company_id:
            raise InvalidTaskError(
                f"opportunity {opportunity.id} does not belong to company {company_id}"
            )

    @staticmethod
    def _validate_required_updates(changes: dict[str, object]) -> None:
        for field in ("title", "assignee_id", "status", "due_at"):
            if field in changes and changes[field] is None:
                raise InvalidTaskError(f"{field} cannot be null")

    @staticmethod
    def _validate_status_transition(
        current_status: TaskStatus,
        target_status: TaskStatus | None,
    ) -> None:
        if target_status is None:
            raise InvalidTaskError("status cannot be null")
        if current_status == target_status:
            return
        if current_status in TERMINAL_STATUSES and target_status != TaskStatus.TODO:
            raise InvalidTaskTransitionError(
                f"a {current_status.value} task must be reopened before changing status"
            )
        if current_status == TaskStatus.TODO and target_status not in {
            TaskStatus.IN_PROGRESS,
            TaskStatus.DONE,
            TaskStatus.CANCELED,
        }:
            raise InvalidTaskTransitionError(
                f"cannot change {current_status.value} directly to {target_status.value}"
            )
        if current_status == TaskStatus.IN_PROGRESS and target_status not in {
            TaskStatus.TODO,
            TaskStatus.DONE,
            TaskStatus.CANCELED,
        }:
            raise InvalidTaskTransitionError(
                f"cannot change {current_status.value} directly to {target_status.value}"
            )
