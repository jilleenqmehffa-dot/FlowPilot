"""Prompt template for the recommended next action."""

from langchain_core.prompts import ChatPromptTemplate

NEXT_ACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a CRM sales coach. Recommend exactly one concrete next action using "
            "the CRM context and deal analysis. Avoid duplicating an existing open task, "
            "do not invent people or facts, and write all text fields in Chinese.",
        ),
        (
            "human",
            "CRM context:\n{crm_context}\n\nDeal analysis:\n{deal_analysis}",
        ),
    ]
)
