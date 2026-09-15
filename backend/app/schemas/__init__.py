"""Public Pydantic API schemas for the CRM domain."""

from backend.app.schemas.activity import (
    ActivityBase,
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
)
from backend.app.schemas.company import (
    CompanyBase,
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
)
from backend.app.schemas.contact import ContactBase, ContactCreate, ContactRead, ContactUpdate
from backend.app.schemas.opportunity import (
    OpportunityBase,
    OpportunityCreate,
    OpportunityRead,
    OpportunityUpdate,
)
from backend.app.schemas.task import TaskBase, TaskCreate, TaskRead, TaskUpdate
from backend.app.schemas.user import UserBase, UserCreate, UserRead, UserUpdate

__all__ = [
    "ActivityBase",
    "ActivityCreate",
    "ActivityRead",
    "ActivityUpdate",
    "CompanyBase",
    "CompanyCreate",
    "CompanyRead",
    "CompanyUpdate",
    "ContactBase",
    "ContactCreate",
    "ContactRead",
    "ContactUpdate",
    "OpportunityBase",
    "OpportunityCreate",
    "OpportunityRead",
    "OpportunityUpdate",
    "TaskBase",
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
