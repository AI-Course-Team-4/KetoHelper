"""
비로그인 사용자용 레시피 템플릿
개인화 없이 기본적인 키토 레시피 제공
"""

from typing import Dict, Any, Optional

# 비로그인 사용자용 레시피 템플릿
GUEST_RECIPE_TEMPLATES = {
    "닭가슴살": {
        "title": "키토 닭가슴살 스테이크",
        "ingredients": [
            "닭가슴살 200g",
            "올리브오일 2큰술",
            "소금, 후추 적당량",
            "마늘 2쪽",
            "로즈마리 1줄기"
        ],
        "steps": [
            "닭가슴살을 소금, 후추로 간을 맞춥니다",
            "팬에 올리브오일을 두르고 마늘과 로즈마리를 넣어 향을 냅니다",
            "닭가슴살을 넣고 앞뒤로 4-5분씩 구워줍니다",
            "완성되면 5분간 휴식시킨 후 먹습니다"
        ],
        "nutrition": {
            "calories": 250,
            "carbs": 2,
            "protein": 45,
            "fat": 8
        },
        "tips": [
            "닭가슴살을 얇게 썰어서 구우면 더 부드러워집니다",
            "구운 후 5분간 휴식시키면 육즙이 고르게 분포됩니다"
        ]
    },
    "계란": {
        "title": "키토 계란말이",
        "ingredients": [
            "계란 3개",
            "버터 1큰술",
            "소금, 후추 적당량",
            "파슬리 적당량"
        ],
        "steps": [
            "계란을 풀어서 소금, 후추로 간을 맞춥니다",
            "팬에 버터를 녹이고 계란물을 부어줍니다",
            "약한 불에서 젓가락으로 저으면서 익혀줍니다",
            "완성되면 파슬리를 뿌려줍니다"
        ],
        "nutrition": {
            "calories": 180,
            "carbs": 1,
            "protein": 15,
            "fat": 12
        },
        "tips": [
            "약한 불에서 천천히 익히면 부드러운 계란말이가 됩니다",
            "버터 대신 코코넛오일을 사용해도 좋습니다"
        ]
    },
    "연어": {
        "title": "키토 연어 스테이크",
        "ingredients": [
            "연어 200g",
            "올리브오일 2큰술",
            "소금, 후추 적당량",
            "레몬 1/2개",
            "딜 적당량"
        ],
        "steps": [
            "연어를 소금, 후추로 간을 맞춥니다",
            "팬에 올리브오일을 두르고 연어를 넣어줍니다",
            "앞뒤로 3-4분씩 구워줍니다",
            "완성되면 레몬즙과 딜을 뿌려줍니다"
        ],
        "nutrition": {
            "calories": 280,
            "carbs": 1,
            "protein": 35,
            "fat": 15
        },
        "tips": [
            "연어는 너무 오래 구우면 건조해지므로 주의하세요",
            "레몬즙을 뿌리면 비린 맛을 줄일 수 있습니다"
        ]
    },
    "아보카도": {
        "title": "키토 아보카도 샐러드",
        "ingredients": [
            "아보카도 1개",
            "토마토 1개",
            "양파 1/4개",
            "올리브오일 2큰술",
            "레몬즙 1큰술",
            "소금, 후추 적당량"
        ],
        "steps": [
            "아보카도를 적당한 크기로 썰어줍니다",
            "토마토와 양파도 썰어줍니다",
            "올리브오일, 레몬즙, 소금, 후추로 드레싱을 만듭니다",
            "모든 재료를 섞어서 완성합니다"
        ],
        "nutrition": {
            "calories": 220,
            "carbs": 8,
            "protein": 3,
            "fat": 20
        },
        "tips": [
            "아보카도는 너무 익으면 샐러드가 물컹해집니다",
            "레몬즙을 뿌리면 아보카도가 갈변하는 것을 방지할 수 있습니다"
        ]
    },
    "소고기": {
        "title": "키토 소고기 스테이크",
        "ingredients": [
            "소고기 200g",
            "버터 2큰술",
            "소금, 후추 적당량",
            "마늘 2쪽",
            "로즈마리 1줄기"
        ],
        "steps": [
            "소고기를 소금, 후추로 간을 맞춥니다",
            "팬에 버터를 녹이고 마늘과 로즈마리를 넣어 향을 냅니다",
            "소고기를 넣고 앞뒤로 3-4분씩 구워줍니다",
            "완성되면 5분간 휴식시킨 후 먹습니다"
        ],
        "nutrition": {
            "calories": 320,
            "carbs": 1,
            "protein": 40,
            "fat": 18
        },
        "tips": [
            "소고기는 실온에서 30분간 두었다가 구우면 더 맛있습니다",
            "구운 후 휴식시키면 육즙이 고르게 분포됩니다"
        ]
    },
    "새우": {
        "title": "키토 새우 볶음",
        "ingredients": [
            "새우 200g",
            "브로콜리 1컵",
            "올리브오일 2큰술",
            "마늘 2쪽",
            "소금, 후추 적당량"
        ],
        "steps": [
            "새우를 소금, 후추로 간을 맞춥니다",
            "팬에 올리브오일을 두르고 마늘을 볶습니다",
            "새우를 넣고 2-3분 볶습니다",
            "브로콜리를 넣고 1-2분 더 볶아 완성합니다"
        ],
        "nutrition": {
            "calories": 180,
            "carbs": 4,
            "protein": 25,
            "fat": 8
        },
        "tips": [
            "새우는 너무 오래 볶으면 질겨집니다",
            "브로콜리는 너무 익히지 않아야 아삭한 식감을 유지합니다"
        ]
    },
    "참치": {
        "title": "키토 참치 샐러드",
        "ingredients": [
            "참치캔 1개",
            "아보카도 1개",
            "양상추 2컵",
            "올리브오일 2큰술",
            "레몬즙 1큰술",
            "소금, 후추 적당량"
        ],
        "steps": [
            "참치캔을 열어 기름을 제거합니다",
            "아보카도를 적당한 크기로 썰어줍니다",
            "양상추를 씻어 물기를 제거합니다",
            "올리브오일, 레몬즙, 소금, 후추로 드레싱을 만듭니다",
            "모든 재료를 섞어서 완성합니다"
        ],
        "nutrition": {
            "calories": 250,
            "carbs": 6,
            "protein": 20,
            "fat": 18
        },
        "tips": [
            "참치는 기름을 완전히 제거해야 샐러드가 깔끔합니다",
            "아보카도는 바로 먹기 직전에 썰어야 갈변을 방지할 수 있습니다"
        ]
    }
}

