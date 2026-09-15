"""Public repositories for the CRM domain."""

from backend.app.repositories.activity import ActivityRepository
from backend.app.repositories.base import BaseRepository
from backend.app.repositories.company import CompanyRepository
from backend.app.repositories.contact import ContactRepository
from backend.app.repositories.opportunity import OpportunityRepository
from backend.app.repositories.task import TaskRepository
from backend.app.repositories.user import UserRepository

__all__ = [
    "ActivityRepository",
    "BaseRepository",
    "CompanyRepository",
    "ContactRepository",
    "OpportunityRepository",
    "TaskRepository",
    "UserRepository",
]
