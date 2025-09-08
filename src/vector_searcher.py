"""
벡터 서칭을 통한 메뉴 검색 기능
사용자 프롬프트를 임베딩으로 변환하여 유사한 메뉴를 찾는 기능 제공
"""

import os
import openai
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from loguru import logger
import numpy as np
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class VectorSearcher:
    """벡터 서칭을 위한 클래스"""
    
    def __init__(self):
        """초기화 - OpenAI 및 Supabase 클라이언트 설정"""
        self.openai_client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.embedding_dimension = int(os.getenv('EMBEDDING_DIMENSION', '1536'))
        
        logger.info("VectorSearcher 초기화 완료")
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        사용자 쿼리를 임베딩으로 변환
        
        Args:
            query (str): 사용자 입력 쿼리
            
        Returns:
            List[float]: 쿼리의 임베딩 벡터
        """
        try:
            logger.info(f"쿼리 임베딩 생성 중: '{query}'")
            
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=query,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.info(f"임베딩 생성 완료 (차원: {len(embedding)})")
            
            return embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise
    
    def search_similar_menus(
        self, 
        query: str, 
        match_count: int = 5, 
        match_threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도를 기반으로 메뉴 검색
        
        Args:
            query (str): 검색할 쿼리
            match_count (int): 반환할 결과 개수
            match_threshold (float): 유사도 임계값 (0~1)
            
        Returns:
            List[Dict]: 검색된 메뉴 리스트
        """
        try:
            # 1. 쿼리를 임베딩으로 변환
            query_embedding = self.generate_query_embedding(query)
            
            # 2. Supabase에서 벡터 검색 실행 (직접 쿼리 방식)
            logger.info(f"벡터 검색 실행 - 쿼리: '{query}', 결과 수: {match_count}, 임계값: {match_threshold}")
            
            # 직접 SQL을 통한 벡터 검색
            logger.info("직접 SQL로 벡터 검색 실행")
            
            # 임베딩 벡터를 PostgreSQL 배열 형식으로 변환
            embedding_array = "{" + ",".join(map(str, query_embedding)) + "}"
            
            # SQL 쿼리 직접 실행
            query_sql = f"""
            SELECT 
                restaurant_name, 
                menu_name, 
                key_ingredients, 
                short_description, 
                combined_text,
                1 - (embedding <=> '{embedding_array}'::vector) AS similarity
            FROM restaurants 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> '{embedding_array}'::vector
            LIMIT {match_count};
            """
            
            try:
                result = self.supabase.rpc('exec', {'sql': query_sql}).execute()
            except:
                # exec 함수가 없는 경우 PostgREST 방식으로 시도
                logger.warning("exec 함수 없음, PostgREST 방식 시도")
                try:
                    # PostgREST select 방식 시도
                    result = self.supabase.table("restaurants").select(
                        f"restaurant_name, menu_name, key_ingredients, short_description, combined_text"
                    ).not_.is_("embedding", "null").limit(match_count).execute()
                    
                    # 수동으로 유사도 계산 (numpy 사용)
                    if result.data:
                        import numpy as np
                        query_vec = np.array(query_embedding)
                        
                        # 모든 임베딩을 가져와서 유사도 계산
                        all_data = self.supabase.table("restaurants").select(
                            "restaurant_name, menu_name, key_ingredients, short_description, combined_text, embedding"
                        ).not_.is_("embedding", "null").execute()
                        
                        if all_data.data:
                            scored_items = []
                            for item in all_data.data:
                                if item.get('embedding'):
                                    try:
                                        # 임베딩이 리스트가 아닌 경우 변환
                                        embedding = item['embedding']
                                        if isinstance(embedding, str):
                                            # 문자열인 경우 JSON 파싱 시도
                                            import json
                                            embedding = json.loads(embedding)
                                        elif not isinstance(embedding, list):
                                            # 다른 타입인 경우 리스트로 변환 시도
                                            embedding = list(embedding)
                                        
                                        item_vec = np.array(embedding, dtype=float)
                                        # 코사인 유사도 계산
                                        similarity = np.dot(query_vec, item_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(item_vec))
                                        item['similarity'] = float(similarity)
                                        scored_items.append(item)
                                    except Exception as e:
                                        logger.warning(f"임베딩 처리 실패: {e}")
                                        continue
                            
                            # 유사도 기준 정렬 및 상위 결과 선택
                            scored_items.sort(key=lambda x: x['similarity'], reverse=True)
                            result.data = scored_items[:match_count]
                        
                except Exception as e:
                    logger.error(f"모든 벡터 검색 방식 실패: {e}")
                    result = type('obj', (object,), {'data': []})
            
            if result.data:
                # 벡터 검색 결과인 경우 거리를 유사도로 변환
                for item in result.data:
                    if 'distance' in item:
                        distance = item.get('distance', 1.0)
                        item['similarity'] = max(0, 1 - float(distance))
                    elif 'similarity' not in item:
                        # 기본 유사도가 없는 경우 0.5로 설정
                        item['similarity'] = 0.5
                
                # 유사도 기준으로 정렬
                result.data.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                
                # 임계값 필터링 (필요한 경우)
                if match_threshold > 0:
                    result.data = [item for item in result.data if item['similarity'] >= match_threshold]
                
                logger.info(f"검색 완료 - {len(result.data)}개 결과 발견")
                return result.data
            else:
                logger.warning("검색 결과가 없습니다")
                return []
                
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            raise
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        검색 결과를 보기 좋게 포맷팅
        
        Args:
            results (List[Dict]): 검색 결과
            
        Returns:
            str: 포맷팅된 결과 문자열
        """
        if not results:
            return "검색 결과가 없습니다."
        
        formatted_output = f"\n🔍 검색 결과 ({len(results)}개):\n"
        formatted_output += "=" * 50 + "\n"
        
        for i, item in enumerate(results, 1):
            similarity = item.get('similarity', 0)
            restaurant_name = item.get('restaurant_name', 'Unknown')
            menu_name = item.get('menu_name', 'Unknown')
            key_ingredients = item.get('key_ingredients', 'N/A')
            short_description = item.get('short_description', 'N/A')
            
            formatted_output += f"{i}. 🏪 {restaurant_name}\n"
            formatted_output += f"   🍽️ 메뉴: {menu_name}\n"
            formatted_output += f"   🥘 주요 재료: {key_ingredients}\n"
            formatted_output += f"   📝 설명: {short_description}\n"
            formatted_output += f"   📊 유사도: {similarity:.3f}\n"
            formatted_output += "-" * 50 + "\n"
        
        return formatted_output
    
    def search_and_display(
        self, 
        query: str, 
        match_count: int = 5, 
        match_threshold: float = 0.1
    ) -> None:
        """
        검색 실행 및 결과 출력
        
        Args:
            query (str): 검색할 쿼리
            match_count (int): 반환할 결과 개수
            match_threshold (float): 유사도 임계값
        """
        try:
            print(f"\n🔍 검색 중: '{query}'")
            print("⏳ 잠시만 기다려주세요...")
            
            # 검색 실행
            results = self.search_similar_menus(query, match_count, match_threshold)
            
            # 결과 출력
            formatted_results = self.format_search_results(results)
            print(formatted_results)
            
        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")
            logger.error(f"검색 실행 실패: {e}")

if __name__ == "__main__":
    # 테스트 실행
    searcher = VectorSearcher()
    
    # 테스트 쿼리들
    test_queries = [
        "매운 한국 음식",
        "건강한 샐러드",
        "치킨이 들어간 요리",
        "달콤한 디저트"
    ]
    
    for query in test_queries:
        searcher.search_and_display(query, match_count=3)
        print("\n" + "="*60 + "\n")
