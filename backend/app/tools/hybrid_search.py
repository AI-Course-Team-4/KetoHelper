"""
Supabase 하이브리드 검색 도구
벡터 검색 + 키워드 검색 + 메타데이터 필터링을 Supabase RPC로 통합
"""

import re
# OpenAI import 주석 처리 (Gemini로 교체)
# import openai
import asyncio
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.config import settings

class HybridSearchTool:
    """Supabase 하이브리드 검색 도구 클래스"""
    
    def __init__(self):
        self.supabase = supabase
        # OpenAI 클라이언트 주석 처리 (임베딩 기능 임시 비활성화)
        # self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def _create_embedding(self, text: str) -> List[float]:
        """텍스트를 임베딩으로 변환 (임시 비활성화)"""
        # OpenAI 임베딩 기능 임시 비활성화 - 키워드 검색만 사용
        print(f"⚠️ 임베딩 기능 비활성화됨 - 키워드 검색만 사용: {text}")
        return []
        
        # try:
        #     response = self.openai_client.embeddings.create(
        #         model="text-embedding-3-small",
        #         input=text
        #     )
        #     return response.data[0].embedding
        # except Exception as e:
        #     print(f"임베딩 생성 오류: {e}")
        #     return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출"""
        # 한글, 영문, 숫자만 추출
        keywords = re.findall(r'[가-힣a-zA-Z0-9]+', query)
        # 2글자 이상만 필터링
        keywords = [kw for kw in keywords if len(kw) >= 2]
        return keywords
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """중복 결과 제거"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results
    
    async def _supabase_hybrid_search(self, query: str, query_embedding: List[float], k: int) -> List[Dict]:
        """Supabase RPC 하이브리드 검색"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            # Supabase RPC 함수 호출
            results = self.supabase.rpc('hybrid_search', {
                'query_text': query,
                'query_embedding': query_embedding,
                'match_count': k
            }).execute()
            
            if results.data:
                print(f"✅ Supabase 하이브리드 검색 성공: {len(results.data)}개")
                return results.data
            else:
                print("⚠️ Supabase 하이브리드 검색 결과 없음")
                return []
                
        except Exception as e:
            print(f"Supabase 하이브리드 검색 오류: {e}")
            return []
    
    async def _fallback_keyword_search(self, query: str, k: int) -> List[Dict]:
        """폴백 키워드 검색 (RPC 실패 시)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            keywords = self._extract_keywords(query)
            if not keywords:
                return []
            
            keyword_results = []
            
            for keyword in keywords[:3]:  # 상위 3개 키워드만 사용
                try:
                    # 제목에서 키워드 검색
                    title_results = self.supabase.table('recipes_keto_enhanced').select('*').ilike('title', f'%{keyword}%').limit(k).execute()
                    
                    # 내용에서 키워드 검색
                    content_results = self.supabase.table('recipes_keto_enhanced').select('*').ilike('content', f'%{keyword}%').limit(k).execute()
                    
                    keyword_results.extend(title_results.data or [])
                    keyword_results.extend(content_results.data or [])
                    
                except Exception as e:
                    print(f"키워드 검색 오류 for '{keyword}': {e}")
                    continue
            
            # 중복 제거
            unique_results = self._deduplicate_results(keyword_results)
            
            # 키워드 검색 결과 포맷팅
            formatted_results = []
            for result in unique_results:
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'vector_score': 0.0,
                    'keyword_score': 1.0,
                    'hybrid_score': 1.0,
                    'search_type': 'keyword',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'embedding']}
                })
            
            return formatted_results[:k]
            
        except Exception as e:
            print(f"폴백 키워드 검색 오류: {e}")
            return []
    
    
    async def hybrid_search(self, query: str, filters: Optional[Dict] = None, k: int = 5) -> List[Dict]:
        """Supabase 하이브리드 검색"""
        try:
            print(f"🔍 Supabase 하이브리드 검색 시작: '{query}'")
            
            # 1. 임베딩 생성
            print("  📊 임베딩 생성 중...")
            query_embedding = await self._create_embedding(query)
            
            if not query_embedding:
                print("  ⚠️ 임베딩 생성 실패, 키워드 검색으로 폴백")
                return await self._fallback_keyword_search(query, k)
            
            # 2. Supabase RPC 하이브리드 검색
            print("  🔄 Supabase RPC 하이브리드 검색 실행...")
            results = await self._supabase_hybrid_search(query, query_embedding, k)
            
            if not results:
                print("  ⚠️ RPC 검색 실패, 키워드 검색으로 폴백")
                return await self._fallback_keyword_search(query, k)
            
            # 3. 결과 포맷팅
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'vector_score': result.get('vector_score', 0.0),
                    'keyword_score': result.get('keyword_score', 0.0),
                    'hybrid_score': result.get('hybrid_score', 0.0),
                    'search_type': 'hybrid',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'vector_score', 'keyword_score', 'hybrid_score']}
                })
            
            print(f"  ✅ 최종 결과: {len(formatted_results)}개")
            
            # 결과 요약 출력
            for i, result in enumerate(formatted_results[:3], 1):
                print(f"    {i}. {result['title']} (점수: {result['hybrid_score']:.3f})")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 하이브리드 검색 오류: {e}")
            return []
    
    async def search(self, query: str, profile: str = "", max_results: int = 5) -> List[Dict]:
        """간단한 검색 인터페이스 (한글 최적화)"""
        try:
            # 한글 검색 최적화 도구 사용
            from app.tools.korean_search import korean_search_tool
            
            # 프로필에서 필터 추출
            filters = {}
            if profile:
                if "아침" in profile or "morning" in profile.lower():
                    filters['category'] = '아침'
                if "쉬운" in profile or "easy" in profile.lower():
                    filters['difficulty'] = '쉬움'
            
            # 한글 최적화 검색 실행
            results = await korean_search_tool.korean_hybrid_search(query, max_results)
            
            # 결과 포맷팅 (검색 전략과 메시지 포함)
            formatted_results = []
            search_strategy = "unknown"
            search_message = ""
            
            for result in results:
                # 첫 번째 결과에서 검색 전략과 메시지 추출
                if not search_message:
                    search_strategy = result.get('search_strategy', 'unknown')
                    search_message = result.get('search_message', '')
                
                formatted_results.append({
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'similarity': result.get('final_score', 0.0),
                    'metadata': result.get('metadata', {}),
                    'search_types': [result.get('search_type', 'hybrid')],
                    'search_strategy': search_strategy,
                    'search_message': search_message
                })
            
            # 검색 결과가 없는 경우 메시지 추가
            if not formatted_results:
                formatted_results.append({
                    'title': '검색 결과 없음',
                    'content': '검색 결과가 없습니다. 다른 키워드를 시도해보세요.',
                    'similarity': 0.0,
                    'metadata': {'search_message': '검색 결과가 없습니다.'},
                    'search_types': ['none'],
                    'search_strategy': 'none',
                    'search_message': '검색 결과가 없습니다. 다른 키워드를 시도해보세요.'
                })
            
            # 검색 메시지 출력
            if search_message:
                print(f"💬 사용자 안내: {search_message}")
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {e}")
            # 폴백: 기존 검색 방식 사용
            try:
                results = await self.hybrid_search(query, {}, max_results)
                
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'title': result.get('title', '제목 없음'),
                        'content': result.get('content', ''),
                        'similarity': result.get('hybrid_score', 0.0),
                        'metadata': result.get('metadata', {}),
                        'search_types': [result.get('search_type', 'hybrid')]
                    })
                
                return formatted_results
            except Exception as fallback_error:
                print(f"Fallback search error: {fallback_error}")
                return []

# 전역 하이브리드 검색 도구 인스턴스
hybrid_search_tool = HybridSearchTool()
