#!/usr/bin/env python3
"""
LLM을 사용한 Enhanced Blob 생성 (헤더 없는 키-값 형식, 통합 최종판)
- 출력 형식: 마크다운 헤더(#) 없음. 아래 6개 키만 한 줄씩 생성:
  제목:, 핵심 요약:, 재료:, 태그:, 알레르기:, 보조 키워드:
- 입력 정규화, 재료 한/영 병기 표준화, 알레르기 자동 추출(토큰 일치 + '가루/파우더' 어근 처리)
- 태그 표준화 + 제목/설명 기반 자동 보강(저탄수/키토/다이어트 감지)
- LLM 프롬프트 강화, 출력 린트/교정
- 영양 스톱워드/고아 단위어/잔여 단위표기(T/t/약간/통/줄/꼬집/한글 수사+단위) 제거
- 근거 없는 '인분/분 내' 문구 제거
- 재료/태그/알레르기 라인은 최종적으로 입력 기반으로 강제 동기화
"""
import os
import json
import re
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# .env 파일 로드
load_dotenv('../.env')

# ==============================
# 사전/룰: 재료 영문표기 & 알레르기 매핑
# ==============================
ING_EN_MAP: Dict[str, str] = {
    # 해조/김치/채소
    "김": "seaweed",
    "김밥용김": "seaweed",
    "김치": "kimchi",
    "묵은지": "aged kimchi",
    "단무지": "pickled radish",
    "오이": "cucumber",
    "당근": "carrot",
    "양배추": "cabbage",
    "파": "green onion",
    "대파": "green onion",
    "쪽파": "green onion",
    "브로콜리": "broccoli",
    "주키니": "zucchini",
    "가지": "eggplant",
    "양송이": "mushroom",
    # 단백질/유제품
    "계란": "egg",
    "달걀": "egg",
    "소고기": "beef",
    "닭가슴살": "chicken breast",
    "닭고기": "chicken",
    "베이컨": "bacon",
    "참치": "tuna",
    "연어": "salmon",
    "치즈": "cheese",
    "모짜렐라": "mozzarella",
    "리코타": "ricotta",
    "파르메산치즈": "parmesan",
    "버터": "butter",
    "우유": "milk",
    "요거트": "yogurt",
    "생크림": "cream",
    # 견과/씨앗/오일
    "아몬드": "almond",
    "아몬드가루": "almond flour",
    "참깨": "sesame seeds",
    "참기름": "sesame oil",
    # 조미/소스
    "소금": "salt",
    "후추": "pepper",
    "마요네즈": "mayonnaise",
    "간장": "soy sauce",
    "타마리": "tamari",
    "올리브유": "olive oil",
    "마늘": "garlic",
    "토마토 페이스트": "tomato paste",
    # 감미료/기타
    "스테비아": "stevia",
    "에리스리톨": "erythritol",
    "알룰로스": "allulose",
    "레몬즙": "lemon juice",
    "애로루트파우더": "arrowroot powder",
}

ALLERGEN_RULES: Dict[str, List[str]] = {
    "계란": ["계란", "달걀", "egg"],
    "우유": ["우유", "버터", "치즈", "요거트", "리코타", "모짜렐라", "파르메산", "크림", "유청",
           "milk", "butter", "cheese", "yogurt", "cream"],
    "견과류": ["아몬드", "호두", "캐슈", "피칸", "피스타치오", "nut", "almond", "walnut",
             "cashew", "pecan", "pistachio", "peanut"],
    "대두": ["대두", "두부", "콩", "간장", "타마리", "soy", "tofu", "tamari", "soy sauce"],
    "밀": ["밀", "밀가루", "gluten", "wheat", "flour"],
    "참깨": ["참깨", "참기름", "sesame", "통깨", "볶은깨", "깨소금"],
    "생선": ["연어", "참치", "고등어", "명태", "대구", "fish", "salmon", "tuna", "mackerel", "cod", "pollock"],
    "갑각류": ["새우", "게", "랍스터", "가재", "crab", "shrimp", "lobster"],
}

