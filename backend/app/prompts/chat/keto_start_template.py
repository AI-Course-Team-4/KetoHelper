"""
키토 다이어트 시작 가이드 템플릿
"""

KETO_START_TEMPLATE = """
# 🥑 키토 다이어트 시작 가이드

## 📋 프로필 정보
- **목표 칼로리**: {kcal_target}kcal
- **탄수화물 제한**: {carbs_limit}g
{profile_section}

## ⚠️ 중요 안전 수칙
{alergies_warning}

## 🍽️ 추천 식품 목록

### 단백질
- **닭고기**: 가슴살, 다리살 (껍질 포함)
- **돼지고기**: 삼겹살, 목살, 앞다리살
- **소고기**: 갈비살, 차돌박이, 등심
- **오리고기**

### 지방
- **라드** (돼지기름), **탈로우** (소기름)
- **해바라기씨유**, **포도씨유**

### 채소 (저탄수화물)
- **잎채소**: 시금치, 케일, 상추, 로메인
- **주키니** (애호박과 유사)
- **무**, **아스파라거스** (소량)

### 음료
- **물**, **블랙커피**, **무가당 허브차**

### 조미료
- **소금**, **후추**
- **비선호 목록에 없는 단일 향신료**

## 🎯 핵심 조언

1. **의료 전문가 상담 필수**: 제한적인 식단으로 인한 영양 결핍 방지
2. **식품 일기 작성**: 알레르기 반응 및 영양소 섭취량 확인
3. **수분 및 전해질 섭취**: 충분한 물과 소금 섭취
4. **인내심과 실험**: 새로운 식단에 적응하는 시간 필요

## ⚡ 빠른 시작 팁
- 허용되는 식품으로 간단한 조리법부터 시작
- 맛이 단조로울 수 있으니 다양한 조리법 시도
- 새로운 식품은 소량부터 시작하여 반응 확인

**건강을 최우선으로 생각하고, 반드시 전문가의 도움을 받으세요!** 💪
"""

def format_keto_start_guide(profile: dict) -> str:
    """키토 시작 가이드 포맷팅"""
    
    # 기본값 설정 (게스트 사용자용)
    kcal_target = profile.get('goals_kcal', 2400)  # 1200 → 2400으로 변경
    carbs_limit = profile.get('goals_carbs_g', 20)
    
    # 알레르기 처리
    allergies = profile.get('allergies', [])
    if allergies:
        allergies_text = f"{', '.join(allergies)} 알레르기 있음"
        allergies_list = ', '.join(allergies)
        allergies_section = f"- **알레르기**: {allergies_text}"
    else:
        allergies_text = "알레르기 없음"
        allergies_list = "없음"
        allergies_section = ""
    
    # 비선호 식품 처리
    dislikes = profile.get('dislikes', [])
    if dislikes:
        dislikes_text = f"{', '.join(dislikes)} 비선호"
        dislikes_section = f"- **비선호 식품**: {dislikes_text}"
    else:
        dislikes_text = "비선호 식품 없음"
        dislikes_section = ""
    
    # 프로필 섹션 구성
    profile_sections = []
    if allergies_section:
        profile_sections.append(allergies_section)
    if dislikes_section:
        profile_sections.append(dislikes_section)
    
    profile_text = "\n".join(profile_sections) if profile_sections else ""
    
    # 알레르기 경고 섹션
    if allergies:
        allergies_warning = f"**알레르기 식품은 절대 금지!** {allergies_list}는 어떤 형태로든 섭취해서는 안 됩니다."
    else:
        allergies_warning = "**안전한 식품만 선택하세요!** 알레르기 반응이 있는 식품은 피하세요."
    
    return KETO_START_TEMPLATE.format(
        kcal_target=kcal_target,
        carbs_limit=carbs_limit,
        allergies_text=allergies_text,
        dislikes_text=dislikes_text,
        allergies_list=allergies_list,
        profile_section=profile_text,
        alergies_warning=allergies_warning
    )
