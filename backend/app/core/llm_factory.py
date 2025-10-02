"""공통 LLM 팩토리.

환경 변수 기반으로 LangChain 호환 Chat LLM 인스턴스를 생성한다.
"""

from typing import Any, Dict, Optional

from app.core.config import settings


def create_chat_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
):
    """LangChain Chat LLM 인스턴스를 생성한다."""

    provider_name = (provider or settings.llm_provider).lower()
    selected_model = model or settings.llm_model
    selected_temperature = settings.llm_temperature if temperature is None else temperature
    selected_max_tokens = settings.llm_max_tokens if max_tokens is None else max_tokens
    selected_timeout = settings.llm_timeout if timeout is None else timeout

    common_kwargs: Dict[str, Any] = {
        "model": selected_model,
        "temperature": float(selected_temperature),
        "max_tokens": int(selected_max_tokens),
    }

    if provider_name == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        return ChatOpenAI(
            api_key=settings.openai_api_key,
            timeout=float(selected_timeout),
            **common_kwargs,
        )

    # 기본: Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is not set")

    return ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        **common_kwargs,
    )
