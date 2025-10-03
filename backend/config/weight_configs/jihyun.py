"""
지현님 개인 실험용 가중치 설정
"""

from app.core.weight_config import WeightConfig

class PersonalWeightConfig(WeightConfig):
    """지현님의 다양성 개선 실험"""
    
    def __init__(self):
        super().__init__()
        
        # 실험 메타데이터
        self.developer_name = "jihyun"
        self.experiment_name = "diversity_improvement"
        self.description = "다양한 검색 방식 균형으로 메뉴 다양성 개선 실험"
        
        # 프롬프트 설정 (기본값 - 필요시 개인 프롬프트 추가 가능)
        self.use_personal_prompts = False
        self.prompt_config_file = "personal_config.py"
        
        # RAG 검색 가중치 개선 (다양성 우선)
        self.vector_search_weight = 0.3      # 40% → 30% (벡터 검색 감소)
        self.exact_ilike_weight = 0.25       # 35% → 25% (정확 매칭 감소)
        self.fts_weight = 0.25               # 30% → 25% (전문 검색 유지)
        self.trigram_weight = 0.15           # 20% → 15% (유사도 검색 유지)
        self.ilike_fallback_weight = 0.05    # 15% → 5% (폴백 검색 최소화)
        
        # 키토 스코어 가중치 개선 (균형 우선)
        self.protein_weight = 12            # 15 → 12 (단백질 감소)
        self.vegetable_weight = 15          # 10 → 15 (채소 강화)
        self.carb_penalty = -12             # -15 → -12 (탄수화물 패널티 완화)
        
        # 유사도 임계값 완화
        self.similarity_threshold = 0.6     # 0.7 → 0.6 (더 관대한 필터링)
        self.max_search_results = 7         # 5 → 7 (더 많은 결과)
        
        print(f"🧪 {self.experiment_name} 실험 설정 적용됨")
        print(f"📈 예상 효과: 다양성 +40%, 검색 정확도 -10%")
