"""Build the bounded CRM context consumed by the deal runtime."""

from sqlalchemy.orm import Session

from backend.app.agent.schemas import ActivityContext, CRMContext, TaskContext
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models import Opportunity
from backend.app.models.enums import TaskStatus
from backend.app.repositories import OpportunityRepository


class CRMContextProvider:
    """Read a deal with eager-loaded relationships and turn it into LLM input."""

    def __init__(
        self,
        session: Session,
        *,
        activity_limit: int = 20,
        task_limit: int = 20,
    ) -> None:
        if activity_limit < 1 or task_limit < 1:
            raise ValueError("context limits must be greater than 0")
        self.opportunities = OpportunityRepository(session)
        self.activity_limit = activity_limit
        self.task_limit = task_limit

    def get(self, opportunity_id: int) -> CRMContext:
        opportunity = self.opportunities.get_detail(opportunity_id)
        if opportunity is None:
            raise ResourceNotFoundError("opportunity", opportunity_id)
        return self._build(opportunity)

    def _build(self, opportunity: Opportunity) -> CRMContext:
        activities = sorted(
            opportunity.activities,
            key=lambda activity: (activity.occurred_at, activity.id),
            reverse=True,
        )[: self.activity_limit]
        tasks = sorted(
            (
                task
                for task in opportunity.tasks
                if task.status in {TaskStatus.TODO, TaskStatus.IN_PROGRESS}
            ),
            key=lambda task: (task.due_at, task.id),
        )[: self.task_limit]
        return CRMContext(
            opportunity_id=opportunity.id,
            opportunity_name=opportunity.name,
            company_id=opportunity.company_id,
            company_name=opportunity.company.name,
            owner_id=opportunity.owner_id,
            owner_name=opportunity.owner.name,
            amount=opportunity.amount,
            stage=opportunity.stage,
            probability=opportunity.probability,
            expected_close_date=opportunity.expected_close_date,
            recent_activities=tuple(
                ActivityContext(
                    summary=activity.summary,
                    notes=activity.notes,
                    occurred_at=activity.occurred_at,
                    performed_by_id=activity.performed_by_id,
                )
                for activity in activities
            ),
            open_tasks=tuple(
                TaskContext(
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    due_at=task.due_at,
                    assignee_id=task.assignee_id,
                )
                for task in tasks
            ),
        )
