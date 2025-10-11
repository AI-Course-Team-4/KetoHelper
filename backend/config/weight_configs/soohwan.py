"""
수환님 개인 실험용 가중치 설정
"""

from app.core.weight_config import WeightConfig
import os

class PersonalWeightConfig(WeightConfig):
    """수환님의 검색 성능 실험 - 세트 A/B + 레거시 유지

    세트 전환: 환경변수 WEIGHT_SET=balanced|fast|legacy (기본 balanced)
    """

    def __init__(self):
        super().__init__()

        # 실험 메타데이터
        self.developer_name = "soohwan"
        self.experiment_name = "weight_set_ab"
        self.description = "가중치 세트 A/B 전환으로 속도·안정성 균형 실험"

        # 프롬프트 설정
        self.use_personal_prompts = True
        self.prompt_config_file = "personal_config_soohwan.py"

        # 기본 스코어 가중치(레시피 스코어링)
        self.protein_weight = 20
        self.vegetable_weight = 12
        self.carb_penalty = -20

        # 세트 선택
        set_name = os.getenv("WEIGHT_SET", "balanced").lower().strip()

        if set_name == "fast":
            # Set A: 빠름(보수적 필터+적은 결과)
            self.vector_search_weight = 0.55
            self.exact_ilike_weight = 0.35
            self.fts_weight = 0.10
            self.trigram_weight = 0.0
            self.ilike_fallback_weight = 0.0
            self.similarity_threshold = 0.80
            self.max_search_results = 3
            speed_desc = "fast"
        elif set_name == "legacy":
            # 기존 soohwan 세팅(정확도 강화, 더 엄격)
            self.vector_search_weight = 0.5
            self.exact_ilike_weight = 0.3
            self.fts_weight = 0.2
            self.trigram_weight = 0.0
            self.ilike_fallback_weight = 0.0
            self.similarity_threshold = 0.80
            self.max_search_results = 3
            speed_desc = "legacy"
        else:
            # Set B: 균형(기본) - 품질/속도 균형, 무결과 리스크 완화
            self.vector_search_weight = 0.55
            self.exact_ilike_weight = 0.30
            self.fts_weight = 0.15
            self.trigram_weight = 0.0
            self.ilike_fallback_weight = 0.0
            self.similarity_threshold = 0.70
            self.max_search_results = 5
            speed_desc = "balanced"

        # LLM 타임아웃/토큰(테스트용 합리 범위 유지)
        self.llm_timeout = 180
        self.llm_max_tokens = 8192

        print(f"🧪 soohwan weight-set 적용: set={speed_desc}, thr={self.similarity_threshold}, k={self.max_search_results}, V/K/E={self.vector_search_weight}/{self.exact_ilike_weight}/{self.fts_weight}")
