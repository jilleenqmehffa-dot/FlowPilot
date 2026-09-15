from backend.app.models import Activity
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import ActivityCreate, ActivityUpdate


class ActivityRepository(BaseRepository[Activity, ActivityCreate, ActivityUpdate]):
    model = Activity
