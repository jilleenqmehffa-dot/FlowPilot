from backend.app.models import Company
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import CompanyCreate, CompanyUpdate


class CompanyRepository(BaseRepository[Company, CompanyCreate, CompanyUpdate]):
    model = Company
