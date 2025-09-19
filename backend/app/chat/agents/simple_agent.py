"""
간단한 키토 코치 에이전트 (LangGraph 호환성 문제 해결용)
"""

from typing import Dict, Any, Optional
# OpenAI 관련 import (주석 처리 - Gemini로 교체)
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from app.core.config import settings
from app.shared.tools.hybrid_search import hybrid_search_tool

class SimpleKetoCoachAgent:
    """간단한 키토 코치 에이전트"""
    
    def __init__(self):
        try:
            # OpenAI 초기화 (주석 처리 - Gemini로 교체)
            # self.llm = ChatOpenAI(
            #     model=settings.llm_model,
            #     api_key=settings.openai_api_key,
            #     temperature=0.1
            # )
            
            # Gemini 초기화
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature,
                max_tokens=settings.gemini_max_tokens
            )
        except Exception as e:
            print(f"Gemini AI 초기화 실패: {e}")
            self.llm = None
    
    async def process_message(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """간단한 메시지 처리"""
        
        try:
            if not self.llm:
                return {
                    "response": "AI 서비스가 현재 사용할 수 없습니다. Google API 키를 확인해주세요.",
                    "intent": "error",
                    "results": [],
                    "tool_calls": []
                }
            
            # 간단한 의도 분류
            intent = self._classify_intent(message)
            
            # 의도에 따른 응답 생성
            response = await self._generate_response(message, intent, profile)
            
            return {
                "response": response,
                "intent": intent,
                "results": [],
                "tool_calls": [{"tool": "simple_agent", "message": message}]
            }
            
        except Exception as e:
            return {
                "response": f"처리 중 오류가 발생했습니다: {str(e)}",
                "intent": "error",
                "results": [],
                "tool_calls": []
            }
    
    def _classify_intent(self, message: str) -> str:
        """간단한 의도 분류"""
        
        message_lower = message.lower()
        
        # 레시피 관련 키워드 (구체적인 음식/요리 관련만)
        recipe_keywords = [
            "레시피", "요리", "만들", "조리", "식단", "추천", "메뉴", "키토",
            "불고기", "샐러드", "스테이크", "볶음", "구이", "찜", "튀김",
            "아침", "점심", "저녁", "간식", "디저트", "국", "찌개", "볶음밥"
        ]
        
        if any(word in message_lower for word in recipe_keywords):
            return "recipe"
        elif any(word in message_lower for word in ["식당", "맛집", "근처", "주변"]):
            return "place"
        elif any(word in message_lower for word in ["식단표", "계획", "일주일", "7일"]):
            return "mealplan"
        elif any(word in message_lower for word in ["알레르기", "프로필", "설정"]):
            return "memory"
        else:
            return "other"
    
    async def _generate_response(
        self, 
        message: str, 
        intent: str, 
        profile: Optional[Dict[str, Any]]
    ) -> str:
        """의도에 따른 응답 생성"""
        
        try:
            # 프로필 정보 컨텍스트
            profile_context = ""
            if profile:
                if profile.get("allergies"):
                    profile_context += f"알레르기: {', '.join(profile['allergies'])}. "
                if profile.get("dislikes"):
                    profile_context += f"비선호 음식: {', '.join(profile['dislikes'])}. "
                if profile.get("goals_carbs_g"):
                    profile_context += f"목표 탄수화물: {profile['goals_carbs_g']}g/일. "
            
            # 의도별 프롬프트
            print(f"🔧 의도 분류 결과: {intent}")
            if intent == "recipe":
                # 하이브리드 검색 및 스마트 응답 생성
                try:
                    print(f"🔍 하이브리드 검색 실행: '{message}'")
                    recipes = await hybrid_search_tool.search(message, profile_context, max_results=3)
                    
                    print(f"🔧 검색 결과: {len(recipes)}개")
                    if recipes:
                        first_recipe = recipes[0]
                        print(f"🔧 첫 번째 결과 전략: {first_recipe.get('search_strategy', 'unknown')}")
                        print(f"🔧 첫 번째 결과 메시지: {first_recipe.get('search_message', '')}")
                    
                    # 하이브리드 방식으로 응답 생성 (AI 모델 호출 없이 직접 반환)
                    print(f"🔧 하이브리드 응답 생성 시작...")
                    try:
                        response = await self._generate_hybrid_recipe_response(message, recipes, profile_context)
                        print(f"🔧 하이브리드 응답 생성 완료")
                        return response  # AI 모델 호출 없이 직접 반환
                    except Exception as e:
                        print(f"🔧 하이브리드 응답 생성 오류: {e}")
                        # ===== 새로 만든 부분 시작: 오류시 Gemini 폴백 =====
                        # 오류 발생 시 Gemini 레시피 생성으로 폴백
                        print(f"🤖 하이브리드 오류 - Gemini로 '{message}' 레시피 생성 시작")
                        return await self._generate_gemini_recipe(message, profile_context)
                        # ===== 새로 만든 부분 끝: 오류시 Gemini 폴백 =====
                        
                        # 기존 하드코딩된 오류 응답 (주석 처리)
                        # return f"""
                        # 🚫 '{message}'에 대한 레시피를 찾을 수 없습니다.
                        # 
                        # 키토 식단에 도움이 될 수 있는 일반적인 조언을 드릴게요:
                        # 
                        # 💡 키토 식단의 기본 원칙:
                        # - 탄수화물: 20-50g/일 이하
                        # - 지방: 70-80% (고품질 지방)
                        # - 단백질: 15-25% (적당량)
                        # 
                        # 🍽️ '{message}'에 대한 키토 조언:
                        # - 키토 친화적인 대체 재료 사용
                        # - 저탄수화물 채소 중심으로 구성
                        # - 고품질 지방과 단백질 포함
                        # 
                        # 더 구체적인 레시피를 원하시면 다른 키워드로 검색해보세요!
                        # """
                    
                except Exception as e:
                    print(f"Supabase 하이브리드 검색 오류: {e}")
                    # ===== 새로 만든 부분 시작: DB 오류시 Gemini 폴백 =====
                    # 오류 발생 시 Gemini 레시피 생성으로 폴백
                    print(f"🤖 DB 오류 - Gemini로 '{message}' 레시피 생성 시작")
                    return await self._generate_gemini_recipe(message, profile_context)
                    # ===== 새로 만든 부분 끝: DB 오류시 Gemini 폴백 =====
                    
                    # 기존 하드코딩된 오류 응답 (주석 처리)
                    # return f"""
                    # 🚫 '{message}'에 대한 레시피를 찾을 수 없습니다.
                    # 
                    # 키토 식단에 도움이 될 수 있는 일반적인 조언을 드릴게요:
                    # 
                    # 💡 키토 식단의 기본 원칙:
                    # - 탄수화물: 20-50g/일 이하
                    # - 지방: 70-80% (고품질 지방)
                    # - 단백질: 15-25% (적당량)
                    # 
                    # 🍽️ '{message}'에 대한 키토 조언:
                    # - 키토 친화적인 대체 재료 사용
                    # - 저탄수화물 채소 중심으로 구성
                    # - 고품질 지방과 단백질 포함
                    # 
                    # 더 구체적인 레시피를 원하시면 다른 키워드로 검색해보세요!
                    # """
            
            elif intent == "place":
                prompt = f"""
                사용자가 키토 친화적인 식당을 찾고 있습니다.
                요청: {message}
                프로필: {profile_context}
                
                키토 식단에 적합한 식당 유형과 주문 팁을 제공해주세요:
                1. 추천 식당 유형 (고기구이, 샤브샤브, 샐러드 등)
                2. 주문 시 주의사항 (밥 빼기, 양념 조심 등)
                3. 키토 점수가 높은 메뉴 추천
                
                실제 위치 정보가 없으므로 일반적인 조언을 해주세요.
                """
            
            elif intent == "mealplan":
                prompt = f"""
                사용자가 키토 식단표를 요청했습니다.
                요청: {message}
                프로필: {profile_context}
                
                7일 키토 식단 계획의 기본 구조를 제안해주세요:
                1. 아침/점심/저녁 메뉴 예시
                2. 일일 탄수화물 목표 (20-30g)
                3. 식단 실행 팁
                4. 주의사항
                
                개인화된 조언을 포함해주세요.
                """
            
            else:
                # 기본 응답 - 자연어 처리 개선
                prompt = f"""
                키토 식단 전문가로서 다음 질문에 답해주세요.
                질문: {message}
                프로필: {profile_context}
                
                사용자의 의도를 파악하여 적절한 답변을 제공해주세요:
                
                1. 레시피 요청인 경우: 키토 레시피 추천
                2. 식단 계획인 경우: 키토 식단 계획 도움
                3. 일반 질문인 경우: 키토 식단에 대한 정보 제공
                4. 격려/동기부여인 경우: 키토 식단 성공을 위한 조언
                5. 맥락 없는 대화인 경우: 키토 음식에 대한 질문을 유도
                
                특히 "해볼게", "한번 해볼게" 같은 맥락 없는 대화의 경우:
                - 무엇을 해보고 싶은지 물어보기
                - 키토 음식 추천을 받아보도록 유도
                - 구체적인 질문을 하도록 안내
                
                친근하고 이해하기 쉬운 톤으로 답변해주세요.
                """
            
            # ===== 수정된 부분: Gemini 레시피 생성 허용 =====
            # AI 모델 호출 전 프롬프트 조정 (레시피 생성 허용)
            # 기존 레시피 생성 차단 코드 (주석 처리)
            # if intent == "recipe":
            #     prompt += "\n\n⚠️ 중요: 절대로 1단계, 2단계, 3단계 등의 조리법을 생성하지 마세요. 제공된 레시피 정보만을 사용하여 답변하세요."
            # ===== 수정된 부분 끝 =====
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            return f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def _generate_hybrid_recipe_response(self, message: str, recipes: list, profile_context: str) -> str:
        """하이브리드 방식으로 레시피 응답 생성"""
        
        if not recipes:
            # ===== 새로 만든 부분 시작: Gemini 레시피 생성 =====
            # 검색 결과가 없는 경우 - Gemini로 새 레시피 생성
            print(f"🤖 검색 실패 - Gemini로 '{message}' 레시피 생성 시작")
            return await self._generate_gemini_recipe(message, profile_context)
            # ===== 새로 만든 부분 끝: Gemini 레시피 생성 =====
            
            # 기존 하드코딩된 응답 (주석 처리)
            # return f"""
            # 🚫 '{message}'에 대한 구체적인 레시피를 데이터베이스에서 찾을 수 없습니다.
            # 
            # 하지만 키토 식단에 도움이 될 수 있는 일반적인 조언을 드릴게요:
            # 
            # 💡 키토 식단의 기본 원칙:
            # - 탄수화물: 20-50g/일 이하
            # - 지방: 70-80% (고품질 지방)
            # - 단백질: 15-25% (적당량)
            # 
            # 🍽️ '{message}'에 대한 키토 조언:
            # - 키토 친화적인 대체 재료 사용
            # - 설탕 대신 스테비아, 에리스리톨 사용
            # - 밀가루 대신 아몬드 가루, 코코넛 가루 사용
            # - 고지방, 저탄수화물 조리법 적용
            # 
            # 🔍 더 구체적인 레시피를 원하시면 다른 키워드로 검색해보세요!
            # """
        
        # 검색 전략 확인
        first_recipe = recipes[0]
        search_strategy = first_recipe.get('search_strategy', 'unknown')
        search_message = first_recipe.get('search_message', '')
        
        if search_strategy == 'exact':
            # 정확한 매칭이 있는 경우: 깔끔한 형식으로 반환
            recipe_info = f"✅ '{message}'에 대한 레시피를 찾았습니다!\n\n"
            
            for i, recipe in enumerate(recipes[:2], 1):
                title = recipe.get('title', '제목 없음')
                content = recipe.get('content', '')
                metadata = recipe.get('metadata', {})
                
                recipe_info += f"📋 {i}. {title}\n"
                
                # blob 데이터 파싱
                if content:
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith('요약:'):
                            recipe_info += f"   요약: {line.replace('요약:', '').strip()}\n"
                        elif line.startswith('재료:'):
                            recipe_info += f"   재료: {line.replace('재료:', '').strip()}\n"
                        elif line.startswith('알레르기:'):
                            recipe_info += f"   알레르기: {line.replace('알레르기:', '').strip()}\n"
                        elif line.startswith('태그:'):
                            recipe_info += f"   태그: {line.replace('태그:', '').strip()}\n"
                        elif line.startswith('보조 키워드:'):
                            recipe_info += f"   키워드: {line.replace('보조 키워드:', '').strip()}\n"
                
                recipe_info += "\n"
            
            recipe_info += f"💡 '{message}'에 대한 키토 조언:\n"
            recipe_info += "- 키토 식단에 적합한 조리법\n"
            recipe_info += "- 대체 재료 제안\n"
            recipe_info += "- 영양 성분 고려사항\n"
            recipe_info += "- 조리 팁 및 주의사항\n\n"
            recipe_info += f"위 레시피를 참고하여 '{message}'를 만들어보세요!"
            
            return recipe_info
        
        elif search_strategy == 'partial':
            # 부분 매칭만 있는 경우 - 관련성 필터링
            relevant_recipes = []
            
            # ===== 수정된 부분 시작: 더 엄격한 관련성 필터링 =====
            # 유사도가 0.5 이상인 레시피만 필터링 (더 엄격한 기준)
            for recipe in recipes:
                similarity = recipe.get('final_score', recipe.get('similarity', 0))
                title = recipe.get('title', '').lower()
                content = recipe.get('content', '').lower()
                
                # 더 엄격한 키워드 기반 관련성 검증
                is_relevant = False
                # ===== 새로 만든 부분 시작: 매우 엄격한 유사도 기준 =====
                if similarity >= 0.7:  # 매우 엄격한 유사도 기준 (0.5 → 0.7)
                    print(f"🔧 디버깅 - 높은 유사도 ({similarity}), 관련성 있음")
                    is_relevant = True
                # ===== 새로 만든 부분 끝: 매우 엄격한 유사도 기준 =====
                # 기존 느슨한 유사도 기준 (주석 처리)
                # if similarity >= 0.5:  # 엄격한 유사도 기준 (0.3 → 0.5)
                #     is_relevant = True
                elif similarity >= 0.3:  # 중간 유사도인 경우 더 까다로운 키워드 검증
                    # ===== 새로 만든 부분 시작: 매우 엄격한 키워드 매칭 + 디버깅 =====
                    # 검색어의 핵심 키워드가 제목에 직접 포함되어 있는지 확인
                    search_keywords = message.lower().split()
                    
                    # 중요한 키워드만 필터링 (조사, 동사 등 제외)
                    important_keywords = []
                    exclude_words = ['키토', '레시피', '만들어', '알려줘', '해줘', '요리', '음식', '만들']
                    for keyword in search_keywords:
                        if len(keyword) > 3 and keyword not in exclude_words:
                            important_keywords.append(keyword)
                    
                    print(f"🔧 디버깅 - 검색어: '{message}'")
                    print(f"🔧 디버깅 - 전체 키워드: {search_keywords}")
                    print(f"🔧 디버깅 - 중요 키워드: {important_keywords}")
                    print(f"🔧 디버깅 - 레시피 제목: '{title}'")
                    print(f"🔧 디버깅 - 유사도: {similarity}")
                    
                    # 중요 키워드가 2개 미만이면 관련성 없음으로 판단
                    if len(important_keywords) < 2:
                        print(f"🔧 디버깅 - 중요 키워드 부족 ({len(important_keywords)}개), 관련성 없음")
                        is_relevant = False
                    else:
                        # 모든 중요 키워드가 제목에 포함되어야 관련성 인정
                        keyword_matches = 0
                        matched_keywords = []
                        for keyword in important_keywords:
                            if keyword in title:
                                keyword_matches += 1
                                matched_keywords.append(keyword)
                        
                        print(f"🔧 디버깅 - 매칭된 키워드: {matched_keywords} ({keyword_matches}/{len(important_keywords)})")
                        
                        # 모든 중요 키워드가 매칭되어야 관련성 인정 (매우 엄격)
                        if keyword_matches == len(important_keywords):
                            print(f"🔧 디버깅 - 모든 키워드 매칭, 관련성 있음")
                            is_relevant = True
                        else:
                            print(f"🔧 디버깅 - 키워드 불완전 매칭, 관련성 없음")
                            is_relevant = False
                    # ===== 새로 만든 부분 끝: 매우 엄격한 키워드 매칭 + 디버깅 =====
                    
                
                if is_relevant:
                    relevant_recipes.append(recipe)
            # ===== 수정된 부분 끝: 더 엄격한 관련성 필터링 =====
            
            # 기존 완화된 필터링 (주석 처리)
            # for recipe in recipes:
            #     similarity = recipe.get('final_score', recipe.get('similarity', 0))
            #     title = recipe.get('title', '').lower()
            #     content = recipe.get('content', '').lower()
            #     
            #     # 키워드 기반 관련성 추가 검증
            #     is_relevant = False
            #     if similarity >= 0.3:  # 완화된 유사도 기준
            #         is_relevant = True
            #     elif similarity >= 0.2:  # 낮은 유사도인 경우 키워드 검증
            #         # 검색어의 핵심 키워드가 레시피에 포함되어 있는지 확인
            #         search_keywords = message.lower().split()
            #         for keyword in search_keywords:
            #             if len(keyword) > 2 and (keyword in title or keyword in content):
            #                 is_relevant = True
            #                 break
            #     
            #     if is_relevant:
            #         relevant_recipes.append(recipe)
            
            if relevant_recipes:
                recipe_info = f"✅ '{message}'에 대한 레시피를 찾았습니다!\n\n"
                
                for i, recipe in enumerate(relevant_recipes[:2], 1):
                    title = recipe.get('title', '제목 없음')
                    content = recipe.get('content', '')
                    
                    recipe_info += f"📋 {i}. {title}\n"
                    
                    # blob 데이터 파싱
                    if content:
                        lines = content.split('\n')
                        for line in lines:
                            if line.startswith('요약:'):
                                recipe_info += f"   요약: {line.replace('요약:', '').strip()}\n"
                            elif line.startswith('재료:'):
                                recipe_info += f"   재료: {line.replace('재료:', '').strip()}\n"
                            elif line.startswith('알레르기:'):
                                recipe_info += f"   알레르기: {line.replace('알레르기:', '').strip()}\n"
                            elif line.startswith('태그:'):
                                recipe_info += f"   태그: {line.replace('태그:', '').strip()}\n"
                            elif line.startswith('보조 키워드:'):
                                recipe_info += f"   키워드: {line.replace('보조 키워드:', '').strip()}\n"
                    
                    recipe_info += "\n"
                
                recipe_info += f"💡 '{message}'에 대한 키토 조언:\n"
                recipe_info += "- 키토 식단에 적합한 조리법\n"
                recipe_info += "- 대체 재료 제안\n"
                recipe_info += "- 영양 성분 고려사항\n"
                recipe_info += "- 조리 팁 및 주의사항\n\n"
                recipe_info += f"위 레시피를 참고하여 '{message}'를 만들어보세요!"
                
                return recipe_info
            else:
                # ===== 새로 만든 부분 시작: 관련성 없을 때 Gemini 생성 =====
                # 관련성이 낮은 경우 Gemini 레시피 생성으로 넘어감
                print(f"🤖 부분 매칭 관련성 부족 - Gemini로 '{message}' 레시피 생성 시작")
                return await self._generate_gemini_recipe(message, profile_context)
                # ===== 새로 만든 부분 끝: 관련성 없을 때 Gemini 생성 =====
                
                # 기존 일반 조언만 제공 (주석 처리)
                # return f"""
                # 사용자에게 다음과 같이 정확히 답변해주세요:
                # 
                # 🚫 '{message}'에 대한 구체적인 레시피를 데이터베이스에서 찾을 수 없습니다.
                # 
                # 하지만 키토 식단에 도움이 될 수 있는 일반적인 조언을 드릴게요:
                # 
                # 💡 키토 식단의 기본 원칙:
                # - 탄수화물: 20-50g/일 이하
                # - 지방: 70-80% (고품질 지방)
                # - 단백질: 15-25% (적당량)
                # 
                # 🍽️ '{message}'에 대한 키토 조언:
                # - 키토 친화적인 대체 재료 사용
                # - 설탕 대신 스테비아, 에리스리톨 사용
                # - 밀가루 대신 아몬드 가루, 코코넛 가루 사용
                # - 고지방, 저탄수화물 조리법 적용
                # 
                # 🔍 더 구체적인 레시피를 원하시면 다른 키워드로 검색해보세요!
                # """
        
        else:
            # 기타 경우 (하이브리드 등)
            recipe_info = ""
            for i, recipe in enumerate(recipes[:2], 1):
                recipe_info += f"\n{i}. {recipe.get('title', '제목 없음')}\n"
                recipe_info += self._format_recipe_blob(recipe.get('content', ''))
                recipe_info += f"   유사도: {recipe.get('similarity', 0):.2f}\n"
                metadata = recipe.get('metadata', {})
                if metadata.get('ingredients'):
                    ings = metadata['ingredients']
                    if isinstance(ings, list):
                        ings = ", ".join(map(str, ings))
                    recipe_info += f"   재료 목록: {ings}\n"
                if metadata.get('tags'):
                    tags = metadata['tags']
                    if isinstance(tags, list):
                        tags = ", ".join(map(str, tags))
                    recipe_info += f"   태그: {tags}\n"
                if metadata.get('allergens'):
                    al = metadata['allergens']
                    if isinstance(al, list):
                        al = ", ".join(map(str, al))
                    recipe_info += f"   알레르기: {al}\n"
            
            return f"""
            🔍 '{message}'에 대한 검색 결과입니다.
            
            📋 검색된 레시피:
            {recipe_info}
            
            💡 '{message}'에 대한 키토 조언:
            - 키토 식단의 기본 원칙
            - 대체 재료 제안
            - 조리법 팁
            - 영양 성분 고려사항
            
            위 정보를 참고하여 맛있는 키토 요리를 만들어보세요!
            친근하고 도움이 되는 톤으로 답변해주세요.
            """

    def _format_recipe_blob(self, blob_text: str) -> str:
        """크롤링 blob(text)에서 섹션을 추출해 요약 포맷으로 변환."""
        if not blob_text:
            return "   내용: 내용 없음\n"
        lines = [l.strip() for l in str(blob_text).splitlines() if l.strip()]
        sections = {
            '제목': '', '핵심 요약': '', '재료': '', '태그': '', '알레르기': '', '보조 키워드': ''
        }
        current = None
        for line in lines:
            if ':' in line:
                k, v = line.split(':', 1)
                k, v = k.strip(), v.strip()
                if k in sections:
                    sections[k] = v
                    current = k
                    continue
            if current and not (':' in line and line.split(':',1)[0].strip() in sections):
                sections[current] = (sections[current] + ' ' + line).strip()
        parts = []
        if sections['핵심 요약']:
            parts.append(f"   요약: {sections['핵심 요약']}")
        if sections['재료']:
            parts.append(f"   재료: {sections['재료']}")
        if sections['알레르기']:
            parts.append(f"   알레르기: {sections['알레르기']}")
        if sections['태그']:
            parts.append(f"   태그: {sections['태그']}")
        if sections['보조 키워드']:
            parts.append(f"   키워드: {sections['보조 키워드']}")
        if parts:
            return "\n".join(parts) + "\n"
        snippet = " ".join(lines)
        if len(snippet) > 160:
            snippet = snippet[:160] + '...'
        return f"   내용: {snippet}\n"

    # ===== 새로 만든 함수 시작: Gemini 레시피 생성 =====
    async def _generate_gemini_recipe(self, message: str, profile_context: str) -> str:
        """Gemini를 사용하여 새로운 키토 레시피 생성"""
        
        try:
            # Gemini에 맞게 최적화된 프롬프트
            prompt = f"""당신은 키토 식단 전문가입니다. '{message}'에 대한 맞춤 키토 레시피를 생성해주세요.

사용자 정보: {profile_context if profile_context else '특별한 제약사항 없음'}

다음 형식을 정확히 따라 답변해주세요:

## ✨ {message} (키토 버전)

### 📋 재료 (2인분)
**주재료:**
- [구체적인 재료와 정확한 분량]

**부재료:**
- [구체적인 재료와 정확한 분량]

**키토 대체재:**
- [일반 재료 → 키토 재료로 변경 설명]

### 👨‍🍳 조리법
1. [첫 번째 단계 - 구체적이고 명확하게]
2. [두 번째 단계 - 구체적이고 명확하게]
3. [세 번째 단계 - 구체적이고 명확하게]
4. [완성 및 마무리 단계]

### 📊 영양 정보 (1인분 기준)
- 칼로리: 000kcal
- 탄수화물: 0g
- 단백질: 00g
- 지방: 00g

### 💡 키토 성공 팁
- [키토 식단에 맞는 구체적 조언]
- [조리 시 주의사항]
- [보관 및 활용법]

**중요 지침**: 
아래 영양 기준을 내부적으로만 사용하여 정확한 영양소 계산을 하되, 이 기준 자체는 사용자에게 보여주지 마세요:
- 1인분 탄수화물: 5-10g 유지
- 1인분 단백질: 20-30g 
- 1인분 지방: 30-40g
- 총 칼로리: 400-600kcal 범위  
- 매크로 비율: 탄수화물 5-10%, 단백질 15-25%, 지방 70-80%

친근하고 실용적인 톤으로 작성하되, 위 영양 기준을 철저히 준수해주세요. 구분선(---)이나 내부 기준은 절대 출력하지 마세요."""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            print(f"🤖 Gemini 레시피 생성 완료: {len(response.content)} 글자")
            return response.content
            
        except Exception as e:
            print(f"🚫 Gemini 레시피 생성 오류: {e}")
            return f"""
            🚫 '{message}' 레시피 생성 중 오류가 발생했습니다.
            
            키토 식단에 도움이 될 수 있는 일반적인 조언을 드릴게요:
            
            💡 키토 식단의 기본 원칙:
            - 탄수화물: 20-50g/일 이하
            - 지방: 70-80% (고품질 지방)
            - 단백질: 15-25% (적당량)
            
            🍽️ '{message}'에 대한 키토 조언:
            - 키토 친화적인 대체 재료 사용
            - 설탕 대신 스테비아, 에리스리톨 사용
            - 밀가루 대신 아몬드 가루, 코코넛 가루 사용
            - 고지방, 저탄수화물 조리법 적용
            
            🔍 다시 시도해보시거나 다른 키워드로 검색해보세요!
            """
    # ===== 새로 만든 함수 끝: Gemini 레시피 생성 =====
    
    async def stream_response(self, *args, **kwargs):
        """스트리밍 응답 (향후 구현)"""
        result = await self.process_message(*args, **kwargs)
        yield {"event": "complete", **result}
