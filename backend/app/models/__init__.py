"""CRM ORM models.

Importing this package registers every model with ``Base.metadata`` and exposes
the public model classes from one stable location.
"""

from backend.app.models.activity import Activity
from backend.app.models.company import Company
from backend.app.models.contact import Contact
from backend.app.models.opportunity import Opportunity
from backend.app.models.task import Task
from backend.app.models.user import User

__all__ = ["Activity", "Company", "Contact", "Opportunity", "Task", "User"]
