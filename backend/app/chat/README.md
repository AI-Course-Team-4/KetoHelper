# Chat 모듈 📱

키토 코치의 일반 채팅 및 대화 관리를 담당하는 모듈입니다.

## 📁 폴더 구조

```
chat/
├── agents/          # 채팅 에이전트들
├── api/            # 채팅 API 엔드포인트
├── prompts/        # 채팅용 프롬프트 템플릿
└── README.md       # 이 파일
```

## 🤖 에이전트 개인화 가이드 (NEW!)

### SimpleKetoCoachAgent 커스터마이징

이제 **개인 설정 파일**을 통해 코드 수정 없이 외부에서 에이전트를 개인화할 수 있습니다!

#### 1. 개인 설정 파일 생성

```bash
# 1. 개인 설정 파일 복사
cp backend/config/personal_config.py backend/config/.personal_config.py

# 2. 개인 설정 활성화
# .personal_config.py 파일에서 USE_PERSONAL_CONFIG = True로 변경
```

#### 2. 채팅 에이전트 설정 수정

```python
# backend/config/.personal_config.py
CHAT_AGENT_CONFIG = {
    "agent_name": "나만의 키토 코치",
    "prompt_file_name": "my_custom_prompt"  # 프롬프트 파일명 변경
}

# 전체 설정 활성화
USE_PERSONAL_CONFIG = True
```

#### 2. 개인 프롬프트 파일 생성

`prompts/` 폴더에 자신만의 프롬프트 파일을 생성하세요:

```python
# prompts/my_custom_prompt.py
GENERAL_CHAT_PROMPT = """
여기에 자신만의 프롬프트 템플릿을 작성하세요.
{message}와 {profile_context} 변수를 포함해야 합니다.
"""

# 또는
PROMPT = """자신만의 프롬프트..."""
```

#### 3. 에이전트 사용

```python
# 개인 설정이 자동으로 적용됩니다!
agent = SimpleKetoCoachAgent()

# 또는 런타임에 설정 오버라이드
my_agent = SimpleKetoCoachAgent(
    prompt_file_name="my_custom_prompt",
    agent_name="내 전용 키토 코치"
)
```

### 🔥 NEW! 장점들

1. **코드 수정 없음**: simple_agent.py 파일을 건드리지 않아도 됨
2. **Git 안전성**: .personal_config.py는 .gitignore에 포함되어 개인 설정 보호
3. **팀 협업**: 각자의 개인 설정을 가지면서 베이스 코드는 공유
4. **쉬운 전환**: USE_PERSONAL_CONFIG = False로 언제든 기본 설정으로 복원

## 📝 프롬프트 작성 가이드

### 프롬프트 파일 구조

프롬프트 파일은 다음 중 하나의 속성을 가져야 합니다:
- `GENERAL_CHAT_PROMPT`
- `PROMPT`

### 필수 변수

프롬프트에서 사용할 수 있는 변수들:
- `{message}`: 사용자의 입력 메시지
- `{profile_context}`: 사용자 프로필 정보 (알레르기, 선호도 등)

### 프롬프트 예시

```python
GENERAL_CHAT_PROMPT = """
당신은 친근한 키토 식단 전문가입니다.

사용자 질문: {message}
사용자 정보: {profile_context}

답변 스타일:
1. 친근하고 격려하는 톤
2. 과학적 근거 기반 조언
3. 실용적이고 구체적인 팁
4. 200-300자 내외 간결한 답변

특별 상황 처리:
- 인사말: 따뜻하게 응답하고 키토 도움 제안
- 감사 인사: 격려하며 추가 질문 유도
- 키토 무관 질문: 정중히 전문 분야 안내

답변해주세요.
"""
```

## 🔧 API 사용법

### 채팅 메시지 전송

```python
POST /api/chat/message
{
    "message": "안녕하세요, 키토 식단 시작하려고 해요",
    "profile": {
        "allergies": ["새우"],
        "goals_carbs_g": 20
    }
}
```

### 응답 형식

```json
{
    "response": "안녕하세요! 키토 식단을 시작하시는군요...",
    "intent": "general_chat",
    "tool_calls": [
        {
            "tool": "general_chat_agent",
            "message": "안녕하세요, 키토 식단 시작하려고 해요"
        }
    ]
}
```

## 🎯 사용 시나리오

### 1. 기본 채팅
- 키토 식단 관련 질문/답변
- 일반적인 인사 및 격려
- 키토 원칙 설명

### 2. 상담 및 조언
- 개인 상황에 맞는 키토 조언
- 부작용 대처법 안내
- 동기 부여 및 격려

### 3. 정보 안내
- 전문 서비스 연결 (레시피 검색, 식당 찾기)
- 키토 관련 일반 정보 제공
- 건강 관련 주의사항 안내

## 📚 개발자 팁

### 1. 프롬프트 테스트
새 프롬프트를 작성했다면 다양한 입력으로 테스트해보세요:
- 인사말: "안녕하세요", "고마워요"
- 키토 질문: "키토 부작용이 있나요?"
- 무관한 질문: "날씨가 어때요?"

### 2. 오류 처리
프롬프트 파일이 없거나 잘못된 경우 기본 프롬프트가 사용됩니다.

### 3. 디버깅
에이전트 초기화 시 콘솔에 출력되는 경고 메시지를 확인하세요.

## 🤝 협업 가이드

### 팀 작업 시 주의사항

1. **파일명 규칙**: `prompts/팀원이름_프롬프트목적.py`
2. **에이전트명 규칙**: "팀원이름 Keto Coach"
3. **테스트**: 자신의 프롬프트가 제대로 작동하는지 확인
4. **문서화**: 특별한 기능이 있다면 주석으로 설명

### 예시 팀 작업

```python
# prompts/junho_friendly_coach.py - 준호팀원의 친근한 코치
GENERAL_CHAT_PROMPT = """
준호의 특별한 친근한 키토 코치입니다...
"""

# agents/simple_agent.py에서 사용
junho_agent = SimpleKetoCoachAgent(
    prompt_file_name="junho_friendly_coach",
    agent_name="준호의 키토 친구"
)
```

---

💡 **문의사항이나 개선 아이디어가 있다면 팀 채널에서 공유해주세요!**
