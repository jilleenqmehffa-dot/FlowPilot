"""LangGraph runtime for the fixed CRM deal decision flow."""

from collections.abc import Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from backend.app.agent.context import CRMContextProvider
from backend.app.agent.llm import create_deepseek_model
from backend.app.agent.prompts import DEAL_ANALYSIS_PROMPT, NEXT_ACTION_PROMPT
from backend.app.agent.schemas import (
    CRMContext,
    DealAnalysis,
    DealRuntimeResult,
    DealRuntimeState,
    NextAction,
)


class DealRuntime:
    """Compiled fixed-order graph: context -> analysis -> next action."""

    def __init__(
        self,
        context_loader: Callable[[int], CRMContext],
        deal_analysis_chain: Runnable[dict[str, str], DealAnalysis],
        next_action_chain: Runnable[dict[str, str], NextAction],
    ) -> None:
        self.context_loader = context_loader
        self.deal_analysis_chain = deal_analysis_chain
        self.next_action_chain = next_action_chain
        self.graph = self._compile_graph()

    def run(self, opportunity_id: int) -> DealRuntimeResult:
        if opportunity_id <= 0:
            raise ValueError("opportunity_id must be greater than 0")
        state = self.graph.invoke({"opportunity_id": opportunity_id})
        return DealRuntimeResult(
            crm_context=state["crm_context"],
            deal_analysis=state["deal_analysis"],
            next_action=state["next_action"],
        )

    def _compile_graph(self):
        workflow = StateGraph(DealRuntimeState)
        workflow.add_node("get_crm_context", self._get_crm_context)
        workflow.add_node("deal_analysis", self._analyze_deal)
        workflow.add_node("next_action", self._recommend_next_action)
        workflow.add_edge(START, "get_crm_context")
        workflow.add_edge("get_crm_context", "deal_analysis")
        workflow.add_edge("deal_analysis", "next_action")
        workflow.add_edge("next_action", END)
        return workflow.compile()

    def _get_crm_context(self, state: DealRuntimeState) -> dict[str, CRMContext]:
        return {"crm_context": self.context_loader(state["opportunity_id"])}

    def _analyze_deal(self, state: DealRuntimeState) -> dict[str, DealAnalysis]:
        context = state["crm_context"]
        analysis = self.deal_analysis_chain.invoke(
            {"crm_context": context.model_dump_json()}
        )
        return {"deal_analysis": analysis}

    def _recommend_next_action(self, state: DealRuntimeState) -> dict[str, NextAction]:
        context = state["crm_context"]
        analysis = state["deal_analysis"]
        action = self.next_action_chain.invoke(
            {
                "crm_context": context.model_dump_json(),
                "deal_analysis": analysis.model_dump_json(),
            }
        )
        return {"next_action": action}


def initialize_runtime(
    session: Session,
    *,
    model: BaseChatModel | None = None,
) -> DealRuntime:
    """Initialize the production runtime without making an LLM request."""

    chat_model = model or create_deepseek_model()
    context_provider = CRMContextProvider(session)
    deal_analysis_chain = DEAL_ANALYSIS_PROMPT | chat_model.with_structured_output(
        DealAnalysis
    )
    next_action_chain = NEXT_ACTION_PROMPT | chat_model.with_structured_output(
        NextAction
    )
    return DealRuntime(
        context_loader=context_provider.get,
        deal_analysis_chain=deal_analysis_chain,
        next_action_chain=next_action_chain,
    )
