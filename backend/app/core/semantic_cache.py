"""
시맨틱 캐시 서비스
의미적 유사성을 기반으로 한 캐시 시스템
"""

import hashlib
import json
import time
from typing import Optional, List, Dict, Any
import openai
from app.core.config import settings
from app.core.database import supabase


class SemanticCacheService:
    """시맨틱 캐시 관리 서비스"""
    
    def __init__(self):
        self.supabase = supabase
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.threshold = 0.90  # 유사도 임계값
        self.window_seconds = 24 * 3600  # 24시간
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        # 공백 정리 및 소문자 변환
        normalized = " ".join(text.strip().split()).lower()
        
        # 동의어 정규화
        synonyms = {
            '식단표': ['식단', '메뉴', '계획', '표'],
            '만들어줘': ['만들어', '생성해줘', '추천해줘', '계획해줘'],
            '키토': ['케토', '저탄수', '저탄수화물'],
            '일주일': ['7일', '1주일'],
            '이러면': ['이런', '같은', '비슷한']
        }
        
        for standard, variants in synonyms.items():
            for variant in variants:
                normalized = normalized.replace(variant, standard)
        
        # 불필요한 단어 제거
        stop_words = ['이러면', '이런', '같은', '비슷한', '이런거']
        for word in stop_words:
            normalized = normalized.replace(word, '')
        
        return normalized.strip()
    
    def _sha256(self, text: str) -> str:
        """SHA256 해시 생성"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    async def _embed_text(self, text: str) -> List[float]:
        """텍스트를 임베딩으로 변환"""
        try:
            print(f"📊 시맨틱 캐시 임베딩 생성: {text[:50]}...")
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            print(f"✅ 시맨틱 캐시 임베딩 완료: {len(embedding)}차원")
            return embedding
        except Exception as e:
            print(f"❌ 시맨틱 캐시 임베딩 오류: {e}")
            return []
    
    def _passes_rules(self, meta: Dict[str, Any], query_text: str) -> bool:
        """메타데이터 규칙 검사"""
        # 식단 생성의 경우 일수 정보도 고려
        if meta.get("route") == "meal_plan":
            cached_days = meta.get("days")
            if cached_days:
                # 요청된 일수 추출 (간단한 패턴 매칭)
                import re
                days_match = re.search(r'(\d+)일', query_text)
                if days_match:
                    requested_days = int(days_match.group(1))
                    # 일수가 다르면 매칭 실패
                    if cached_days != requested_days:
                        print(f"   📅 일수 불일치: 캐시 {cached_days}일 vs 요청 {requested_days}일")
                        return False
        return True
    
    async def semantic_lookup(
        self, 
        text: str, 
        user_id: str, 
        model_ver: str, 
        opts_hash: str
    ) -> Optional[str]:
        """시맨틱 캐시에서 유사한 결과 검색"""
        try:
            # 텍스트 정규화
            normalized_text = self._normalize_text(text)
            
            # 임베딩 생성
            query_vec = await self._embed_text(normalized_text)
            if not query_vec:
                return None
            
            # Supabase RPC 호출
            response = self.supabase.rpc("sc_match", {
                "query_vec": query_vec,
                "p_user": user_id,
                "p_model_ver": model_ver,
                "p_opts_hash": opts_hash,
                "p_window_seconds": self.window_seconds,
                "p_limit": 1
            }).execute()
            
            rows = getattr(response, "data", []) or []
            if not rows:
                print(f"🔍 시맨틱 캐시 미스: 유사한 결과 없음")
                return None
            
            top_result = rows[0]
            score = float(top_result["score"])
            
            print(f"🔍 시맨틱 캐시 검색 결과: 점수 {score:.3f} (임계값 {self.threshold})")
            
            if score >= self.threshold and self._passes_rules(top_result["meta"], text):
                print(f"✅ 시맨틱 캐시 히트: {score:.3f} (임계값 {self.threshold})")
                print(f"   📝 원본 메시지: '{text[:50]}...'")
                print(f"   🎯 매칭된 메시지: '{top_result.get('meta', {}).get('original_message', 'N/A')[:50]}...'")
                return top_result["answer"]
            else:
                print(f"❌ 시맨틱 캐시 미스: 점수 {score:.3f} < 임계값 {self.threshold}")
                return None
                
        except Exception as e:
            print(f"❌ 시맨틱 캐시 조회 오류: {e}")
            return None
    
    async def save_semantic_cache(
        self,
        text: str,
        user_id: str,
        model_ver: str,
        opts_hash: str,
        answer: str,
        meta: Dict[str, Any]
    ) -> bool:
        """시맨틱 캐시에 결과 저장"""
        try:
            # 텍스트 정규화
            normalized_text = self._normalize_text(text)
            
            # 임베딩 생성
            embedding = await self._embed_text(normalized_text)
            if not embedding:
                return False
            
            # 해시 생성
            prompt_hash = self._sha256(normalized_text)
            
            # 데이터 저장
            row = {
                "user_id": user_id,
                "model_ver": model_ver,
                "opts_hash": opts_hash,
                "prompt_hash": prompt_hash,
                "answer": answer,
                "meta": meta,
                "embedding": embedding
            }
            
            result = self.supabase.table("semantic_cache").insert(row).execute()
            
            if result.data:
                print(f"✅ 시맨틱 캐시 저장 완료: {len(answer)}자")
                print(f"   📝 메시지: '{normalized_text[:50]}...'")
                print(f"   🏷️ 모델: {model_ver}")
                print(f"   🔑 옵션 해시: {opts_hash[:20]}...")
                return True
            else:
                print(f"❌ 시맨틱 캐시 저장 실패")
                return False
                
        except Exception as e:
            print(f"❌ 시맨틱 캐시 저장 오류: {e}")
            return False


# 전역 인스턴스
semantic_cache_service = SemanticCacheService()
