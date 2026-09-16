"""Structured values exchanged by CRM agent stages."""

from backend.app.agent.schemas.context import ActivityContext, CRMContext, TaskContext
from backend.app.agent.schemas.deal_analysis import DealAnalysis
from backend.app.agent.schemas.next_action import NextAction
from backend.app.agent.schemas.runtime import DealRuntimeResult, DealRuntimeState

__all__ = [
    "ActivityContext",
    "CRMContext",
    "DealAnalysis",
    "DealRuntimeResult",
    "DealRuntimeState",
    "NextAction",
    "TaskContext",
]
