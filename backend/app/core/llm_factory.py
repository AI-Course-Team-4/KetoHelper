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
    
    # 디버깅: 설정값 확인
    print(f"🔧 LLM Factory 설정: provider={provider_name}, model={selected_model}, max_tokens={selected_max_tokens}")

    common_kwargs: Dict[str, Any] = {
        "model": selected_model,
        "temperature": float(selected_temperature),
        "max_tokens": int(selected_max_tokens),
    }

    if provider_name == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        # OpenAI ChatOpenAI에서는 max_tokens 대신 max_tokens를 직접 전달
        openai_kwargs = common_kwargs.copy()
        
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            timeout=float(selected_timeout),
            max_tokens=int(selected_max_tokens),  # 명시적으로 max_tokens 설정
            model=selected_model,
            temperature=float(selected_temperature),
        )

    # 기본: Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    import os
    import warnings

    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is not set")

    # Google API 관련 경고 완전 비활성화
    warnings.filterwarnings("ignore", category=UserWarning, module="google")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="google")
    
    # ALTS credentials 오류 완전 방지
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
    os.environ.pop("GCLOUD_PROJECT", None)
    os.environ.pop("GOOGLE_CLOUD_PROJECT_ID", None)
    
    # Google API 인증 방식 강제 설정
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
    os.environ["GOOGLE_API_USE_MTLS"] = "false"
    os.environ["GOOGLE_API_USE_GRPC"] = "false"
    
    # Google API 라이브러리 설정
    os.environ["GOOGLE_CLOUD_DISABLE_GRPC"] = "true"
    os.environ["GOOGLE_CLOUD_DISABLE_MTLS"] = "true"

    return ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        timeout=float(selected_timeout),
        **common_kwargs,
    )
