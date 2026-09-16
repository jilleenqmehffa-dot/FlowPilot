"""Public CRM business services."""

from backend.app.services.activity_service import ActivityService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.task_service import TaskService

__all__ = ["ActivityService", "OpportunityService", "TaskService"]
