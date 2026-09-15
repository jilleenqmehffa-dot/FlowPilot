from backend.app.models import Opportunity
from backend.app.repositories.base import BaseRepository
from backend.app.schemas import OpportunityCreate, OpportunityUpdate


class OpportunityRepository(
    BaseRepository[Opportunity, OpportunityCreate, OpportunityUpdate]
):
    model = Opportunity
