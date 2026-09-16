"""State and final result types for the deal runtime."""

from typing import NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict

from backend.app.agent.schemas.context import CRMContext
from backend.app.agent.schemas.deal_analysis import DealAnalysis
from backend.app.agent.schemas.next_action import NextAction


class DealRuntimeState(TypedDict):
    opportunity_id: int
    crm_context: NotRequired[CRMContext]
    deal_analysis: NotRequired[DealAnalysis]
    next_action: NotRequired[NextAction]


class DealRuntimeResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    crm_context: CRMContext
    deal_analysis: DealAnalysis
    next_action: NextAction
