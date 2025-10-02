# LLM 스위칭 — 팩토리 패턴 리팩터링 PRD (v1.0)
작성일: 2025-10-02 06:27  \
대상: 최종 키토 프로젝트 (BE: FastAPI, LangChain)  \
작성자: 팀4 (초보자 친화 버전)

---

## 1. 목적 (Why)
- **.env 스위치만** 바꿔서 **Gemini ↔ OpenAI** 모델을 자유롭게 교체한다.
- 각 에이전트 파일에서 LLM 생성 코드를 제거하고 **공통 팩토리**로 일원화한다.
- 성능/응답속도/비용 벤치를 **동일 테스트 스크립트**로 쉽게 비교한다.

### 배경
- 현재 `ChatGoogleGenerativeAI`를 각 파일에서 직접 생성 → 모델 교체 시 **동일한 변경을 여러 곳**에서 반복해야 함.
- 팀원이 초보 수준이므로 **간단한 구조** + **수정 범위 최소화**가 필요.

---

## 2. 범위 (Scope)
### 포함
- 공통 LLM 팩토리 파일 추가: `backend/app/core/llm_factory.py`
- 기존 5개 모듈의 LLM 초기화부를 **한 줄**로 교체
  - `backend/app/agents/chat_agent.py`
  - `backend/app/agents/meal_planner.py`
  - `backend/app/agents/place_search_agent.py`
  - `backend/app/core/orchestrator.py`
  - `backend/app/core/intent_classifier.py`
- 환경변수/설정 확장: `backend/app/core/config.py`, `.env.example`
- 벤치마크 실행 가이드

### 제외
- 프롬프트/비즈니스 로직 변경
- 임베딩 파이프라인 변경(이미 OpenAI embeddings 사용 중)

---

## 3. 성공 기준 (DoD)
- `.env`에서 `LLM_PROVIDER`만 바꿔도 모든 에이전트가 정상 동작
- 동일 프롬프트로 **5~10회 벤치** 실행 시
  - 타임아웃 0% (또는 팀 합의 기준 이하)
  - 평균 응답시간, 토큰사용량, 비용 로그가 수집됨
- 코드 변경 라인 수 최소 (각 파일 5~10줄 내)

---

## 4. 아키텍처 개요
```
[.env] ──▶ config.py ──▶ llm_factory.py ──▶ (ChatOpenAI | ChatGoogleGenerativeAI)
                                        └─▶ agents/orchestrator/intent_classifier
```
- 모든 소비자는 `create_chat_llm()`로만 LLM을 얻는다.
- LangChain **동일 인터페이스**(`ainvoke([...])`) 유지 → 호출부 변경 최소화.

---

## 5. 환경 변수 설계 (.env)
```bash
# 기본: Gemini
LLM_PROVIDER=gemini                 # gemini | openai
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=8192
LLM_TIMEOUT=60
GOOGLE_API_KEY=...your key...

# OpenAI로 전환(필요 시 주석 해제)
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini
# OPENAI_API_KEY=...your key...
```

---

## 6. 설정 코드 변경 (config.py)
```python
# backend/app/core/config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # ----- 공통 -----
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "openai"
    llm_model: str = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    # 공통 파라미터
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "8192"))
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))  # seconds

    # ----- Gemini -----
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # ----- OpenAI -----
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
```

---

## 7. LLM 팩토리 추가 (llm_factory.py)
```python
# backend/app/core/llm_factory.py
from typing import Optional, Any, Dict
from app.core.config import settings

def create_chat_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
):
    \"\"\"LangChain 호환 Chat LLM 인스턴스를 생성.
    반환 객체는 ainvoke([...])를 지원해야 한다.
    \"\"\"
    provider = (provider or settings.llm_provider).lower()
    model = model or settings.llm_model
    temperature = settings.llm_temperature if temperature is None else temperature
    max_tokens = settings.llm_max_tokens if max_tokens is None else max_tokens
    timeout = settings.llm_timeout if timeout is None else timeout

    common_kwargs: Dict[str, Any] = {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "timeout": int(timeout),
    }

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        return ChatOpenAI(api_key=settings.openai_api_key, **common_kwargs)

    # default: gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is not set")
    common_kwargs.pop("timeout", None)  # Gemini는 timeout 인자를 무시할 수 있음
    return ChatGoogleGenerativeAI(google_api_key=settings.google_api_key, **common_kwargs)
```

