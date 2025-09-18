"""
LangGraph 기반 키토 코치 에이전트 오케스트레이터
의도 분류 → 도구 실행 → 응답 생성의 전체 플로우 관리
"""

import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, BaseMessage
import json

from app.core.config import settings
from app.tools.recipe_rag import RecipeRAGTool
from app.tools.place_search import PlaceSearchTool
from app.tools.keto_score import KetoScoreCalculator
from app.agents.meal_planner import MealPlannerAgent

from typing_extensions import TypedDict

class AgentState(TypedDict):
    """에이전트 상태 관리 클래스"""
    messages: List[BaseMessage]
    intent: str
    slots: Dict[str, Any]
    results: List[Dict[str, Any]]
    response: str
    tool_calls: List[Dict[str, Any]]
    profile: Optional[Dict[str, Any]]
    location: Optional[Dict[str, float]]
    radius_km: float

class KetoCoachAgent:
    """키토 코치 메인 에이전트"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0.1
        )
        
        # 도구들 초기화
        self.recipe_rag = RecipeRAGTool()
        self.place_search = PlaceSearchTool()
        self.keto_score = KetoScoreCalculator()
        self.meal_planner = MealPlannerAgent()
        
        # 워크플로우 그래프 구성
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        
        workflow = StateGraph(AgentState)
        
        # 노드 추가
        workflow.add_node("router", self._router_node)
        workflow.add_node("recipe_rag", self._recipe_rag_node)
        workflow.add_node("place_search", self._place_search_node)
        workflow.add_node("meal_plan", self._meal_plan_node)
        workflow.add_node("memory_update", self._memory_update_node)
        workflow.add_node("answer", self._answer_node)
        
        # 시작점 설정
        workflow.set_entry_point("router")
        
        # 라우터에서 각 노드로의 조건부 엣지
        workflow.add_conditional_edges(
            "router",
            self._route_condition,
            {
                "recipe": "recipe_rag",
                "place": "place_search",
                "mealplan": "meal_plan",
                "memory": "memory_update",
                "other": "answer"
            }
        )
        
        # 모든 노드에서 answer로
        workflow.add_edge("recipe_rag", "answer")
        workflow.add_edge("place_search", "answer")
        workflow.add_edge("meal_plan", "answer")
        workflow.add_edge("memory_update", "answer")
        workflow.add_edge("answer", END)
        
        return workflow.compile()
    
    async def _router_node(self, state: AgentState) -> AgentState:
        """의도 분류 노드"""
        
        message = state["messages"][-1].content if state["messages"] else ""
        
        router_prompt = f"""
        사용자 메시지를 분석하여 의도와 슬롯을 추출하세요.
        
        사용자 메시지: "{message}"
        
        다음 JSON 형태로 응답하세요:
        {{
            "intent": "recipe|place|mealplan|memory|other",
            "slots": {{
                "location": "지역명 (예: 역삼역, 강남)",
                "radius": "검색 반경 (km)",
                "category": "음식 카테고리",
                "preferences": "선호사항",
                "allergies": "알레르기",
                "meal_type": "식사 타입 (아침/점심/저녁)",
                "days": "식단표 일수"
            }}
        }}
        
        의도 분류:
        - recipe: 레시피 추천 요청
        - place: 식당/장소 검색 요청
        - mealplan: 식단표 생성 요청
        - memory: 프로필/선호도 업데이트
        - other: 일반 대화/기타
        """
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=router_prompt)])
            
            # JSON 파싱
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                state["intent"] = result.get("intent", "other")
                state["slots"] = result.get("slots", {})
            else:
                state["intent"] = "other"
                state["slots"] = {}
            
            state["tool_calls"].append({
                "tool": "router",
                "intent": state["intent"],
                "slots": state["slots"]
            })
            
        except Exception as e:
            print(f"Router error: {e}")
            state["intent"] = "other"
            state["slots"] = {}
        
        return state
    
    def _route_condition(self, state: AgentState) -> str:
        """라우팅 조건 함수"""
        return state["intent"]
    
    async def _recipe_rag_node(self, state: AgentState) -> AgentState:
        """레시피 RAG 노드"""
        
        try:
            message = state.messages[-1].content if state.messages else ""
            
            # 프로필 정보 반영
            profile_context = ""
            if state.profile:
                allergies = state.profile.get("allergies", [])
                dislikes = state.profile.get("dislikes", [])
                if allergies:
                    profile_context += f"알레르기: {', '.join(allergies)}. "
                if dislikes:
                    profile_context += f"싫어하는 음식: {', '.join(dislikes)}. "
            
            # RAG 검색 실행
            search_results = await self.recipe_rag.search(
                query=message,
                profile_context=profile_context,
                max_results=5
            )
            
            state.results = search_results
            state.tool_calls.append({
                "tool": "recipe_rag",
                "query": message,
                "results_count": len(search_results)
            })
            
        except Exception as e:
            print(f"Recipe RAG error: {e}")
            state.results = []
        
        return state
    
    async def _place_search_node(self, state: AgentState) -> AgentState:
        """장소 검색 노드"""
        
        try:
            message = state.messages[-1].content if state.messages else ""
            
            # 위치 정보 추출
            lat = state.location.get("lat", 37.4979) if state.location else 37.4979  # 기본: 강남역
            lng = state.location.get("lng", 127.0276) if state.location else 127.0276
            
            # 검색 쿼리 개선
            query_improvement_prompt = f"""
            사용자 요청을 카카오 로컬 검색에 적합한 키워드로 변환하세요.
            
            사용자 요청: "{message}"
            
            키토 친화적인 검색 키워드 (1-3개)를 반환하세요:
            예시: "구이", "샤브샤브", "샐러드", "스테이크", "회"
            """
            
            llm_response = await self.llm.ainvoke([HumanMessage(content=query_improvement_prompt)])
            search_keywords = llm_response.content.strip().split(", ")
            
            all_places = []
            
            # 각 키워드로 검색
            for keyword in search_keywords[:3]:  # 최대 3개 키워드
                places = await self.place_search.search(
                    query=keyword.strip('"'),
                    lat=lat,
                    lng=lng,
                    radius=int(state.radius_km * 1000)
                )
                
                # 키토 스코어 계산
                for place in places:
                    score_result = self.keto_score.calculate_score(
                        name=place.get("name", ""),
                        category=place.get("category", ""),
                        address=place.get("address", "")
                    )
                    
                    place.update({
                        "keto_score": score_result["score"],
                        "why": score_result["reasons"],
                        "tips": score_result["tips"]
                    })
                    
                    all_places.append(place)
            
            # 중복 제거 및 정렬
            unique_places = {}
            for place in all_places:
                place_id = place.get("id", "")
                if place_id not in unique_places or place["keto_score"] > unique_places[place_id]["keto_score"]:
                    unique_places[place_id] = place
            
            # 키토 스코어 순 정렬
            sorted_places = sorted(
                unique_places.values(),
                key=lambda x: x["keto_score"],
                reverse=True
            )
            
            state.results = sorted_places[:10]  # 상위 10개
            state.tool_calls.append({
                "tool": "place_search",
                "keywords": search_keywords,
                "location": {"lat": lat, "lng": lng},
                "results_count": len(state.results)
            })
            
        except Exception as e:
            print(f"Place search error: {e}")
            state.results = []
        
        return state
    
    async def _meal_plan_node(self, state: AgentState) -> AgentState:
        """식단표 생성 노드"""
        
        try:
            # 슬롯에서 매개변수 추출
            days = state.slots.get("days", 7)
            
            # 프로필에서 제약 조건 추출
            kcal_target = None
            carbs_max = 30
            allergies = []
            dislikes = []
            
            if state.profile:
                kcal_target = state.profile.get("goals_kcal")
                carbs_max = state.profile.get("goals_carbs_g", 30)
                allergies = state.profile.get("allergies", [])
                dislikes = state.profile.get("dislikes", [])
            
            # 식단표 생성
            meal_plan = await self.meal_planner.generate_meal_plan(
                days=days,
                kcal_target=kcal_target,
                carbs_max=carbs_max,
                allergies=allergies,
                dislikes=dislikes
            )
            
            state.results = [meal_plan]
            state.tool_calls.append({
                "tool": "meal_planner",
                "days": days,
                "constraints": {
                    "kcal_target": kcal_target,
                    "carbs_max": carbs_max,
                    "allergies": allergies,
                    "dislikes": dislikes
                }
            })
            
        except Exception as e:
            print(f"Meal plan error: {e}")
            state.results = []
        
        return state
    
    async def _memory_update_node(self, state: AgentState) -> AgentState:
        """메모리/프로필 업데이트 노드"""
        
        try:
            message = state.messages[-1].content if state.messages else ""
            
            # 프로필 업데이트 정보 추출
            update_prompt = f"""
            사용자 메시지에서 프로필 업데이트 정보를 추출하세요.
            
            사용자 메시지: "{message}"
            
            JSON 형태로 응답하세요:
            {{
                "allergies": ["추가할 알레르기"],
                "dislikes": ["추가할 비선호 음식"],
                "goals_kcal": 목표칼로리숫자,
                "goals_carbs_g": 목표탄수화물그램
            }}
            
            업데이트할 항목만 포함하세요.
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=update_prompt)])
            
            # JSON 파싱 및 프로필 업데이트
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                updates = json.loads(json_match.group())
                if not state.profile:
                    state.profile = {}
                
                for key, value in updates.items():
                    if value:  # 빈 값이 아닌 경우만 업데이트
                        state.profile[key] = value
                
                state.tool_calls.append({
                    "tool": "memory_update",
                    "updates": updates
                })
            
        except Exception as e:
            print(f"Memory update error: {e}")
        
        return state
    
    async def _answer_node(self, state: AgentState) -> AgentState:
        """최종 응답 생성 노드"""
        
        try:
            message = state.messages[-1].content if state.messages else ""
            
            # 결과 기반 응답 생성
            context = ""
            if state.results:
                context = f"검색 결과: {json.dumps(state.results[:3], ensure_ascii=False, indent=2)}"
            
            answer_prompt = f"""
            사용자의 키토 식단 관련 질문에 친근하고 도움이 되는 답변을 해주세요.
            
            사용자 질문: "{message}"
            의도: {state.intent}
            검색 결과: {context}
            
            답변 가이드라인:
            1. 한국어로 자연스럽게 답변
            2. 키토 식단의 특성을 고려한 조언 포함
            3. 구체적이고 실용적인 정보 제공
            4. 검색 결과가 있으면 적극 활용
            5. 200자 내외로 간결하게
            
            검색 결과가 없는 경우 일반적인 키토 식단 조언을 제공하세요.
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=answer_prompt)])
            state.response = response.content
            
        except Exception as e:
            print(f"Answer generation error: {e}")
            state.response = "죄송합니다. 답변 생성 중 오류가 발생했습니다. 다시 시도해주세요."
        
        return state
    
    async def process_message(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """메시지 처리 메인 함수"""
        
        # 초기 상태 설정
        initial_state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "intent": "",
            "slots": {},
            "results": [],
            "response": "",
            "tool_calls": [],
            "profile": profile,
            "location": location,
            "radius_km": radius_km
        }
        
        # 워크플로우 실행
        final_state = await self.workflow.ainvoke(initial_state)
        
        return {
            "response": final_state.response,
            "intent": final_state.intent,
            "results": final_state.results,
            "tool_calls": final_state.tool_calls
        }
    
    async def stream_response(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """스트리밍 응답 생성"""
        
        # 노드별 스트리밍 이벤트 생성
        yield {"event": "start", "message": "처리를 시작합니다..."}
        
        # 의도 분류
        yield {"event": "routing", "message": "의도를 분석하고 있습니다..."}
        
        # 워크플로우 실행 (실제로는 위의 process_message와 동일)
        result = await self.process_message(message, location, radius_km, profile)
        
        # 도구 실행 이벤트들
        for tool_call in result.get("tool_calls", []):
            yield {
                "event": "tool_execution",
                "tool": tool_call["tool"],
                "message": f"{tool_call['tool']} 도구를 실행하고 있습니다..."
            }
        
        # 최종 응답
        yield {
            "event": "complete",
            "response": result["response"],
            "intent": result["intent"],
            "results": result["results"]
        }
