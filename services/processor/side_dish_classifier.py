"""
메뉴 사이드/메인 분류기
"""

from dataclasses import dataclass
from typing import List, Optional
import re
import statistics
import unicodedata


@dataclass
class SideClassifyResult:
    is_side: bool
    side_score: int
    main_score: int
    reason: str
    tags: List[str]


class SideDishClassifier:
    # ===== 사전(초안) =====
    SIDE_ADD = ["추가","옵션","토핑","리필","사리","공기밥","추가밥","추가면","추가소스","곱빼기","곱","곁들임",
                "반찬추가","국물추가","계란추가","치즈추가","김가루추가","소스추가","밥추가","면추가","사이드",
                "사이드메뉴","add","extra","+치즈","+밥","+면"]
    SIDE_COOK = ["감자튀김","프렌치프라이","웨지감자","치즈스틱","어니언링","치즈볼","새우튀김","모듬튀김",
                 "닭껍질튀김","콘샐러드","콜슬로","피클","단무지","마늘빵","수프","스프","에피타이저","갈릭브레드",
                 "우동사리","당면사리","라면사리","모밀사리","소면사리","면사리","밥","공깃밥","주먹밥"]
    DRINK = ["아메리카노","라떼","카푸치노","바닐라","콜드브루","샷","콜라","사이다","환타","제로","스프라이트",
             "코크","펩시","맥주","생맥","소주","막걸리","와인","하이볼","사케","청주","진토닉","칵테일","잔","병","피처"]
    DESSERT = ["아이스크림","젤라또","빙수","케이크","치즈케이크","푸딩","티라미수","쿠키","브라우니","마카롱",
               "디저트","팬케이크","펜케이크","팬케익"]
    SIZE_HINT = ["미니","하프","小","half","mini","스몰","S"]
    MAIN_HINT = ["정식","세트","코스","백반","덮밥","비빔밥","찜","찌개","탕","전골","수육","보쌈","볶음","볶음밥",
                 "돈가스","국밥","설렁탕","스테이크","파스타","리조또","피자","버거","샌드위치","플래터",
                 "라멘","소바","우동","초밥","사시미","짜장","짬뽕","탕수육","카레","샤브"]

    # '소/小' 오탐 제거 등
    EXCEPTIONS = [r"소곱창", r"소고기", r"소주", r"소금", r"소스"]

    # ===== 정규식 패턴 =====
    _RE_DONBURI = re.compile(r"(텐|규|가츠|사케|장어|치킨|가이|오야코|부타)동$")
    _RE_OPT_PREFIX = re.compile(r"^\s*\+")
    _RE_OPT_SUFFIX = re.compile(r"(추가|토핑|리필)\s*$")
    _RE_OPT_PARENS = re.compile(r"\((?:[^)]*?)추가(?:[^)]*?)\)$")
    _RE_DRINK_VOL = re.compile(r"\b\d+\s?(?:ml|oz)\b", re.I)
    _RE_COUNT_CUP = re.compile(r"\b\d+\s?잔\b")

    def __init__(self, price_ratio_threshold: float = 0.45, absolute_side_max: int = 9000, industry: Optional[str] = None):
        self.price_ratio_threshold = price_ratio_threshold
        self.absolute_side_max = absolute_side_max
        self.industry = industry  # e.g. 'cafe', 'bar', 'korean', ...

    def _norm(self, s: str) -> str:
        """텍스트 정규화"""
        s = unicodedata.normalize("NFKC", s or "")
        s = re.sub(r"[()\[\]{}]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _hit(self, text: str, words: List[str]) -> List[str]:
        """키워드 매칭"""
        t = text.lower()
        hits = []
        for w in words:
            if w.lower() in t:
                hits.append(w)
        return hits

    def _hits_regex(self, text: str) -> dict:
        """정규표현식 패턴 매칭"""
        try:
            return {
                "donburi": bool(self._RE_DONBURI.search(text)),
                "opt_prefix": bool(self._RE_OPT_PREFIX.search(text)),
                "opt_suffix": bool(self._RE_OPT_SUFFIX.search(text)),
                "opt_parens": bool(self._RE_OPT_PARENS.search(text)),
                "drink_vol": bool(self._RE_DRINK_VOL.search(text)),
                "count_cup": bool(self._RE_COUNT_CUP.search(text)),
            }
        except Exception:
            return {key: False for key in ["donburi", "opt_prefix", "opt_suffix", "opt_parens", "drink_vol", "count_cup"]}

    def classify(
        self,
        name: str,
        description: Optional[str],
        price: Optional[float],
        restaurant_prices: List[Optional[float]],
    ) -> SideClassifyResult:
        """메뉴 사이드/메인 분류"""
        
        # 빠른 실패 조건
        if not name or len(name.strip()) < 2:
            return SideClassifyResult(False, 0, 0, "메뉴명 부족", [])
        
        text = self._norm(f"{name} {(description or '')}")

        # 1) 키워드 매치
        side_hits = self._hit(text, self.SIDE_ADD + self.SIDE_COOK + self.SIZE_HINT + self.DRINK + self.DESSERT)
        main_hits = self._hit(text, self.MAIN_HINT)

        # 1-1) 덮밥류 접미 보정(메인 힌트)
        if self._RE_DONBURI.search(text):
            main_hits.append("~동(덮밥접미)")

        # 2) 예외 제거
        for ex in self.EXCEPTIONS:
            if re.search(ex, text):
                side_hits = [h for h in side_hits if h not in ["소","小","S","스몰"]]

        # 3) 업종 보정: 카페/바는 음료가 메인일 수 있음
        drink_penalty = 0
        drink_only = side_hits and all(h in self.DRINK for h in side_hits)
        if self.industry in ("cafe", "bar"):
            if drink_only:
                main_hits.append("업종보정(음료=메인가능)")
                drink_penalty = 1  # 사이드 점수 1 감점

        # 4) 가격 분포(65 분위 참조 → 메인가격대 방어)
        nums = [p for p in restaurant_prices if isinstance(p, (int, float))]
        median = statistics.median(nums) if nums else None
        q65 = None
        if nums and len(nums) >= 3:
            try:
                q65 = statistics.quantiles(nums, n=20)[12]  # ~65% 분위
            except Exception:
                q65 = median
        else:
            q65 = median

        ratio_flag = False
        abs_flag = False
        if isinstance(price, (int, float)):
            base_ref = q65 or median
            if base_ref and price <= base_ref * self.price_ratio_threshold:
                ratio_flag = True
            # 업종별 절대 컷 상향(카페/바)
            abs_cut = self.absolute_side_max if self.industry not in ("cafe","bar") else int(self.absolute_side_max * 1.3)
            if price <= abs_cut:
                abs_flag = True

        # 5) 패턴 보너스(옵션/용량/잔수)
        re_hits = self._hits_regex(text)
        pattern_side_bonus = any([re_hits["opt_prefix"], re_hits["opt_suffix"], re_hits["opt_parens"],
                                  re_hits["drink_vol"], re_hits["count_cup"]])

        # 6) 길이/토큰 보조(사이드 힌트가 있을 때만)
        tokens = text.split()
        short_flag = (len(tokens) <= 1) and bool(side_hits or pattern_side_bonus)

        # ===== 스코어 =====
        side_score = 0
        if side_hits: side_score += 1
        if ratio_flag: side_score += 1
        if abs_flag and side_hits: side_score += 1
        if pattern_side_bonus: side_score += 1
        if short_flag: side_score += 1
        side_score -= drink_penalty

        main_score = len(main_hits)

        # ===== 결정 =====
        is_side = (side_score >= 1) and (main_score == 0)

        reason = (
            f"side_hits={side_hits}, main_hits={main_hits}, price={price}, "
            f"median={median}, q65={q65}, ratio={ratio_flag}, abs={abs_flag}, "
            f"patterns={re_hits}, short={short_flag}, industry={self.industry}, "
            f"side_score={side_score}, main_score={main_score}"
        )
        tags = list(dict.fromkeys(side_hits + main_hits))
        return SideClassifyResult(is_side=is_side, side_score=side_score, main_score=main_score, reason=reason, tags=tags)