def get_guest_recipe_template(ingredient: str) -> Optional[Dict[str, Any]]:
    """비로그인 사용자용 레시피 템플릿 반환"""
    
    # 재료명 정규화
    ingredient_lower = ingredient.lower().strip()
    
    # 직접 매칭
    if ingredient_lower in GUEST_RECIPE_TEMPLATES:
        return GUEST_RECIPE_TEMPLATES[ingredient_lower]
    
    # 부분 매칭
    for key, template in GUEST_RECIPE_TEMPLATES.items():
        if key in ingredient_lower or ingredient_lower in key:
            return template
    
    return None

def format_guest_recipe_template(template: Dict[str, Any]) -> str:
    """비로그인 사용자용 레시피 템플릿을 마크다운 형식으로 포맷팅"""
    
    # 마크다운 형식으로 포맷팅
    markdown = f"""# 🍽️ {template['title']}

## 📋 재료 (2인분)
{chr(10).join([f"- {ingredient}" for ingredient in template['ingredients']])}

## 👨‍🍳 조리법
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(template['steps'])])}

## 📊 영양 정보 (1인분 기준)
- **칼로리**: {template['nutrition']['calories']}kcal
- **탄수화물**: {template['nutrition']['carbs']}g
- **단백질**: {template['nutrition']['protein']}g
- **지방**: {template['nutrition']['fat']}g

## 💡 키토 성공 팁
{chr(10).join([f"- {tip}" for tip in template['tips']])}

## 💡 더 나은 서비스를 위해
**로그인**하시면 알레르기, 비선호 식품을 고려한 **맞춤형 레시피**를 받을 수 있습니다!"""
    
    return markdown
