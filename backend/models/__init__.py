"""CRM ORM models.

Importing this package registers every model with ``Base.metadata`` and exposes
the public model classes from one stable location.
"""

from backend.models.activity import Activity
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.opportunity import Opportunity
from backend.models.task import Task
from backend.models.user import User

__all__ = ["Activity", "Company", "Contact", "Opportunity", "Task", "User"]
