"""
수환님 개인 실험용 가중치 설정
"""

from app.core.weight_config import WeightConfig

class PersonalWeightConfig(WeightConfig):
    """수환님의 검색 정확도 개선 실험"""
    
    def __init__(self):
        super().__init__()
        
        # 실험 메타데이터
        self.developer_name = "soohwan"
        self.experiment_name = "search_accuracy_improvement"
        self.description = "벡터 검색 가중치 증가로 검색 정확도 개선 실험"
        
        # 프롬프트 설정
        self.use_personal_prompts = True
        self.prompt_config_file = "personal_config_soohwan.py"
        
        # RAG 검색 가중치 개선 (정확도 우선)
        self.vector_search_weight = 0.5      # 40% → 50% (벡터 검색 강화)
        self.exact_ilike_weight = 0.3        # 35% → 30% (정확 매칭 유지)
        self.fts_weight = 0.2               # 30% → 20% (전문 검색 감소)
        self.trigram_weight = 0.0            # 20% → 0% (유사도 검색 제거)
        self.ilike_fallback_weight = 0.0     # 15% → 0% (폴백 검색 제거)
        
        # 키토 스코어 가중치 개선 (단백질 우선)
        self.protein_weight = 20            # 15 → 20 (단백질 강화)
        self.vegetable_weight = 12          # 10 → 12 (채소 강화)
        self.carb_penalty = -20             # -15 → -20 (탄수화물 강한 패널티)
        
        # 유사도 임계값 강화
        self.similarity_threshold = 0.8     # 0.7 → 0.8 (더 엄격한 필터링)
        self.max_search_results = 2         # 5 → 3 (더 정확한 결과만)
        
        print(f"🧪 {self.experiment_name} 실험 설정 적용됨")
