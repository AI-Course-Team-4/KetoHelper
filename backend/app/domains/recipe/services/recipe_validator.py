"""
RecipeValidator 서비스
골든셋 기반 레시피 생성 및 검증 (Generator + Judge LLM)
"""

import json
import re
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from langchain.schema import HumanMessage

from app.core.llm_factory import create_chat_llm
from app.prompts.meal.generator import get_generator_prompt
from app.prompts.meal.judge import get_judge_prompt
from app.core.config import settings
from supabase import create_client, Client


class RecipeValidator:
    """골든셋 기반 레시피 검증 서비스"""
    
    def __init__(self):
        """초기화"""
        try:
            self.llm = create_chat_llm()
        except Exception as e:
            print(f"LLM 초기화 실패: {e}")
            self.llm = None
        
        # Supabase 클라이언트
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        
        # 설정
        self.max_attempts = 3  # 최초 1회 + 재시도 2회
        self.generator_timeout = 120  # 초 (Gemini는 프롬프트가 길어서 시간이 더 걸림)
        self.judge_timeout = 90  # 초
    
    async def generate_validated_recipe(
        self,
        meal_type: str,
        constraints: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        검증된 레시피 생성 (골든셋 기반)
        
        Args:
            meal_type: 식사 타입 (예: "닭고기 요리", "샐러드")
            constraints: 사용자 제약 조건 {allergies, dislikes, kcal_target, carbs_max}
            user_id: 사용자 ID (옵션)
        
        Returns:
            {
                "success": bool,
                "recipe": dict,  # 최종 레시피
                "validation": dict,  # 검증 결과
                "attempts": int,  # 시도 횟수
                "response_time_ms": int
            }
        """
        
        start_time = datetime.now()
        
        try:
            # 1. 골든셋 선택
            base_recipe, transform_rules = await self._select_golden_recipe(
                meal_type, constraints
            )
            
            if not base_recipe:
                return {
                    "success": False,
                    "error": "적합한 골든셋 레시피를 찾을 수 없습니다",
                    "attempts": 0
                }
            
            # 2. 생성 + 검증 루프 (최대 3회)
            attempts = 0
            last_generated = None
            last_judge_report = None
            
            while attempts < self.max_attempts:
                attempts += 1
                print(f"🔄 시도 {attempts}/{self.max_attempts}")
                
                try:
                    # Generator 호출
                    generated_recipe = await self._call_generator(
                        base_recipe, transform_rules, constraints
                    )
                    
                    if not generated_recipe:
                        print(f"  ❌ Generator 실패")
                        continue
                    
                    last_generated = generated_recipe
                    
                    # Judge 호출
                    judge_report = await self._call_judge(
                        base_recipe, transform_rules, constraints, generated_recipe
                    )
                    
                    if not judge_report:
                        print(f"  ❌ Judge 실패")
                        continue
                    
                    last_judge_report = judge_report
                    
                    # 통과 여부 확인
                    if judge_report.get("passed"):
                        print(f"  ✅ 검증 통과! (시도 {attempts}회)")
                        
                        # DB 저장
                        generated_id = await self._save_to_db(
                            user_id=user_id,
                            base_recipe_id=base_recipe.get("id"),
                            generated_recipe=generated_recipe,
                            judge_report=judge_report,
                            passed=True,
                            attempts=attempts,
                            response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                        )
                        
                        return {
                            "success": True,
                            "recipe": self._format_final_recipe(
                                base_recipe, generated_recipe
                            ),
                            "validation": judge_report,
                            "attempts": attempts,
                            "response_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                            "generated_id": generated_id
                        }
                    
                    # 실패 시 suggested_fixes 적용
                    print(f"  ⚠️ 검증 실패: {judge_report.get('reasons', [])}")
                    if attempts < self.max_attempts:
                        constraints = self._apply_suggested_fixes(
                            constraints, judge_report.get("suggested_fixes", [])
                        )
                
                except asyncio.TimeoutError:
                    print(f"  ⏱️ 타임아웃 (시도 {attempts})")
                    continue
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON 파싱 오류: {e}")
                    continue
                except Exception as e:
                    print(f"  ❌ 예상치 못한 오류: {e}")
                    continue
            
            # 최대 시도 횟수 초과
            print(f"❌ 검증 실패 (최대 {self.max_attempts}회 시도)")
            
            # 실패한 레시피도 DB에 저장 (분석용)
            if last_generated and last_judge_report:
                await self._save_to_db(
                    user_id=user_id,
                    base_recipe_id=base_recipe.get("id"),
                    generated_recipe=last_generated,
                    judge_report=last_judge_report,
                    passed=False,
                    attempts=attempts,
                    response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                )
            
            return {
                "success": False,
                "error": f"검증 실패 (시도 {attempts}회)",
                "last_recipe": last_generated,
                "last_validation": last_judge_report,
                "attempts": attempts,
                "response_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }
        
        except Exception as e:
            print(f"❌ RecipeValidator 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "attempts": 0
            }
    
    async def _select_golden_recipe(
        self,
        meal_type: str,
        constraints: Dict[str, Any]
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        골든셋 레시피 선택
        
        Returns:
            (base_recipe, transform_rules)
        """
        
        try:
            # meal_type에서 태그 추출 (간단한 키워드 매칭)
            tags = self._extract_tags_from_meal_type(meal_type)
            
            # 골든셋 검색 (태그 기반)
            response = self.supabase.rpc(
                'search_golden_recipes',
                {'search_tags': tags}
            ).execute()
            
            if not response.data or len(response.data) == 0:
                print(f"⚠️ 태그 '{tags}'에 맞는 골든셋 없음, 랜덤 선택")
                # 랜덤 선택
                response = self.supabase.table('golden_recipes')\
                    .select('*')\
                    .eq('is_active', True)\
                    .limit(1)\
                    .execute()
            
            if not response.data:
                return None, None
            
            base_recipe = response.data[0]
            print(f"✅ 골든셋 선택: {base_recipe['title']}")
            
            # 변형 규칙 조회
            rules_response = self.supabase.table('transform_rules')\
                .select('*')\
                .eq('base_recipe_id', base_recipe['id'])\
                .limit(1)\
                .execute()
            
            transform_rules = rules_response.data[0] if rules_response.data else {
                "swaps_json": [],
                "amount_limits_json": [],
                "forbidden_json": ["sugar", "honey", "rice", "wheat_flour"]
            }
            
            return base_recipe, transform_rules
        
        except Exception as e:
            print(f"❌ 골든셋 선택 오류: {e}")
            return None, None
    
    def _extract_tags_from_meal_type(self, meal_type: str) -> List[str]:
        """meal_type에서 태그 추출"""
        
        tag_mapping = {
            "닭": ["chicken", "keto"],
            "돼지": ["pork", "keto"],
            "계란": ["egg", "breakfast", "keto"],
            "샐러드": ["salad", "keto"],
            "볶음": ["stir_fry", "keto"],
            "구이": ["grilled", "keto"],
            "고기": ["protein", "keto"]
        }
        
        tags = set()
        for keyword, mapped_tags in tag_mapping.items():
            if keyword in meal_type:
                tags.update(mapped_tags)
        
        return list(tags) if tags else ["keto"]
    
    async def _call_generator(
        self,
        base_recipe: Dict,
        transform_rules: Dict,
        constraints: Dict
    ) -> Optional[Dict]:
        """Generator LLM 호출"""
        
        try:
            if not self.llm:
                raise Exception("LLM 초기화되지 않음")
            
            prompt = get_generator_prompt(base_recipe, transform_rules, constraints)
            
            # 타임아웃 적용
            response = await asyncio.wait_for(
                self.llm.ainvoke([HumanMessage(content=prompt)]),
                timeout=self.generator_timeout
            )
            
            # JSON 추출
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            print(f"  ⚠️ JSON 형식 아님: {response.content[:100]}")
            return None
        
        except asyncio.TimeoutError:
            print(f"  ⏱️ Generator 타임아웃 ({self.generator_timeout}초)")
            raise
        except Exception as e:
            print(f"  ❌ Generator 오류: {e}")
            return None
    
    async def _call_judge(
        self,
        base_recipe: Dict,
        transform_rules: Dict,
        constraints: Dict,
        generated_recipe: Dict
    ) -> Optional[Dict]:
        """Judge LLM 호출"""
        
        try:
            if not self.llm:
                raise Exception("LLM 초기화되지 않음")
            
            prompt = get_judge_prompt(
                base_recipe, transform_rules, constraints, generated_recipe
            )
            
            # 타임아웃 적용
            response = await asyncio.wait_for(
                self.llm.ainvoke([HumanMessage(content=prompt)]),
                timeout=self.judge_timeout
            )
            
            # JSON 추출
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            print(f"  ⚠️ JSON 형식 아님: {response.content[:100]}")
            return None
        
        except asyncio.TimeoutError:
            print(f"  ⏱️ Judge 타임아웃 ({self.judge_timeout}초)")
            raise
        except Exception as e:
            print(f"  ❌ Judge 오류: {e}")
            return None
    
    def _apply_suggested_fixes(
        self,
        constraints: Dict,
        suggested_fixes: List[str]
    ) -> Dict:
        """suggested_fixes를 constraints에 반영"""
        
        # 간단한 구현: suggested_fixes를 파싱하여 금지어 추가
        # 예: "rice를 konjac_rice로 치환하세요" -> rice를 금지어에 추가
        
        new_constraints = constraints.copy()
        
        for fix in suggested_fixes:
            # "재료를" 패턴 찾기
            if "을" in fix or "를" in fix:
                # 간단한 파싱
                parts = fix.split("을")
                if len(parts) < 2:
                    parts = fix.split("를")
                
                if len(parts) >= 2:
                    ingredient = parts[0].strip()
                    if "dislikes" not in new_constraints:
                        new_constraints["dislikes"] = []
                    new_constraints["dislikes"].append(ingredient)
        
        return new_constraints
    
    def _format_final_recipe(
        self,
        base_recipe: Dict,
        generated_recipe: Dict
    ) -> Dict:
        """최종 레시피 포맷팅"""
        
        title = base_recipe.get("title", "키토 레시피")
        title_suffix = generated_recipe.get("title_suffix", "")
        
        return {
            "type": "recipe",
            "id": f"validated_{base_recipe.get('id', 'unknown')}",
            "title": f"{title}{title_suffix}",
            "ingredients": generated_recipe.get("final_ingredients", []),
            "steps": generated_recipe.get("final_steps", []),
            "macros": generated_recipe.get("estimated_macros", {}),
            "source": "golden_validated",
            "base_recipe_id": base_recipe.get("id"),
            "deltas": generated_recipe.get("deltas", [])
        }
    
    async def _save_to_db(
        self,
        user_id: Optional[str],
        base_recipe_id: str,
        generated_recipe: Dict,
        judge_report: Dict,
        passed: bool,
        attempts: int,
        response_time_ms: int
    ) -> str:
        """생성 결과를 DB에 저장"""
        
        try:
            data = {
                "user_id": user_id,
                "base_recipe_id": base_recipe_id,
                "deltas_json": generated_recipe.get("deltas", []),
                "final_ingredients_json": generated_recipe.get("final_ingredients", []),
                "final_steps_json": generated_recipe.get("final_steps", []),
                "judge_report_json": judge_report,
                "passed": passed,
                "attempts": attempts,
                "response_time_ms": response_time_ms,
                "model_gen": "gemini-pro",  # LLM 모델명
                "model_judge": "gemini-pro",
                "created_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table('generated_recipes')\
                .insert(data)\
                .execute()
            
            if response.data:
                return response.data[0]['id']
            
            return None
        
        except Exception as e:
            print(f"❌ DB 저장 실패: {e}")
            return None

