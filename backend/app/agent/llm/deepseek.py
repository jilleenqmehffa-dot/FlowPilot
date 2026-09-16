"""Lazy DeepSeek chat-model construction."""

from langchain_deepseek import ChatDeepSeek

from backend.app.core.config import Settings, get_settings


def create_deepseek_model(settings: Settings | None = None) -> ChatDeepSeek:
    """Build the chat model without making an API request."""

    runtime_settings = settings or get_settings()
    if runtime_settings.deepseek_api_key is None:
        raise RuntimeError("Set DEEPSEEK_API_KEY before initializing the deal runtime")
    return ChatDeepSeek(
        model=runtime_settings.deepseek_model,
        api_key=runtime_settings.deepseek_api_key,
        base_url=runtime_settings.deepseek_base_url,
        temperature=runtime_settings.deepseek_temperature,
    )