---

## 8. 각 파일 수정 가이드 (1줄 치환)
### 대상 파일
- `backend/app/agents/chat_agent.py`
- `backend/app/agents/meal_planner.py`
- `backend/app/agents/place_search_agent.py`
- `backend/app/core/orchestrator.py`
- `backend/app/core/intent_classifier.py`

### 변경 패턴
```python
# (삭제) from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.llm_factory import create_chat_llm

# (삭제) self.llm = ChatGoogleGenerativeAI(...)
self.llm = create_chat_llm()
```

> 기존 호출부(`await self.llm.ainvoke([...])`)는 그대로 사용.

---

## 9. 설치 & 실행
```bash
pip install langchain-openai langchain-google-genai

# .env 세팅 후
uvicorn app.main:app --reload
```

---

## 10. 벤치마크 계획 (간단)
- **테스트 스크립트**: 기존에 준비된 파일 사용 (예: `scripts/bench_llm.py` 가정)
- **프로시저**
  1) `.env`에서 `LLM_PROVIDER=gemini`로 설정 → 5~10회 반복 실행 → 평균/표준편차 기록  
  2) `LLM_PROVIDER=openai`로 변경 → 동일 횟수 실행 → 기록  
  3) 응답 품질은 간단 체크리스트로 주관 평가(예/아니오 5문항)
- **기록 항목**
  - average_latency_ms, p95_latency_ms
  - timeout_rate
  - output_tokens / total_tokens (가능 시)
  - subjective_quality_score (0~5)

> 결과는 CSV/MD 표 형태로 저장해서 비교(예: `reports/bench_YYYYMMDD.csv`).

---

## 11. 롤백 전략
- 문제가 생기면 `LLM_PROVIDER=gemini`로 즉시 되돌림
- PR은 다음 3개의 커밋으로 분리하여 위험 최소화
  1) add: `core/llm_factory.py`
  2) refactor: 5개 파일에 `create_chat_llm()` 적용
  3) chore: `config.py`/`.env.example` 업데이트

---

## 12. 리스크 & 완화
- **API Key 누락**: 팩토리에서 명시적 예외 발생 → 부트 단계에서 즉시 발견
- **토큰 한도 차이**: `LLM_MAX_TOKENS`로 출력 토큰 한도 통일, 긴 응답은 내부 프롬프트에서 요약지시
- **타임아웃**: `.env` `LLM_TIMEOUT` 조정 + 상위 레벨의 `asyncio.wait_for`와 중복 세팅 주의

---

## 13. 일정(제안)
- D0: PR 올리고 로컬 테스트 (0.5일)
- D1: 스테이징 배포 & 벤치(0.5일)
- D2: 결과 공유 & 기본값 결정(0.5일)

---

## 14. 수용 기준 (Acceptance)
- `.env` 한 줄로 모델 전환 가능 (코드 변경 불필요)
- 두 공급자 모두에서 주요 3기능(**챗봇/식단/식당검색**) 정상 동작
- 벤치 CSV/MD 결과가 저장되어 비교 가능

---

## 15. 참고
- 기존 파일 위치
  - `backend/app/agents/chat_agent.py`
  - `backend/app/agents/meal_planner.py`
  - `backend/app/agents/place_search_agent.py`
  - `backend/app/core/orchestrator.py`
  - `backend/app/core/intent_classifier.py`
  - `backend/app/core/config.py`
- 새 파일
  - `backend/app/core/llm_factory.py`

---

## 16. 부록 — 체크리스트 (초보자용)
- [ ] `pip install langchain-openai langchain-google-genai`
- [ ] `llm_factory.py` 생성 및 복붙
- [ ] 5개 파일에서 `self.llm = create_chat_llm()`로 교체
- [ ] `.env`에 `LLM_PROVIDER`, `LLM_MODEL`, 키 추가
- [ ] 로컬에서 Gemini로 동작 확인
- [ ] OpenAI로 전환 후 동작 확인
- [ ] 벤치 5~10회 실행 결과 저장
