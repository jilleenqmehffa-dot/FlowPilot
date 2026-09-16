"""Public API for the FlowPilot CRM agent."""

from backend.app.agent.context import CRMContextProvider
from backend.app.agent.llm import create_deepseek_model
from backend.app.agent.runtime import DealRuntime, initialize_runtime
from backend.app.agent.schemas import (
    CRMContext,
    DealAnalysis,
    DealRuntimeResult,
    NextAction,
)

__all__ = [
    "CRMContext",
    "CRMContextProvider",
    "DealAnalysis",
    "DealRuntime",
    "DealRuntimeResult",
    "NextAction",
    "create_deepseek_model",
    "initialize_runtime",
]
