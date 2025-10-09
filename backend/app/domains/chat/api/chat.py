"""
채팅 API 엔드포인트
LangGraph 에이전트를 통한 대화형 추천 + 스레드 관리
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, List, Optional
import json
import uuid
from datetime import datetime

from app.shared.models.schemas import ChatMessage, ChatResponse, ChatThread, ChatHistory
from app.core.orchestrator import KetoCoachAgent
from app.core.database import supabase
from app.tools.shared.profile_tool import user_profile_tool
import os
import logging

# 로그 게이팅: 장문/민감 디버그 로그는 ENV로 제어
DEBUG_VERBOSE = os.getenv("DEBUG_VERBOSE", "false").lower() == "true"
logger = logging.getLogger("chat")

def dbg(msg: str):
    if DEBUG_VERBOSE:
        print(msg)
from app.tools.shared.profile_tool import user_profile_tool

router = APIRouter(prefix="/chat", tags=["chat"])

async def ensure_thread(user_id: Optional[str], guest_id: Optional[str], thread_id: Optional[str] = None) -> dict:
    """스레드가 존재하는지 확인하고, 없으면 생성"""
    try:
        dbg(f"🔍 ensure_thread 호출: user_id={user_id}, guest_id={guest_id}, thread_id={thread_id}")
        
        # thread_id가 제공된 경우 해당 스레드 조회
        if thread_id:
            dbg(f"🔍 기존 스레드 조회 중: {thread_id}")
            response = supabase.table("chat_thread").select("*").eq("id", thread_id).execute()
            dbg(f"🔍 스레드 조회 결과: {len(response.data) if response.data else 0}개 스레드")
            if response.data:
                dbg(f"✅ 기존 스레드 발견: id={response.data[0]['id']}, title={response.data[0]['title']}")
                return response.data[0]
            else:
                dbg("⚠️ 해당 스레드가 존재하지 않음, 새로 생성")
        
        # user_id와 guest_id가 모두 없으면 게스트로 처리
        if not user_id and not guest_id:
            guest_id = str(uuid.uuid4())
            dbg(f"🎭 게스트 ID 자동 생성: {guest_id}")
        
        # 새 스레드 생성
        new_thread_id = str(uuid.uuid4())
        new_thread = {
            "id": new_thread_id,
            "title": "새 채팅",
            "user_id": user_id,
            "guest_id": guest_id,
            "last_message_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        dbg(f"🆕 새 스레드 생성 중: id={new_thread['id']}, title={new_thread['title']}")
        result = supabase.table("chat_thread").insert(new_thread).execute()
        dbg(f"🔍 스레드 생성 결과: id={result.data[0]['id'] if result.data else 'None'}")
        
        created_thread = result.data[0] if result.data else new_thread
        dbg(f"✅ 스레드 생성 완료: id={created_thread['id']}, title={created_thread['title']}")
        return created_thread
        
    except Exception as e:
        print(f"❌ 스레드 생성/조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"스레드 처리 실패: {str(e)}")

async def insert_chat_message(thread_id: str, role: str, message: str, user_id: Optional[str] = None, guest_id: Optional[str] = None) -> dict:
    """채팅 메시지를 데이터베이스에 저장"""
    try:
        dbg(f"💾 메시지 저장 시작: thread_id={thread_id}, role={role}, message={message[:50]}...")
        dbg(f"💾 사용자 정보: user_id={user_id}, guest_id={guest_id}")
        
        # user_id와 guest_id가 모두 없으면 게스트로 처리
        if not user_id and not guest_id:
            guest_id = str(uuid.uuid4())
            dbg(f"🎭 메시지 저장용 게스트 ID 자동 생성: {guest_id}")
        
        chat_data = {
            "thread_id": thread_id,
            "role": role,
            "message": message,
            "user_id": user_id,
            "guest_id": guest_id,
            "message_uuid": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        dbg(f"💾 저장할 데이터: thread_id={chat_data['thread_id']}, role={chat_data['role']}, message={chat_data['message'][:30]}...")
        
        # 게스트 사용자는 데이터베이스에 저장하지 않음 (SessionStorage만 사용)
        if guest_id and not user_id:
            dbg(f"🎭 게스트 사용자 - 데이터베이스 저장 건너뛰기: guest_id={guest_id}")
            return chat_data  # 데이터베이스 저장 없이 데이터만 반환
        
        result = supabase.table("chat").insert(chat_data).execute()
        dbg(f"💾 저장 결과: id={result.data[0]['id'] if result.data else 'None'}")
        return result.data[0] if result.data else chat_data
        
    except Exception as e:
        print(f"❌ 메시지 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"메시지 저장 실패: {str(e)}")

async def update_thread_last_message(thread_id: str):
    """스레드의 마지막 메시지 시간 업데이트"""
    try:
        supabase.table("chat_thread").update({
            "last_message_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", thread_id).execute()
    except Exception as e:
        print(f"❌ 스레드 업데이트 실패: {e}")

# 중복 요청 방지를 위한 캐시 (메모리 기반)
import hashlib
import asyncio
import time

_request_cache = {}
_dedupe_lock = asyncio.Lock()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """
    대화형 키토 코치 채팅 엔드포인트
    
    - 레시피 추천: "아침에 먹을만한 한식 키토 뭐 있어?"
    - 식당 찾기: "역삼역 근처 키토 가능한 식당 알려줘"
    - 식단표 생성: "7일 식단표 만들어줘"
    """
    import uuid
    request_id = str(uuid.uuid4())[:8]
    
    # 중복 요청 방지 임시 비활성화 (게스트 사용자 테스트용)
    # raw_user = request.user_id or request.guest_id or "anon"
    # msg_norm = (request.message or "").strip()
    # msg_hash = hashlib.sha256(msg_norm.encode("utf-8")).hexdigest()[:16]  # 짧게
    # 
    # cache_key = f"{raw_user}:{msg_hash}"
    # current_time = time.time()
    # 
    # async with _dedupe_lock:
    #     last_time = _request_cache.get(cache_key)
    #     if last_time and (current_time - last_time) < 30:  # 30초로 연장
    #         print(f"🚫 중복 요청 차단! [ID: {request_id}] '{request.message}' (Δ {current_time - last_time:.2f}s)")
    #         raise HTTPException(status_code=429, detail="Too many requests")
    #     _request_cache[cache_key] = current_time
    # 
    # # 오래된 캐시 간단 청소
    # if len(_request_cache) > 5000:
    #     _request_cache.clear()
    
    print(f"🔥 DEBUG: chat_endpoint 진입! [ID: {request_id}] 메시지: '{request.message}'")
    
    # 게스트에서 로그인으로 전환 시 잘못된 요청 방지
    if request.user_id and request.guest_id:
        print(f"⚠️ 잘못된 요청: user_id와 guest_id가 동시에 전달됨")
        raise HTTPException(
            status_code=400, 
            detail="Cannot use both user_id and guest_id simultaneously"
        )
    
    try:
        # 스레드 확인/생성
        thread = await ensure_thread(request.user_id, request.guest_id, request.thread_id)
        thread_id = thread["id"]
        
        # 스레드에서 사용할 user_id와 guest_id 가져오기
        thread_user_id = thread.get("user_id")
        thread_guest_id = thread.get("guest_id")
        
        # 게스트 사용자의 경우 전달받은 chat_history 사용, 로그인 사용자는 DB에서 조회
        if request.guest_id and request.chat_history:
            # 게스트 사용자: 프론트엔드에서 전달받은 SessionStorage 데이터를 ChatHistory 객체로 변환
            converted_history = []
            for msg in request.chat_history:
                try:
                    # SessionStorage 데이터를 ChatHistory 형식으로 변환
                    chat_msg = ChatHistory(
                        id=int(msg.get('id', 0)) if msg.get('id') else 0,
                        thread_id=thread_id,
                        role=msg.get('role', ''),
                        message=msg.get('message', ''),
                        created_at=datetime.fromisoformat(msg.get('created_at', '').replace('Z', '+00:00'))
                    )
                    converted_history.append(chat_msg)
                except Exception as e:
                    print(f"⚠️ 게스트 메시지 변환 오류: {e}, 메시지: {msg}")
                    continue
            
            chat_history = converted_history
            print(f"🎭 게스트 사용자 채팅 히스토리 변환 완료: {len(chat_history)}개 메시지")
        else:
            # 로그인 사용자: DB에서 조회
            print(f"📚 로그인 사용자 대화 내용 조회 중... (thread_id: {thread_id})")
            print(f"🔍 thread_id 타입: {type(thread_id)}, 값: {repr(thread_id)}")
            
            if thread_id:
                history_response = supabase.table("chat").select("*").eq("thread_id", thread_id).order("created_at", desc=True).limit(20).execute()
                print(f"🔍 Supabase 응답: {len(history_response.data) if history_response.data else 0}개 메시지")
            else:
                print("⚠️ thread_id가 None이므로 대화 히스토리 조회 건너뜀")
                history_response = type('obj', (object,), {'data': []})()
            
            # 대화 히스토리를 역순으로 정렬 (오래된 것부터)
            chat_history = list(reversed(history_response.data)) if history_response.data else []
            print(f"📖 조회된 대화 히스토리: {len(chat_history)}개 메시지")
        
        # 사용자 메시지 저장
        await insert_chat_message(
            thread_id=thread_id,
            role="user",
            message=request.message,
            user_id=thread_user_id,
            guest_id=thread_guest_id
        )
        
        # 게스트 사용자가 아닌 경우에만 저장 후 히스토리 재조회
        if not (request.guest_id and request.chat_history):
            # 로그인 사용자만 저장 후 다시 히스토리 조회 (저장된 메시지 포함)
            chat_history = await get_chat_history(thread_id, limit=50)
            print(f"📚 저장 후 히스토리 조회: {len(chat_history)}개 메시지")
            
            # 디버그: 실제 조회된 데이터 확인
            if chat_history:
                first_msg = chat_history[0]
                last_msg = chat_history[-1]
                print(f"🔍 첫 번째 메시지: id={first_msg.id}, role={first_msg.role}, message={first_msg.message[:20]}...")
                print(f"🔍 마지막 메시지: id={last_msg.id}, role={last_msg.role}, message={last_msg.message[:20]}...")
            else:
                print("⚠️ 대화 히스토리가 비어있습니다!")
        else:
            print(f"🎭 게스트 사용자 - 기존 chat_history 유지: {len(chat_history)}개 메시지")
        
        # 키토 코치 오케스트레이터 실행
        print(f"🚀 DEBUG: chat API 요청 받음 [ID: {request_id}] - '{request.message}'")
        agent = KetoCoachAgent()
        # 오케스트레이터에 user_id 정보 포함해서 전달
        profile_with_user_id = request.profile or {}
        if thread_user_id:
            profile_with_user_id["user_id"] = thread_user_id
        
        # user_id가 있으면 서버에서 프로필 자동 병합
        if thread_user_id:
            try:
                prefs = await user_profile_tool.get_user_preferences(thread_user_id)
                if prefs and isinstance(prefs.get("data"), dict):
                    p = prefs["data"]
                    profile_with_user_id.setdefault("allergies", p.get("allergies") or [])
                    profile_with_user_id.setdefault("dislikes", p.get("dislikes") or [])
                    if p.get("goals_kcal") is not None:
                        profile_with_user_id.setdefault("goals_kcal", p.get("goals_kcal"))
                    if p.get("goals_carbs_g") is not None:
                        profile_with_user_id.setdefault("goals_carbs_g", p.get("goals_carbs_g"))
            except Exception as e:
                print(f"⚠️ 프로필 자동 병합 실패: {e}")

        result = await agent.process_message(
            message=request.message,
            location=request.location,
            radius_km=request.radius_km or 5.0,
            profile=profile_with_user_id,
            chat_history=chat_history,
            thread_id=thread_id
        )
        print(f"✅ DEBUG: 오케스트레이터 결과 [ID: {request_id}] - intent: {result.get('intent', 'unknown')}")
        
        # AI 응답 저장
        await insert_chat_message(
            thread_id=thread_id,
            role="assistant",
            message=result.get("response", ""),
            user_id=thread_user_id,
            guest_id=thread_guest_id
        )
        
        # 스레드 제목 업데이트 (첫 메시지인 경우 또는 새 채팅인 경우)
        if thread["title"] == "새 채팅" or not thread["title"] or thread["title"].strip() == "":
            title = request.message[:30] + ("..." if len(request.message) > 30 else "")
            supabase.table("chat_thread").update({
                "title": title,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", thread_id).execute()
        
        # 스레드 마지막 메시지 시간 업데이트
        await update_thread_last_message(thread_id)
        
        # AI 응답 배열 생성
        assistant_batch = [{
            "role": "assistant",
            "message": result.get("response", "")
        }]
        
        # ChatResponse 스키마 대신 딕셔너리로 반환하여 meal_plan_data 포함
        response_data = {
            "response": result.get("response", "죄송합니다. 응답을 생성할 수 없습니다."),
            "intent": result.get("intent", "unknown"),
            "results": result.get("results"),
            "session_id": thread_id,  # 호환성을 위해 session_id로도 반환
            "thread_id": thread_id,
            "assistantBatch": assistant_batch
        }
        
        # 식단 관련 응답인 경우 meal_plan_data 추가
        if result.get("meal_plan_data"):
            response_data["meal_plan_data"] = result.get("meal_plan_data")
        
        return response_data
        
    except Exception as e:
        print(f"❌ 채팅 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")

@router.get("/threads", response_model=List[ChatThread])
async def get_chat_threads(
    user_id: Optional[str] = Query(None, description="사용자 ID (로그인 시)"),
    guest_id: Optional[str] = Query(None, description="게스트 ID (비로그인 시)"),
    limit: int = Query(20, description="조회할 스레드 수")
):
    """사용자/게스트의 채팅 스레드 목록 조회"""
    try:
        print(f"🔍 스레드 목록 조회 요청 - user_id: {user_id}, guest_id: {guest_id}")
        
        if not user_id and not guest_id:
            print("⚠️ user_id와 guest_id가 모두 없음 - 빈 목록 반환")
            return []
        
        # 쿼리 조건 구성
        query = supabase.table("chat_thread").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        if guest_id:
            query = query.eq("guest_id", guest_id)
        
        # 최신 순으로 정렬하고 제한
        response = query.order("last_message_at", desc=True).limit(limit).execute()
        
        threads = []
        for thread in response.data:
            threads.append(ChatThread(
                id=thread["id"],
                title=thread["title"],
                last_message_at=datetime.fromisoformat(thread["last_message_at"].replace('Z', '+00:00')),
                created_at=datetime.fromisoformat(thread["created_at"].replace('Z', '+00:00'))
            ))
        
        return threads
        
    except Exception as e:
        print(f"❌ 스레드 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"스레드 목록 조회 실패: {str(e)}")

@router.post("/threads/new", response_model=ChatThread)
async def create_new_thread(
    user_id: Optional[str] = Query(None, description="사용자 ID (로그인 시)"),
    guest_id: Optional[str] = Query(None, description="게스트 ID (비로그인 시)")
):
    """새 채팅 스레드 생성"""
    try:
        print(f"🆕 새 스레드 생성 요청 - user_id: {user_id}, guest_id: {guest_id}")
        
        # 스레드 생성
        thread = await ensure_thread(user_id, guest_id, None)
        
        return ChatThread(
            id=thread["id"],
            title=thread["title"],
            last_message_at=thread["last_message_at"],
            created_at=thread["created_at"]
        )
        
    except Exception as e:
        print(f"❌ 새 스레드 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"새 스레드 생성 중 오류 발생: {str(e)}")

@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """채팅 스레드 삭제"""
    try:
        print(f"🗑️ 스레드 삭제 요청 - thread_id: {thread_id}")
        
        # 스레드와 관련된 모든 메시지 삭제
        supabase.table("chat").delete().eq("thread_id", thread_id).execute()
        
        # 스레드 삭제
        supabase.table("chat_thread").delete().eq("id", thread_id).execute()
        
        print(f"✅ 스레드 삭제 완료: {thread_id}")
        return {"message": "스레드가 성공적으로 삭제되었습니다"}
        
    except Exception as e:
        print(f"❌ 스레드 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"스레드 삭제 중 오류 발생: {str(e)}")

@router.get("/history/{thread_id}", response_model=List[ChatHistory])
async def get_chat_history(
    thread_id: str,
    limit: int = Query(20, description="조회할 메시지 수"),
    before: Optional[str] = Query(None, description="이전 메시지 ID (페이징용)")
):
    """특정 스레드의 채팅 기록 조회"""
    try:
        print(f"🔍 get_chat_history 호출: thread_id={thread_id}, limit={limit}, before={before} (type: {type(before)})")
        
        # 게스트 사용자 처리: SessionStorage만 사용하므로 빈 배열 반환
        if thread_id.startswith("guest-"):
            guest_id = thread_id.replace("guest-", "")
            print(f"🎭 게스트 사용자 채팅 히스토리 조회: guest_id={guest_id} - SessionStorage만 사용하므로 빈 배열 반환")
            return []  # 게스트는 데이터베이스에서 조회하지 않음
        
        # 로그인 사용자는 thread_id로 조회
        query = supabase.table("chat").select("*").eq("thread_id", thread_id)
        
        # 페이징 처리 (before 매개변수가 올바른 문자열일 때만)
        # Query 객체가 전달되는 경우를 방지
        if before and hasattr(before, 'strip') and isinstance(before, str) and before.strip():
            # before가 created_at인 경우
            try:
                before_time = datetime.fromisoformat(before.replace('Z', '+00:00'))
                query = query.lt("created_at", before_time.isoformat())
            except:
                # before가 ID인 경우
                try:
                    query = query.lt("id", int(before))
                except (ValueError, TypeError):
                    # ID 변환 실패 시 무시
                    pass
        
        # 시간 순으로 정렬하고 제한
        response = query.order("created_at", desc=False).limit(limit).execute()
        
        messages = []
        for msg in response.data:
            messages.append(ChatHistory(
                id=msg["id"],
                thread_id=msg["thread_id"],
                role=msg["role"],
                message=msg["message"],
                created_at=datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
            ))
        
        return messages
        
    except Exception as e:
        print(f"❌ 채팅 기록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 기록 조회 실패: {str(e)}")

@router.post("/stream")
async def chat_stream(request: ChatMessage):
    """
    스트리밍 채팅 엔드포인트
    실시간으로 응답을 스트리밍
    """
    print(f"🌊 DEBUG: chat_stream 진입! 메시지: '{request.message}'")
    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            # 스레드 확인/생성
            thread = await ensure_thread(request.user_id, request.guest_id, request.thread_id)
            thread_id = thread["id"]
            
            # 스레드에서 사용할 user_id와 guest_id 가져오기
            thread_user_id = thread.get("user_id")
            thread_guest_id = thread.get("guest_id")
            
            # 사용자 메시지 저장
            await insert_chat_message(
                thread_id=thread_id,
                role="user",
                message=request.message,
                user_id=thread_user_id,
                guest_id=thread_guest_id
            )
            
            # 에이전트를 통한 스트리밍 응답
            agent = KetoCoachAgent()
            full_response = ""
            # 일반/스트리밍 경로 모두에서 user_id를 프로필에 일관 주입
            profile_with_user_id = request.profile or {}
            if thread_user_id:
                profile_with_user_id["user_id"] = thread_user_id
                # 스트리밍 경로도 서버에서 프로필 자동 병합
                try:
                    prefs = await user_profile_tool.get_user_preferences(thread_user_id)
                    if prefs and isinstance(prefs.get("data"), dict):
                        p = prefs["data"]
                        profile_with_user_id.setdefault("allergies", p.get("allergies") or [])
                        profile_with_user_id.setdefault("dislikes", p.get("dislikes") or [])
                        if p.get("goals_kcal") is not None:
                            profile_with_user_id.setdefault("goals_kcal", p.get("goals_kcal"))
                        if p.get("goals_carbs_g") is not None:
                            profile_with_user_id.setdefault("goals_carbs_g", p.get("goals_carbs_g"))
                except Exception as e:
                    print(f"⚠️(stream) 프로필 자동 병합 실패: {e}")
            async for chunk in agent.stream_response(
                message=request.message,
                location=request.location,
                radius_km=request.radius_km or 5.0,
                profile=profile_with_user_id
            ):
                full_response += chunk.get("content", "")
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            # AI 응답 저장
            await insert_chat_message(
                thread_id=thread_id,
                role="assistant",
                message=full_response,
                user_id=thread_user_id,
                guest_id=thread_guest_id
            )
            
            # 스레드 업데이트
            await update_thread_last_message(thread_id)
                
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

@router.get("/history_legacy/{session_id}")
async def get_chat_history_legacy(session_id: str):
    """레거시 호환성을 위한 세션 기반 채팅 기록 조회"""
    try:
        # session_id를 thread_id로 사용
        response = supabase.table("chat").select("*").eq("thread_id", session_id).order("created_at", desc=False).execute()
        
        messages = []
        for msg in response.data:
            messages.append({
                "role": msg["role"],
                "content": msg["message"],
                "tool_calls": msg.get("tool_calls"),
                "created_at": msg["created_at"]
            })
        
        return {
            "session_id": session_id,
            "messages": messages
        }
        
    except Exception as e:
        print(f"❌ 레거시 채팅 기록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 기록 조회 실패: {str(e)}")