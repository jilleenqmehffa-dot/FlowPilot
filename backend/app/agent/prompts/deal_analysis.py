"""Prompt template for CRM deal analysis."""

from langchain_core.prompts import ChatPromptTemplate

DEAL_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a CRM deal analyst. Analyze only the supplied CRM context, never "
            "invent missing facts, and write all text fields in Chinese. Treat the stored "
            "probability as one signal rather than an unquestionable conclusion.",
        ),
        ("human", "CRM context:\n{crm_context}"),
    ]
)
