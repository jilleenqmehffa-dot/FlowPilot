from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from backend.app.models.enums import OpportunityStage
from backend.app.schemas.base import Name200, RecordId, RecordRead, SchemaModel

Amount = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
Probability = Annotated[int, Field(ge=0, le=100)]


class OpportunityBase(SchemaModel):
    name: Name200
    company_id: RecordId
    owner_id: RecordId
    amount: Amount | None = None
    stage: OpportunityStage = OpportunityStage.NEW
    probability: Probability | None = None
    expected_close_date: date | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(SchemaModel):
    name: Name200 | None = None
    company_id: RecordId | None = None
    owner_id: RecordId | None = None
    amount: Amount | None = None
    stage: OpportunityStage | None = None
    probability: Probability | None = None
    expected_close_date: date | None = None


class OpportunityRead(OpportunityBase, RecordRead):
    pass
