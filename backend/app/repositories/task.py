from backend.app.models import Task
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    model = Task
