"""
채팅 API 엔드포인트
LangGraph 에이전트를 통한 대화형 추천
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import uuid
from datetime import datetime

from app.shared.models.schemas import ChatMessage, ChatResponse
from app.chat.agents.simple_agent import SimpleKetoCoachAgent
from app.core.database import supabase

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """
    대화형 키토 코치 채팅 엔드포인트
    
    - 레시피 추천: "아침에 먹을만한 한식 키토 뭐 있어?"
    - 식당 찾기: "역삼역 근처 키토 가능한 식당 알려줘"
    - 식단표 생성: "7일 식단표 만들어줘"
    """
    try:
        # 세션 ID 생성
        session_id = str(uuid.uuid4())
        user_id = getattr(request, 'user_id', 'anonymous')
        
        # 사용자 메시지 저장 (Supabase)
        user_message_data = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "user",
            "content": request.message,
            "created_at": datetime.utcnow().isoformat()
        }
        # TODO: Supabase에 메시지 저장 구현
        
        # 간단한 에이전트 실행
        agent = SimpleKetoCoachAgent()
        result = await agent.process_message(
            message=request.message,
            location=request.location,
            radius_km=request.radius_km,
            profile=request.profile
        )
        
        # AI 응답 저장 (Supabase)
        assistant_message_data = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "assistant",
            "content": result.get("response", ""),
            "tool_calls": result.get("tool_calls"),
            "created_at": datetime.utcnow().isoformat()
        }
        # TODO: Supabase에 메시지 저장 구현
        
        return ChatResponse(
            response=result.get("response", "죄송합니다. 응답을 생성할 수 없습니다."),
            intent=result.get("intent", "unknown"),
            results=result.get("results"),
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")

@router.post("/stream")
async def chat_stream(request: ChatMessage):
    """
    스트리밍 채팅 엔드포인트
    실시간으로 응답을 스트리밍
    """
    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            session_id = str(uuid.uuid4())
            user_id = getattr(request, 'user_id', 'anonymous')
            
            # 사용자 메시지 저장 (Supabase)
            user_message_data = {
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": request.message,
                "created_at": datetime.utcnow().isoformat()
            }
            # TODO: Supabase에 메시지 저장 구현
            
            # 에이전트를 통한 스트리밍 응답
            agent = SimpleKetoCoachAgent()
            async for chunk in agent.stream_response(
                message=request.message,
                location=request.location,
                radius_km=request.radius_km,
                profile=request.profile
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            error_chunk = {
                "error": True,
                "message": f"스트리밍 중 오류 발생: {str(e)}"
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """특정 세션의 채팅 기록 조회"""
    try:
        # Supabase로 메시지 조회
        # TODO: Supabase에서 메시지 조회 구현
        messages = []
        
        # 세션 ID로 필터링
        session_messages = [
            msg for msg in messages 
            if msg.get("session_id") == session_id
        ]
        
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "tool_calls": msg.get("tool_calls"),
                    "created_at": msg.get("created_at")
                }
                for msg in session_messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 기록 조회 실패: {str(e)}")
