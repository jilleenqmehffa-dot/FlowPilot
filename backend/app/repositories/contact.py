from backend.app.models import Contact
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import ContactCreate, ContactUpdate


class ContactRepository(BaseRepository[Contact, ContactCreate, ContactUpdate]):
    model = Contact
