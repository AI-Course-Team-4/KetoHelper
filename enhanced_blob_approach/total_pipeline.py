#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 파이프라인 (기본 210개 전부 처리):
Raw(recipes_keto_raw) → LLM Enhanced Blob(키-값, 헤더없음) → Embedding(라벨 제거본) → Supabase Upsert

전제:
- SQL Editor에 'recipes_keto_enhanced' 테이블과 RPC 'fn_upsert_recipe_enhanced'가 배포되어 있어야 함
- OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY(또는 ANON_KEY) 가 .env에 존재

모델:
- Chat: gpt-4o-mini
- Embedding: text-embedding-3-small (1536차원)

기본값:
- TOTAL_LIMIT = 210  (원하신 대로 전체 210개 기본 처리)
- BATCH_SIZE = 20
- START_OFFSET = 0   (필요시 환경변수로 바꿔서 이어서 처리 가능)

주의:
- 업서트는 source_id(UUID)를 기준으로 동작. raw.id가 UUID가 아니면 중복 생길 수 있음.
  필요시 SQL에 fingerprint UNIQUE를 추가하거나, SKIP_EXISTING 옵션을 True로 주면 기존 처리건을 건너뜀.
"""

import os
import re
import json
import time
import uuid
from typing import Any, Dict, List, Tuple, Optional

from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# ==============================
# 환경변수 로드
# ==============================
load_dotenv('../.env')  # 경로는 프로젝트 구조에 맞게 조정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

# 기본 처리 범위(요청 사항 반영: 210개)
DEFAULT_TOTAL_LIMIT = 210
DEFAULT_BATCH_SIZE = 20
DEFAULT_START_OFFSET = 0

# 검색/속도
SLEEP_SEC = 0.1
EMBED_MODEL = "text-embedding-3-small"  # 1536
CHAT_MODEL = "gpt-4o-mini"

# 이미 처리된 source_id 건너뛰기 (기본 False: 전체 210 재처리/업서트)
SKIP_EXISTING = os.getenv("SKIP_EXISTING", "false").lower() == "true"


# ==============================
# 사전/룰: 재료 영문표기 & 알레르기 매핑
# ==============================
ING_EN_MAP: Dict[str, str] = {
    # 해조/김치/채소
    "김": "seaweed", "김밥용김": "seaweed", "김치": "kimchi", "묵은지": "aged kimchi",
    "단무지": "pickled radish", "오이": "cucumber", "당근": "carrot", "양배추": "cabbage",
    "파": "green onion", "대파": "green onion", "쪽파": "green onion",
    "브로콜리": "broccoli", "주키니": "zucchini", "가지": "eggplant", "양송이": "mushroom",
    # 단백질/유제품
    "계란": "egg", "달걀": "egg", "소고기": "beef", "닭가슴살": "chicken breast",
    "닭고기": "chicken", "베이컨": "bacon", "참치": "tuna", "연어": "salmon",
    "치즈": "cheese", "모짜렐라": "mozzarella", "리코타": "ricotta", "파르메산치즈": "parmesan",
    "버터": "butter", "우유": "milk", "요거트": "yogurt", "생크림": "cream",
    # 견과/씨앗/오일
    "아몬드": "almond", "아몬드가루": "almond flour", "참깨": "sesame seeds", "참기름": "sesame oil",
    # 조미/소스/감미료
    "소금": "salt", "후추": "pepper", "마요네즈": "mayonnaise", "간장": "soy sauce", "타마리": "tamari",
    "올리브유": "olive oil", "마늘": "garlic", "토마토 페이스트": "tomato paste",
    "스테비아": "stevia", "에리스리톨": "erythritol", "알룰로스": "allulose",
    "레몬즙": "lemon juice", "애로루트파우더": "arrowroot powder",
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

MARKETING_WORDS = ["만들기","레시피","초간단","초스피드","꿀팁","노하우","No ","NO ","no ","키토제닉","다이어트 레시피"]
FILLER_WORDS = ["기타","기타 기타","기타기타","etc","기타 등등"]
NUTRITION_STOPWORDS = {"단백질","지방","탄수화물","순탄수","칼로리","당","나트륨","콜레스테롤","식이섬유"}
ORPHAN_UNITS = {"팩","대","소","중","큰","작은","스틱","한줌","한","컵","통","줄"}

AMOUNT_PATTERN = re.compile(r"""
    (\(|\[|\{)[^)\]\}]*?(\)|\]|\})                               # 괄호 내 비고
  | \b\d+\s*[./]?\s*\d*\s*(개|장|컵|큰술|작은술|스푼|tsp|tbsp|T|t|g|kg|ml|l|L|줌|쪽|개비|알|마리|토막|줄기|조각|통|꼬집)\b
  | \b약간\b
  | \b(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s*(개|장|컵|큰술|작은술|스푼|줌|쪽|개비|알|마리|토막|줄기|조각|통)\b
  | \b반\s*(개|장|컵|큰술|작은술|스푼|통)\b
""", re.IGNORECASE | re.VERBOSE)


# ==============================
# 유틸: 텍스트/태그 정규화
# ==============================
def advanced_normalize_text(text: str) -> str:
    if not text: return ""
    text = text.strip()
    for fw in FILLER_WORDS: text = text.replace(fw, " ")
    for mw in MARKETING_WORDS: text = text.replace(mw, " ")
    text = re.sub(r"[※★♥♡`\"'#@$%^*\\/<>\[\]{}]", " ", text)
    text = text.replace("|", " ").replace("+", " ")
    return re.sub(r"\s+", " ", text).strip()

def clean_title_marketing(title: str) -> str:
    title = advanced_normalize_text(title)
    title = re.sub(r"(밥)없는", r"\1 없는", title)
    title = re.sub(r"(참치)계란(김밥?)", r"\1 계란 \2", title)
    return re.sub(r"[~!?.]+$", "", title).strip()

def normalize_tags(raw_tags: Any) -> List[str]:
    tags: List[str] = []
    if isinstance(raw_tags, str):
        try: raw_tags = json.loads(raw_tags)
        except: raw_tags = [t.strip() for t in re.split(r"[,\s]+", raw_tags) if t.strip()]
    if isinstance(raw_tags, list):
        tags = [advanced_normalize_text(str(t)) for t in raw_tags if str(t).strip()]
    lower = [t.lower() for t in tags]
    has_keto = any(("키토" in t) or ("keto" in t) for t in lower)
    has_diet = any(("다이어트" in t) or ("diet" in t) for t in lower)
    has_lowcarb = any(("저탄수" in t) or ("low" in t and "carb" in t) for t in lower)
    out = []
    if has_keto: out.append("키토(keto)")
    if has_diet: out.append("다이어트(diet)")
    if has_lowcarb: out.append("저탄수(low-carb)")
    return out[:3]

def infer_tags_from_text(title: str, description: str, tags_norm: List[str]) -> List[str]:
    text = f"{title} {description}".lower()
    have = set(tags_norm)
    def add(tag: str):
        if tag not in have and tag not in tags_norm:
            tags_norm.append(tag)
    if ("키토" in text or "keto" in text): add("키토(keto)")
    if ("저탄수" in text or "low carb" in text or "탄수화물 없" in text or "무탄수" in text): add("저탄수(low-carb)")
    if ("다이어트" in text or "diet" in text): add("다이어트(diet)")
    ordered = []
    for t in ["키토(keto)","저탄수(low-carb)","다이어트(diet)"]:
        if t in tags_norm and t not in ordered:
            ordered.append(t)
    return ordered[:3] if ordered else tags_norm[:3]


# ==============================
# 재료 파싱/정규화/영문 병기/알레르기
# ==============================
def strip_amount(text: str) -> str:
    return re.sub(r"\s+", " ", AMOUNT_PATTERN.sub(" ", text)).strip()

def drop_orphan_units(token: str) -> str:
    return " ".join([p for p in token.split() if p not in ORPHAN_UNITS]).strip()

def normalize_ingredient_token(token: str) -> str:
    t = advanced_normalize_text(token)
    t = re.sub(r"\b(or|혹은)\b", " ", t, flags=re.IGNORECASE)  # or/혹은 제거
    t = strip_amount(t)
    # 대표 표기 통일/오타 교정
    t = t.replace("달걀", "계란")
    t = t.replace("김밥 김", "김").replace("김밥김", "김").replace("김밥용 김", "김")
    t = re.sub(r"\b아몬드\s*가루\b", "아몬드가루", t)
    t = re.sub(r"\b애로루트\s*파우더\b", "애로루트파우더", t)
    t = re.sub(r"\b슬\s*라이스\s*치즈\b", "치즈", t)
    t = t.replace("깨소금", "참깨")  # 알레르기 인식 위해 매핑
    return drop_orphan_units(t)

def kor_eng_bilingual(token: str) -> str:
    en = ING_EN_MAP.get(token)
    return f"{token}({en})" if en else token

def extract_ingredients_from_json(ingredients_data: Any) -> List[str]:
    items: List[str] = []
    if isinstance(ingredients_data, str):
        try: ingredients_data = json.loads(ingredients_data)
        except: ingredients_data = [s.strip() for s in ingredients_data.split(",") if s.strip()]
    if isinstance(ingredients_data, list):
        for item in ingredients_data:
            if isinstance(item, dict):
                name = item.get("name") or item.get("ingredient") or ""
                if name: items.append(normalize_ingredient_token(name))
            elif isinstance(item, str):
                items.append(normalize_ingredient_token(item))
    seen, result = set(), []
    for x in items:
        if x and x not in seen:
            seen.add(x); result.append(x)
    return [x for x in result if x not in NUTRITION_STOPWORDS]

def infer_allergens_from_ingredients(ingredients_kor: List[str]) -> List[str]:
    def canon(tok: str) -> str:
        return re.sub(r"(가루|분말|파우더)$", "", tok)
    tokens = {canon(t) for t in ingredients_kor}
    joined_lower = " ".join(canon(t) for t in ingredients_kor).lower()
    found: List[str] = []
    for label, kws in ALLERGEN_RULES.items():
        for kw in kws:
            if re.match(r"^[가-힣]+$", kw):
                if kw in tokens: found.append(label); break
            else:
                if re.search(rf"\b{re.escape(kw.lower())}\b", joined_lower):
                    found.append(label); break
    order = ["계란","우유","견과류","대두","밀","참깨","생선","갑각류"]
    seen = set()
    out = [a for a in order if (a in found and not (a in seen or seen.add(a)))]
    return out or ["해당 없음"]


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
마크다운 헤더(#)는 사용하지 말고, 아래 6개의 키-값 라인만 출력하세요.
각 라인은 한 줄로, 라벨과 콜론 뒤에 내용을 적습니다. 빈 줄을 넣지 마세요.

제목(정규화): {title}
설명(정규화): {description}
태그(표준화): {tags_str}
재료(한글): {ing_kor_str}
재료(한/영 병기 추천): {ing_bi_str}
알레르기(재료 기반, 이 목록만 사용): {allergens_str}

형식(정확히 이 순서/라벨):
제목: [마케팅 단어 제거된 깔끔한 제목]
핵심 요약: [자연어 2~3문장. 사실 기반 설명만. '+' 금지. 메타 문장 금지]
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
    if not text: return text
    text = re.sub(r"\blow\s*carb\b", "low-carb", text, flags=re.IGNORECASE)
    text = text.replace("dlow-carb", "low-carb")
    text = text.replace("묵은지(pickled radish)", "묵은지(aged kimchi)")
    text = text.replace("단무지(aged kimchi)", "단무지(pickled radish)")
    text = text.replace("+", " ")
    # 인라인 라벨이 한 줄에 붙은 경우 줄바꿈으로 분리
    text = re.sub(r"\s*(제목|핵심 요약|재료|태그|알레르기|보조 키워드)\s*:\s*", r"\n\1: ", text)
    text = re.sub(r"^\n+", "", text).strip()
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{2,}", "\n", text).strip()

def strip_meta_sentences(text: str) -> str:
    if not text: return text
    text = re.sub(r"핵심 요약:\s*(요리\s*종류는|건강\s*특성은|한\s*줄\s*설명은)[^.。!?]+[.。!?]\s*", "핵심 요약: ", text)
    return re.sub(r"[ \t]+", " ", text).strip()

def replace_kv_line(blob_text: str, label: str, content_line: str) -> str:
    patt = re.compile(rf"^(?:{re.escape(label)})\s*:\s*.*$", re.MULTILINE)
    if patt.search(blob_text):
        return patt.sub(f"{label}: {content_line}", blob_text)
    sep = "\n" if blob_text and not blob_text.endswith("\n") else ""
    return f"{blob_text}{sep}{label}: {content_line}"

def strip_unbacked_serving_time(text: str, has_serv: bool, has_time: bool) -> str:
    if not text: return text
    if not has_serv: text = re.sub(r"\b\d+\s*인분\b", "", text)
    if not has_time: text = re.sub(r"\b\d+\s*분\s*내?\b", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()

def ensure_kv_fields(blob: str) -> str:
    """6개 라벨이 모두 존재하도록 보정"""
    required = ["제목","핵심 요약","재료","태그","알레르기","보조 키워드"]
    present = {m.group(1) for m in re.finditer(r"^(제목|핵심 요약|재료|태그|알레르기|보조 키워드)\s*:", blob, re.M)}
    for k in required:
        if k not in present:
            blob += f"\n{k}: "
    return blob.strip()

def to_embed_input(blob: str) -> str:
    """임베딩 입력에서 라벨 제거 (시맨틱 노이즈 감소)"""
    return re.sub(r"^(제목|핵심 요약|재료|태그|알레르기|보조 키워드)\s*:\s*", "", blob, flags=re.M).strip()


# ==============================
# OpenAI 호출 (LLM/임베딩)
# ==============================
def llm_enhance_blob(recipe: dict, openai_client: OpenAI) -> Tuple[str, Dict[str, Any]]:
    """blob_text, meta(title, ingredients_bi, tags, allergens)"""
    raw_title = recipe.get("title") or ""
    raw_desc = recipe.get("summary") or recipe.get("description") or ""
    raw_tags = recipe.get("tags", [])
    ingredients_data = recipe.get("ingredients", [])

    title = clean_title_marketing(raw_title)
    description = advanced_normalize_text(raw_desc)
    tags_norm = infer_tags_from_text(title, description, normalize_tags(raw_tags))

    ing_kor = extract_ingredients_from_json(ingredients_data)
    ing_bi = [kor_eng_bilingual(tok) for tok in ing_kor]
    allergens = infer_allergens_from_ingredients(ing_kor)

    prompt = build_llm_prompt(title, description, tags_norm, ing_kor, ing_bi, allergens)

    resp = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role":"system","content":"당신은 레시피 메타데이터를 임베딩용 키-값 Blob으로 직렬화하는 전문가입니다. 라벨 철자/순서/콜론을 고정하고, 입력 사실만을 짧은 자연어로 작성하세요."},
            {"role":"user","content":prompt},
        ],
        temperature=0.1,
        max_tokens=800,
    )
    blob = resp.choices[0].message.content or ""
    blob = lint_and_fix_blob(blob)
    blob = strip_meta_sentences(blob)

    # 입력 기반 강제 동기화
    if ing_bi:
        blob = replace_kv_line(blob, "재료", ", ".join(ing_bi[:7]))
    if tags_norm:
        blob = replace_kv_line(blob, "태그", ", ".join(tags_norm))
    blob = replace_kv_line(blob, "알레르기", ", ".join(allergens))
    blob = ensure_kv_fields(blob)

    # 근거 없는 '인분/분 내' 문구 제거
    has_serv = bool(recipe.get("servings"))
    has_time = bool(recipe.get("time") or recipe.get("cook_time") or recipe.get("duration"))
    blob = strip_unbacked_serving_time(blob, has_serv, has_time)

    meta = {
        "title": title,
        "ingredients_bi": ing_bi[:7],
        "tags": tags_norm,
        "allergens": allergens,
    }
    time.sleep(SLEEP_SEC)
    return blob, meta

def embed_text(openai_client: OpenAI, text: str) -> List[float]:
    """OpenAI 임베딩 생성 (1536차원)"""
    if len(text) > 8000:
        text = text[:8000]
    emb = openai_client.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding
    time.sleep(SLEEP_SEC)
    return emb


# ==============================
# Supabase Upsert
# ==============================
def try_uuid(val: Any) -> Optional[str]:
    if val is None: return None
    s = str(val)
    try:
        _ = uuid.UUID(s)
        return s
    except Exception:
        return None

def upsert_enhanced(
    client,
    source_id: Optional[str],
    title: str,
    blob: str,
    ingredients_bi: List[str],
    tags_norm: List[str],
    allergens: List[str],
    embedding: List[float],
):
    payload = {
        "p_source_id": source_id,
        "p_title": title,
        "p_blob": blob,
        "p_ingredients": ingredients_bi,
        "p_tags": tags_norm,
        "p_allergens": allergens,
        "p_embedding": embedding,
    }
    return client.rpc("fn_upsert_recipe_enhanced", payload).execute()


# ==============================
# 보조: existing source_ids 로딩(옵션)
# ==============================
def load_existing_ids(sb_client) -> set[str]:
    ids = set()
    res = sb_client.table("recipes_keto_enhanced").select("source_id").not_.is_("source_id", None).execute()
    for row in (res.data or []):
        sid = row.get("source_id")
        if sid: ids.add(str(sid))
    return ids


# ==============================
# 메인 파이프라인
# ==============================
def process_batch(openai_client: OpenAI, sb_client, offset: int, limit: int, existing_ids: Optional[set] = None) -> int:
    """raw → enhanced 변환/업서트. 처리 개수 반환."""
    q = sb_client.table("recipes_keto_raw").select("*").order("id", desc=False).range(offset, offset + limit - 1)
    res = q.execute()
    rows = res.data or []
    if not rows: return 0

    for i, r in enumerate(rows, 1):
        rid = r.get("id")
        source_uuid = try_uuid(rid)

        if SKIP_EXISTING and source_uuid and existing_ids is not None and source_uuid in existing_ids:
            print(f"- skip existing: offset {offset+i-1} | id={source_uuid}")
            continue

        try:
            blob, meta = llm_enhance_blob(r, openai_client)
            emb = embed_text(openai_client, to_embed_input(blob))  # 라벨 제거본으로 임베딩

            upsert_enhanced(
                sb_client,
                source_uuid,
                meta["title"],
                blob,
                meta["ingredients_bi"],
                meta["tags"],
                meta["allergens"],
                emb,
            )
            if source_uuid and existing_ids is not None:
                existing_ids.add(source_uuid)

            print(f"✓ upsert: offset {offset+i-1} | title={meta['title']}")
        except Exception as e:
            print(f"✗ error at offset {offset+i-1} (id={rid}): {e}")

    return len(rows)

def run_pipeline(total_limit: int = DEFAULT_TOTAL_LIMIT, batch_size: int = DEFAULT_BATCH_SIZE, start_offset: int = DEFAULT_START_OFFSET):
    assert OPENAI_API_KEY and SUPABASE_URL and SUPABASE_KEY, "ENV(OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY/ANON_KEY) 필요"

    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    sb_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    existing_ids = load_existing_ids(sb_client) if SKIP_EXISTING else None

    processed = 0
    offset = start_offset
    while processed < total_limit:
        remain = total_limit - processed
        n = process_batch(openai_client, sb_client, offset, min(batch_size, remain), existing_ids)
        if n == 0:
            break
        offset += n
        processed += n

    print(f"\nDone. processed={processed}, start_offset={start_offset}, total_limit={total_limit}, batch_size={batch_size}, skip_existing={SKIP_EXISTING}")


# ==============================
# CLI
# ==============================
if __name__ == "__main__":
    TOTAL_LIMIT = int(os.getenv("TOTAL_LIMIT", str(DEFAULT_TOTAL_LIMIT)))   # 기본 210
    BS = int(os.getenv("BATCH_SIZE", str(DEFAULT_BATCH_SIZE)))             # 기본 20
    START = int(os.getenv("START_OFFSET", str(DEFAULT_START_OFFSET)))      # 기본 0
    run_pipeline(total_limit=TOTAL_LIMIT, batch_size=BS, start_offset=START)
