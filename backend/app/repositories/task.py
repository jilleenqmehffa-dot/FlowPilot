from sqlalchemy import select
from sqlalchemy.orm import joinedload

from backend.app.models import Task
from backend.app.models.enums import TaskStatus
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    model = Task

    def get_for_update(self, task_id: int) -> Task | None:
        statement = select(Task).where(Task.id == task_id).with_for_update()
        return self.session.scalar(statement)

    def get_detail(self, task_id: int) -> Task | None:
        statement = (
            select(Task)
            .options(
                joinedload(Task.assignee),
                joinedload(Task.company),
                joinedload(Task.opportunity),
            )
            .where(Task.id == task_id)
        )
        return self.session.scalar(statement)

    def list_filtered(
        self,
        *,
        assignee_id: int | None = None,
        company_id: int | None = None,
        opportunity_id: int | None = None,
        status: TaskStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        if not 1 <= limit <= self.max_page_size:
            raise ValueError(f"limit must be between 1 and {self.max_page_size}")

        statement = select(Task)
        if assignee_id is not None:
            statement = statement.where(Task.assignee_id == assignee_id)
        if company_id is not None:
            statement = statement.where(Task.company_id == company_id)
        if opportunity_id is not None:
            statement = statement.where(Task.opportunity_id == opportunity_id)
        if status is not None:
            statement = statement.where(Task.status == status)
        statement = (
            statement.order_by(Task.due_at, Task.id).offset(offset).limit(limit)
        )
        return list(self.session.scalars(statement).all())
