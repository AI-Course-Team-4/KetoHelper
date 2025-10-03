"""
가중치 중앙 관리 시스템
환경변수 + 개인 설정 파일 하이브리드 방식
"""

import os
import sys
import importlib
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class WeightConfig:
    """가중치 설정 클래스"""
    
    # LLM 가중치
    llm_temperature: float = 0.1
    llm_max_tokens: int = 8192
    llm_timeout: int = 60
    
    # RAG 검색 가중치
    vector_search_weight: float = 0.4
    exact_ilike_weight: float = 0.35
    fts_weight: float = 0.3
    trigram_weight: float = 0.2
    ilike_fallback_weight: float = 0.15
    
    # 키토 스코어 가중치
    protein_weight: int = 15
    vegetable_weight: int = 10
    carb_penalty: int = -15
    sugar_penalty: int = -10
    processed_penalty: int = -12
    
    # 유사도 임계값
    similarity_threshold: float = 0.7
    max_search_results: int = 5
    
    # 하이브리드 검색 가중치 (식당)
    vector_score_weight: float = 1.0
    keyword_score_weight: float = 1.0
    keto_score_weight: float = 1.0
    
    # 실험 메타데이터
    experiment_name: str = "default"
    developer_name: str = "unknown"
    description: str = "기본 설정"
    
    # 프롬프트 설정
    use_personal_prompts: bool = False
    prompt_config_file: str = "personal_config.py"
    
    @classmethod
    def load_config(cls, developer_name: Optional[str] = None) -> 'WeightConfig':
        """
        가중치 설정 로드
        
        Args:
            developer_name: 개발자 이름 (soohwan, jihyun, minseok 등)
            
        Returns:
            WeightConfig: 로드된 가중치 설정
        """
        # 1. 환경변수에서 개발자 이름 확인
        env_developer = os.getenv("DEVELOPER_NAME")
        if env_developer:
            developer_name = env_developer
        
        # 2. 개인 설정 파일 로드 시도
        if developer_name and developer_name != "default":
            try:
                personal_config = cls._load_personal_config(developer_name)
                if personal_config:
                    print(f"✅ {developer_name}님의 개인 설정 로드됨")
                    return personal_config
            except Exception as e:
                print(f"⚠️ {developer_name}님의 개인 설정 로드 실패: {e}")
        
        # 3. 기본 설정 사용
        config = cls()
        print(f"✅ 기본 설정 로드됨")
        return config
    
    @classmethod
    def _load_personal_config(cls, developer_name: str) -> Optional['WeightConfig']:
        """개인 설정 파일 로드"""
        try:
            # config/weight_configs/{developer_name}.py 로드
            module_path = f"config.weight_configs.{developer_name}"
            personal_module = importlib.import_module(module_path)
            
            # PersonalWeightConfig 클래스 찾기
            if hasattr(personal_module, 'PersonalWeightConfig'):
                return personal_module.PersonalWeightConfig()
            else:
                print(f"⚠️ {developer_name}.py에 PersonalWeightConfig 클래스가 없습니다")
                return None
                
        except ImportError as e:
            print(f"⚠️ {developer_name}.py 파일을 찾을 수 없습니다: {e}")
            return None
    
    
    def print_config(self):
        """현재 설정 출력"""
        print("\n" + "="*60)
        print(f"🔧 가중치 설정 정보")
        print("="*60)
        print(f"👤 개발자: {self.developer_name}")
        print(f"🧪 실험명: {self.experiment_name}")
        print(f"📝 설명: {self.description}")
        print("\n📊 LLM 가중치:")
        print(f"  - Temperature: {self.llm_temperature}")
        print(f"  - Max Tokens: {self.llm_max_tokens}")
        print(f"  - Timeout: {self.llm_timeout}s")
        
        print("\n🔍 RAG 검색 가중치:")
        print(f"  - 벡터 검색: {self.vector_search_weight:.1%}")
        print(f"  - 정확 매칭: {self.exact_ilike_weight:.1%}")
        print(f"  - 전문 검색: {self.fts_weight:.1%}")
        print(f"  - 유사도 검색: {self.trigram_weight:.1%}")
        print(f"  - 폴백 검색: {self.ilike_fallback_weight:.1%}")
        
        print("\n🥑 키토 스코어 가중치:")
        print(f"  - 단백질: +{self.protein_weight}점")
        print(f"  - 채소: +{self.vegetable_weight}점")
        print(f"  - 탄수화물: {self.carb_penalty}점")
        print(f"  - 당분: {self.sugar_penalty}점")
        print(f"  - 가공식품: {self.processed_penalty}점")
        
        print("\n🎯 기타 설정:")
        print(f"  - 유사도 임계값: {self.similarity_threshold}")
        print(f"  - 최대 검색 결과: {self.max_search_results}개")
        print("="*60)

# 전역 가중치 설정 인스턴스
weight_config = WeightConfig.load_config()
