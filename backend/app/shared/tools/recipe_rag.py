"""
레시피 RAG (Retrieval Augmented Generation) 도구
ChromaDB를 사용한 벡터 검색 기반 레시피 추천
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import os
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


class RecipeRAGTool:
    """레시피 RAG 도구"""
    
    def __init__(self):
        """ChromaDB 클라이언트 및 컬렉션 초기화"""
        
        # ChromaDB 클라이언트 생성
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 임베딩 모델
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        
        # 레시피 컬렉션
        self.collection_name = "keto_recipes"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"✅ 기존 ChromaDB 컬렉션 '{self.collection_name}' 연결됨")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "키토 레시피 벡터 저장소"}
            )
            print(f"✅ 새 ChromaDB 컬렉션 '{self.collection_name}' 생성됨")
    
    async def add_recipe_to_vector_store(self, recipe: Dict[str, Any]) -> Optional[str]:
        """
        레시피를 벡터 저장소에 추가
        
        Args:
            recipe: 레시피 데이터 딕셔너리
            
        Returns:
            성공 시 레시피 ID, 실패 시 None
        """
        try:
            # 레시피 ID 생성
            recipe_id = recipe.get("id") or f"recipe_{len(self.collection.get()['ids']) + 1}"
            
            # 검색용 텍스트 생성
            search_text = self._create_search_text(recipe)
            
            # 임베딩 생성
            embedding = self.embeddings.embed_query(search_text)
            
            # ChromaDB에 추가
            self.collection.add(
                documents=[search_text],
                embeddings=[embedding],
                metadatas=[{
                    "recipe_id": recipe_id,
                    "title": recipe.get("title", ""),
                    "tags": ",".join(recipe.get("tags", [])),
                    "kcal": recipe.get("macros", {}).get("kcal", 0),
                    "carb": recipe.get("macros", {}).get("carb", 0),
                    "protein": recipe.get("macros", {}).get("protein", 0),
                    "fat": recipe.get("macros", {}).get("fat", 0),
                    "ketoized": recipe.get("ketoized", False)
                }],
                ids=[recipe_id]
            )
            
            print(f"✅ 레시피 '{recipe.get('title')}' 벡터 저장소에 추가 완료")
            return recipe_id
            
        except Exception as e:
            print(f"❌ 레시피 벡터 저장 오류: {e}")
            return None
    
    def _create_search_text(self, recipe: Dict[str, Any]) -> str:
        """레시피를 검색용 텍스트로 변환"""
        
        parts = []
        
        # 제목
        if "title" in recipe:
            parts.append(f"제목: {recipe['title']}")
        
        # 재료
        if "ingredients" in recipe:
            ingredients = []
            for ing in recipe["ingredients"]:
                if isinstance(ing, dict):
                    name = ing.get("name", "")
                    amount = ing.get("amount", "")
                    unit = ing.get("unit", "")
                    ingredients.append(f"{name} {amount}{unit}")
                else:
                    ingredients.append(str(ing))
            parts.append(f"재료: {', '.join(ingredients)}")
        
        # 조리법
        if "steps" in recipe:
            steps = ". ".join(recipe["steps"])
            parts.append(f"조리법: {steps}")
        
        # 태그
        if "tags" in recipe:
            parts.append(f"태그: {', '.join(recipe['tags'])}")
        
        # 팁
        if "tips" in recipe:
            tips = ". ".join(recipe["tips"])
            parts.append(f"팁: {tips}")
        
        # 설명
        if "content" in recipe:
            parts.append(f"설명: {recipe['content']}")
        
        return "\n".join(parts)
    
    async def search(self, query: str, max_results: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        레시피 검색
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            filters: 메타데이터 필터
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embeddings.embed_query(query)
            
            # ChromaDB 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # 결과 포맷팅
            formatted_results = []
            for i in range(len(results["ids"][0])):
                result = {
                    "recipe_id": results["ids"][0][i],
                    "title": results["metadatas"][0][i].get("title", ""),
                    "content": results["documents"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # 거리를 유사도로 변환
                    "metadata": results["metadatas"][0][i]
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 레시피 검색 오류: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보 조회"""
        try:
            data = self.collection.get()
            return {
                "collection_name": self.collection_name,
                "document_count": len(data["ids"]),
                "client_type": "ChromaDB PersistentClient"
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "error": str(e)
            }
    
    async def delete_recipe(self, recipe_id: str) -> bool:
        """레시피 삭제"""
        try:
            self.collection.delete(ids=[recipe_id])
            print(f"✅ 레시피 {recipe_id} 삭제 완료")
            return True
        except Exception as e:
            print(f"❌ 레시피 삭제 오류: {e}")
            return False
    
    async def update_recipe(self, recipe_id: str, recipe: Dict[str, Any]) -> bool:
        """레시피 업데이트"""
        try:
            # 기존 레시피 삭제
            await self.delete_recipe(recipe_id)
            
            # 새 레시피 추가
            recipe["id"] = recipe_id
            result = await self.add_recipe_to_vector_store(recipe)
            
            return result is not None
        except Exception as e:
            print(f"❌ 레시피 업데이트 오류: {e}")
            return False


def get_vector_store():
    """벡터 저장소 인스턴스 반환 (하위 호환성)"""
    return RecipeRAGTool()


# 하이브리드 검색용 도구 함수
async def hybrid_search_tool(query: str, profile: str = "", max_results: int = 5) -> List[Dict]:
    """하이브리드 검색 도구 함수"""
    rag_tool = RecipeRAGTool()
    return await rag_tool.search(query, max_results=max_results)