MARKETING_WORDS = [
    "만들기", "레시피", "초간단", "초스피드", "꿀팁", "노하우", "No ", "NO ", "no ",
    "키토제닉", "다이어트 레시피"
]
FILLER_WORDS = ["기타", "기타 기타", "기타기타", "etc", "기타 등등"]

NUTRITION_STOPWORDS = {"단백질", "지방", "탄수화물", "순탄수", "칼로리", "당", "나트륨", "콜레스테롤", "식이섬유"}
ORPHAN_UNITS = {"팩", "대", "소", "중", "큰", "작은", "스틱", "한줌", "한", "컵", "통", "줄"}

# ==============================
# 유틸: 텍스트/태그 정규화
# ==============================
def advanced_normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    for fw in FILLER_WORDS:
        text = text.replace(fw, " ")
    for mw in MARKETING_WORDS:
        text = text.replace(mw, " ")
    text = re.sub(r"[※★♥♡`\"'#@$%^*\\/<>\[\]{}]", " ", text)
    text = text.replace("|", " ").replace("+", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def clean_title_marketing(title: str) -> str:
    title = advanced_normalize_text(title)
    title = re.sub(r"(밥)없는", r"\1 없는", title)
    title = re.sub(r"(참치)계란(김밥?)", r"\1 계란 \2", title)
    title = re.sub(r"[~!?.]+$", "", title).strip()
    return title

def normalize_tags(raw_tags: Any) -> List[str]:
    tags: List[str] = []
    if isinstance(raw_tags, str):
        try:
            raw_tags = json.loads(raw_tags)
        except Exception:
            raw_tags = [t.strip() for t in re.split(r"[,\s]+", raw_tags) if t.strip()]
    if isinstance(raw_tags, list):
        tags = [advanced_normalize_text(str(t)) for t in raw_tags if str(t).strip()]
    lower = [t.lower() for t in tags]
    has_keto = any(("키토" in t) or ("keto" in t) for t in lower)
    has_diet = any(("다이어트" in t) or ("diet" in t) for t in lower)
    has_lowcarb = any(("저탄수" in t) or ("low" in t and "carb" in t) for t in lower)
    normalized = []
    if has_keto:    normalized.append("키토(keto)")
    if has_diet:    normalized.append("다이어트(diet)")
    if has_lowcarb: normalized.append("저탄수(low-carb)")
    return normalized[:3]

def infer_tags_from_text(title: str, description: str, tags_norm: List[str]) -> List[str]:
    text = f"{title} {description}".lower()
    have = set(tags_norm)
    def add(tag: str):
        if tag not in have and tag not in tags_norm:
            tags_norm.append(tag)
    # '탄수화물 없는/무탄수/제로 탄수'도 저탄수로 간주
    if ("키토" in text or "keto" in text): add("키토(keto)")
    if ("저탄수" in text or "low carb" in text or "탄수화물 없" in text or "무탄수" in text):
        add("저탄수(low-carb)")
    if ("다이어트" in text or "diet" in text): add("다이어트(diet)")
    out = []
    for t in ["키토(keto)", "저탄수(low-carb)", "다이어트(diet)"]:
        if t in tags_norm and t not in out:
            out.append(t)
    return out[:3] if out else tags_norm[:3]

# ==============================
# 재료 파싱/정규화/영문 병기/알레르기
# ==============================
AMOUNT_PATTERN = re.compile(
    r"""
    (\(|\[|\{)[^)\]\}]*?(\)|\]|\})             # 괄호 내 비고
  | \b\d+\s*[./]?\s*\d*\s*                     # 숫자/분수(1, 1/2, 1.5 등)
    (개|장|컵|큰술|작은술|스푼|tsp|tbsp|T|t|g|kg|ml|l|L|줌|쪽|개비|알|마리|토막|줄기|조각|통|꼬집)\b
  | \b약간\b                                   # 메모성 표현
  | \b(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s*
    (개|장|컵|큰술|작은술|스푼|줌|쪽|개비|알|마리|토막|줄기|조각|통)\b   # 한글 수사+단위
  | \b반\s*(개|장|컵|큰술|작은술|스푼|통)\b                          # '반개/반 컵' 등
""", re.IGNORECASE | re.VERBOSE)

def strip_amount(text: str) -> str:
    text = AMOUNT_PATTERN.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def drop_orphan_units(token: str) -> str:
    parts = [p for p in token.split() if p not in ORPHAN_UNITS]
    return " ".join(parts).strip()

def normalize_ingredient_token(token: str) -> str:
    t = advanced_normalize_text(token)
    # 'or', '혹은' 분기표 제거 → 간단히 노이즈만 제거
    t = re.sub(r"\b(or|혹은)\b", " ", t, flags=re.IGNORECASE)
    t = strip_amount(t)
    # 대표 표기 통일/오타 교정
    t = t.replace("달걀", "계란")
    t = t.replace("김밥 김", "김").replace("김밥김", "김").replace("김밥용 김", "김")
    t = re.sub(r"\b아몬드\s*가루\b", "아몬드가루", t)         # '아몬드 가루' → '아몬드가루'
    t = re.sub(r"\b애로루트\s*파우더\b", "애로루트파우더", t) # '애로루트 파우더' 붙임
    t = re.sub(r"\b슬\s*라이스\s*치즈\b", "치즈", t)          # '슬 라이스치즈' → '치즈'
    t = t.replace("깨소금", "참깨")                           # 알레르기 인식 위해 매핑
    t = drop_orphan_units(t)
    return t

def kor_eng_bilingual(token: str) -> str:
    en = ING_EN_MAP.get(token)
    return f"{token}({en})" if en else token

def extract_ingredients_from_json(ingredients_data: Any) -> List[str]:
    items: List[str] = []
    if isinstance(ingredients_data, str):
        try:
            ingredients_data = json.loads(ingredients_data)
        except Exception:
            ingredients_data = [s.strip() for s in ingredients_data.split(",") if s.strip()]
    if isinstance(ingredients_data, list):
        for item in ingredients_data:
            if isinstance(item, dict):
                name = item.get("name") or item.get("ingredient") or ""
                if name:
                    items.append(normalize_ingredient_token(name))
            elif isinstance(item, str):
                items.append(normalize_ingredient_token(item))
    seen = set()
    result: List[str] = []
    for x in items:
        if x and x not in seen:
            seen.add(x); result.append(x)
    result = [x for x in result if x not in NUTRITION_STOPWORDS]
    return result

def infer_allergens_from_ingredients(ingredients_kor: List[str]) -> List[str]:
    def canon(tok: str) -> str:
        # '아몬드가루' → '아몬드', '참깨파우더' → '참깨'
        return re.sub(r"(가루|분말|파우더)$", "", tok)
    tokens = {canon(t) for t in ingredients_kor}
    joined_lower = " ".join(canon(t) for t in ingredients_kor).lower()
    allergens_found: List[str] = []
    for label, keywords in ALLERGEN_RULES.items():
        for kw in keywords:
            if re.match(r"^[가-힣]+$", kw):
                if kw in tokens:
                    allergens_found.append(label); break
            else:
                if re.search(rf"\b{re.escape(kw.lower())}\b", joined_lower):
                    allergens_found.append(label); break
    order = ["계란", "우유", "견과류", "대두", "밀", "참깨", "생선", "갑각류"]
    seen = set()
    dedup_sorted = [a for a in order if (a in allergens_found and not (a in seen or seen.add(a)))]
    return dedup_sorted or ["해당 없음"]

# ==============================
# LLM 프롬프트 & 후처리
# ==============================
def build_llm_prompt(title: str, description: str, tags_norm: List[str],
                     ingredients_kor: List[str], ingredients_bilingual: List[str],
                     allergens: List[str]) -> str:
    tags_str = ", ".join(tags_norm) if tags_norm else "(없음)"
    ing_kor_str = ", ".join(ingredients_kor[:10]) if ingredients_kor else "(없음)"
    ing_bi_str = ", ".join(ingredients_bilingual[:10]) if ingredients_bilingual else "(없음)"
    allergens_str = ", ".join(allergens)
    return f"""
다음 레시피 정보를 분석해 임베딩 전용 Blob 텍스트를 만들어주세요.
마크다운 헤더(#)를 절대 사용하지 말고, 아래 6개의 키-값 라인만 출력하세요.
각 라인은 한 줄로, 라벨과 콜론 뒤에 내용을 적습니다. 빈 줄을 넣지 마세요.

제목(정규화): {title}
설명(정규화): {description}
태그(표준화): {tags_str}
재료(한글): {ing_kor_str}
재료(한/영 병기 추천): {ing_bi_str}
알레르기(재료 기반, 이 목록만 사용): {allergens_str}

형식(정확히 이 순서/라벨):
제목: [마케팅 단어 제거된 깔끔한 제목]
핵심 요약: [자연어 2~3문장. 사실 기반 설명만. '+' 금지. '요리 종류는/건강 특성은/한 줄 설명은' 같은 메타 문장 금지]
재료: [상위 핵심 재료 5~7개, 가능한 경우 한/영 병기. 예) 계란(egg), 김(seaweed)]
태그: [핵심 태그 최대 3개. 예) 키토(keto), 다이어트(diet), 저탄수(low-carb)]
알레르기: [아래 제공 목록과 동일하게 출력: {allergens_str}]
보조 키워드: [검색 보조 키워드 5~8개. 예) 무설탕, 밀가루 무첨가, 저탄수 디저트, 도시락, 간편 한끼]

제약:
- 존재하지 않는 정보 추정/창작 금지
- 불용어/장식어/과장 표현 금지
- 콜론(:)과 라벨 철자/순서 고정
- 섹션 헤더(#) 절대 사용 금지
""".strip()

def lint_and_fix_blob(text: str) -> str:
    if not text:
        return text
    # low carb → low-carb, dlow-carb 교정
    text = re.sub(r"\blow\s*carb\b", "low-carb", text, flags=re.IGNORECASE)
    text = text.replace("dlow-carb", "low-carb")
    # 묵은지/단무지 영어 표기 교정
    text = text.replace("묵은지(pickled radish)", "묵은지(aged kimchi)")
    text = text.replace("단무지(aged kimchi)", "단무지(pickled radish)")
    # 플러스 기호 금지
    text = text.replace("+", " ")
    # 인라인 라벨이 한 줄에 붙은 경우 줄바꿈으로 분리
    text = re.sub(r"\s*(제목|핵심 요약|재료|태그|알레르기|보조 키워드)\s*:\s*", r"\n\1: ", text)
    text = text.strip()
    # 선행 개행 제거
    text = re.sub(r"^\n+", "", text)
    # 중복 공백/개행 최소화
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def strip_meta_sentences(text: str) -> str:
    if not text:
        return text
    # 메타 서술 제거 (핵심 요약 라인 내에서)
    text = re.sub(r"핵심 요약:\s*(요리\s*종류는|건강\s*특성은|한\s*줄\s*설명은)[^.。!?]+[.。!?]\s*", "핵심 요약: ", text)
    # 연속 공백 정리
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def replace_kv_line(blob_text: str, label: str, content_line: str) -> str:
    """
    지정 라벨의 '라벨: 값' 라인을 교체. 없으면 맨 끝에 추가.
    """
    patt = re.compile(rf"^(?:{re.escape(label)})\s*:\s*.*$", re.MULTILINE)
    if patt.search(blob_text):
        return patt.sub(f"{label}: {content_line}", blob_text)
    sep = "\n" if blob_text and not blob_text.endswith("\n") else ""
    return f"{blob_text}{sep}{label}: {content_line}"

def strip_unbacked_serving_time(text: str, has_serv: bool, has_time: bool) -> str:
    if not text:
        return text
    if not has_serv:
        text = re.sub(r"\b\d+\s*인분\b", "", text)
    if not has_time:
        text = re.sub(r"\b\d+\s*분\s*내?\b", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()

# ==============================
# LLM 호출
# ==============================
def llm_enhance_blob(recipe: dict, openai_client: OpenAI) -> str:
    raw_title = recipe.get("title") or ""
    raw_desc = recipe.get("summary") or recipe.get("description") or ""
    raw_tags = recipe.get("tags", [])
    ingredients_data = recipe.get("ingredients", [])

    # 정규화/표준화
    title = clean_title_marketing(raw_title)
    description = advanced_normalize_text(raw_desc)
    tags_norm = infer_tags_from_text(title, description, normalize_tags(raw_tags))

    ing_kor = extract_ingredients_from_json(ingredients_data)
    ing_bi = [kor_eng_bilingual(tok) for tok in ing_kor]

    allergens = infer_allergens_from_ingredients(ing_kor)

    prompt = build_llm_prompt(title, description, tags_norm, ing_kor, ing_bi, allergens)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": ("당신은 레시피 메타데이터를 임베딩용 키-값 Blob으로 직렬화하는 전문가입니다. "
                             "라벨 철자/순서/콜론을 고정하고, 입력 사실만을 짧은 자연어로 작성하세요.")},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=800,
        )
        llm_result = response.choices[0].message.content or ""

        # --- 후처리 파이프라인 ---
        llm_result = lint_and_fix_blob(llm_result)
        llm_result = strip_meta_sentences(llm_result)

        # 입력 기반으로 재료/태그/알레르기 라인 강제 동기화
        if ing_bi:
            llm_result = replace_kv_line(llm_result, "재료", ", ".join(ing_bi[:7]))
        if tags_norm:
            llm_result = replace_kv_line(llm_result, "태그", ", ".join(tags_norm))
        llm_result = replace_kv_line(llm_result, "알레르기", ", ".join(allergens))

        # 근거 없는 '인분/분 내' 문구 제거
        has_serv = bool(recipe.get("servings"))
        has_time = bool(recipe.get("time") or recipe.get("cook_time") or recipe.get("duration"))
        llm_result = strip_unbacked_serving_time(llm_result, has_serv, has_time)

        time.sleep(0.1)
        return llm_result

    except Exception as e:
        print(f"LLM Enhanced Blob 생성 실패: {e}")
        # 실패 시 최소 안전값
        fallback_tags = ", ".join(tags_norm[:3]) if tags_norm else ""
        fallback_ing = ", ".join(ing_bi[:7]) if ing_bi else ""
        fallback_allerg = ", ".join(allergens)
        return (
            f"제목: {title}\n"
            f"핵심 요약: 간단한 건강 지향 요리 설명(입력 기반).\n"
            f"재료: {fallback_ing}\n"
            f"태그: {fallback_tags}\n"
            f"알레르기: {fallback_allerg}\n"
            f"보조 키워드: 무설탕, 밀가루 무첨가, 저탄수, 간편 한끼"
        )

# ==============================
# 테스트: Supabase에서 10건 가져와 생성
# ==============================
def test_llm_enhanced_blob_generation():
    print("=== LLM을 사용한 Enhanced Blob 생성 테스트 (10개) ===")
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    try:
        result = client.table("recipes_keto_raw").select("*").limit(10).execute()
        if not result.data:
            print("❌ 데이터가 없습니다.")
            return
        for i, recipe in enumerate(result.data, 1):
            print(f"\n{i}. 원본 제목: {str(recipe.get('title', ''))[:60]}")
            enhanced_blob = llm_enhance_blob(recipe, openai_client)
            print("   LLM Enhanced Blob:")
            print(enhanced_blob)
            print("   ---")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_llm_enhanced_blob_generation()
