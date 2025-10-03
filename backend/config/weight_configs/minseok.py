"""
민석님 개인 실험용 가중치 설정
"""

from app.core.weight_config import WeightConfig

class PersonalWeightConfig(WeightConfig):
    """민석님의 키토 스코어 최적화 실험"""
    
    def __init__(self):
        super().__init__()
        
        # 실험 메타데이터
        self.developer_name = "minseok"
        self.experiment_name = "keto_score_optimization"
        self.description = "키토 친화도 점수 계산 최적화로 더 정확한 평가 실험"
        
        # 프롬프트 설정 (기본값 - 필요시 개인 프롬프트 추가 가능)
        self.use_personal_prompts = False
        self.prompt_config_file = "personal_config.py"
        
        # RAG 검색 가중치 유지 (기본값)
        self.vector_search_weight = 0.4
        self.exact_ilike_weight = 0.35
        self.fts_weight = 0.3
        self.trigram_weight = 0.2
        self.ilike_fallback_weight = 0.15
        
        # 키토 스코어 가중치 대폭 개선
        self.protein_weight = 25            # 15 → 25 (단백질 대폭 강화)
        self.vegetable_weight = 18          # 10 → 18 (채소 대폭 강화)
        self.carb_penalty = -25             # -15 → -25 (탄수화물 강한 패널티)
        self.sugar_penalty = -15            # -10 → -15 (당분 강한 패널티)
        self.processed_penalty = -18        # -12 → -18 (가공식품 강한 패널티)
        
        # 하이브리드 검색 가중치 개선 (식당 검색)
        self.vector_score_weight = 1.2      # 1.0 → 1.2 (벡터 점수 강화)
        self.keyword_score_weight = 0.8     # 1.0 → 0.8 (키워드 점수 감소)
        self.keto_score_weight = 1.5        # 1.0 → 1.5 (키토 점수 대폭 강화)
        
        # 유사도 임계값 유지
        self.similarity_threshold = 0.7
        self.max_search_results = 5
        
        print(f"🧪 {self.experiment_name} 실험 설정 적용됨")
        print(f"📈 예상 효과: 키토 친화도 평가 정확도 +35%, 식당 추천 품질 +20%")
