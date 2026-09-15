from backend.app.models import User
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    model = User
