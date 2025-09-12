크롤링 → 풍부화 → 임베딩 → 검색 (하이브리드 필터링) — 운영 가이드

요약: 키워드(정규화 ID) + 벡터 안전망을 결합해 알러지/비선호를 안전하게 필터링하고, keto_score를 중심으로 가중 정렬합니다. 저장소는 Postgres + pgvector 단일 구성을 권장합니다.

0. 골자(추천)

크롤링 → 정규화/중복제거 → 풍부화(증강) → DB 저장 → '선별된 텍스트만' 임베딩 → (동일 Postgres) pgvector 인덱싱 → 검색 시 하드필터(알러지/비선호) + 벡터 안전망 → 랭킹

0.5 크롤링 세부 단계

Seed URL 생성: 키워드/지역/카테고리 기반 URL 패턴 생성
목록 페이지 크롤링: 페이지네이션 처리, 동적 로딩 대응
상세 페이지 크롤링: 메뉴/리뷰/이미지 수집
데이터 검증 및 정제: 필수 필드 체크, 형식 검증
중복 제거: 실시간/배치 중복 탐지 및 병합

1. 정규화/중복제거 분리·명시

Idempotent upsert: 소스별 source, source_url 기준.

Canonical key: (name_norm, addr_norm) + 보조키(전화/좌표 반경).

중복 병합 규칙: source_trust_rank 우선(신뢰도 높은 소스가 승리).

1.5 에러 처리 및 복구 전략

크롤링 실패 시 재시도 로직:
- HTTP 403/429: 지수 백오프(10s → 5m), QPS 절반으로 감속
- HTTP 5xx: 3회 재시도, 타임아웃 증가(8s → 12s)
- 파싱 실패: 대체 셀렉터 시도, 실패 시 스킵+로그

부분 실패 시 데이터 보존:
- 성공한 필드는 저장, 실패한 필드는 NULL 처리
- 재시도 큐에 실패 URL 등록
- 배치 완료 후 실패 건 재처리

네트워크 장애 시 백오프:
- 연결 실패 시 1m → 5m → 15m 단계적 대기
- 프록시 풀 로테이션으로 IP 차단 회피
- User-Agent 로테이션으로 차단 위험 감소

2. 풍부화는 '근거-태깅형'으로

생성/추론 경로를 출처 라벨로 기록:
menu_enriched.source ∈ {'raw','rule','llm','embed'}.

핵심 필드는 ID 매핑 테이블에 저장:
menu_ingredients(menu_id, ingredient_id, source, confidence)
(예: main_ingredients, allergens 등)

2.5 데이터 품질 검증

필수 필드 완성도 체크:
- 식당: name, lat, lng, category (필수)
- 메뉴: menu_name, price|range (선택적)
- 풍부화: short_desc, main_ingredients (권장)

데이터 타입 및 형식 검증:
- 좌표: lat(-90~90), lng(-180~180) 범위 체크
- 전화번호: 정규식 패턴 검증
- 가격: 숫자형 변환 및 이상치 탐지
- URL: 형식 검증 및 접근 가능성 체크

이상치 탐지 및 처리:
- 가격: 상위/하위 1% 제거 또는 플래그
- 좌표: 서울시 경계 외부 좌표 검증
- 텍스트: 길이 제한 및 특수문자 정제

품질 점수 기반 필터링:
- 완성도 점수: 필수 필드 기반 0~100점
- 신뢰도 점수: 소스별 가중치 반영
- 최종 품질 점수 ≥ 70점만 저장

3. 임베딩은 “필요 최소 텍스트”만

임베딩 대상(권장)

menu_search_text = menu_name
                  + short_desc
                  + main_ingredients(동의어 확장)
                  + cooking_method
                  + dietary_tags
                  + spice/meal_time(텍스트화)


(선택) ingredient_embeddings: 표준 재료/알레르겐 대표 벡터(자유문장 매핑·안전망 보조)

임베딩 비대상

raw 스냅샷 전체, 리뷰 전문(법/변동성), 주소/전화/가격(변동·탐색 비기여).

4. 저장소는 한 곳(Postgres + pgvector)

이중 저장소 지양(이중쓰기·정합성 리스크).

테이블 예시:
menu_embeddings(menu_id, model, dim, embedding vector, content_hash, updated_at)
→ pgvector HNSW(또는 IVFFlat) 인덱스 생성.

5. 재임베딩 정책(필수)

content_hash(menu_search_text) 보관 → 변경 시에만 재임베딩.

트리거/잡: menu_enriched 갱신 → 해시 비교 → 변경 시 menu_embeddings 업데이트 큐에 적재.

모델/버전 메타: model='text-embedding-3-small', algo_ver='RAG-v1.2' 등 기록.

6. 검색 파이프라인(런타임)
6.1 하드필터(키워드/ID 기반)

조인으로 즉시 제외:
menu_ingredients ⨝ (user_allergens ∪ user_dislikes)

6.2 벡터 안전망(누락 최소화, 하이브리드)

대상:
(a) menu_ingredients 비어있음, 또는
(b) confidence 낮은 매핑 포함 메뉴 부분 집합만.

규칙:
cos(menu_embedding, allergen/avoid_embedding_of_user) ≥ τ (보수적 권장값: 0.86) 이면 의심/제외 + 로그 적재.

목적: 키워드 매핑 누락 보완(전수 벡터 필터링은 금지).

6.3 1차 후보 생성(탐색)

pgvector로 menu_embeddings TopK(예: 50~100) 검색.

6.4 소프트 가중치(부스팅)

선호 태그/조리법/맛 등 가중치 합산(preference_boost) — 하드필터와 별개.

6.5 최종 정렬

keto_score 1순위 → 동점/근접 시 preference_boost → 거리/평판 보정.

(선택) 하이브리드 재정렬: BM25(or trigram) 0.3 + 벡터 0.7.

7. 운영/성능 가드레일

pgvector 인덱스: HNSW 권장(대화형). ef_search는 목표 응답시간에 맞춰 튜닝.

인덱스 구성:
menu_embeddings.menu_id UNIQUE, embedding 벡터 인덱스
(필요 시 WHERE is_active 파셜 인덱스).

스케일아웃: 임베딩/재임베딩은 큐(Celery 등) 로 비동기 처리(배치/우선순위 관리).

7.5 모니터링 및 로깅 시스템

크롤링 성공률 실시간 모니터링:
- 사이트별 성공/실패율 대시보드
- 시간대별 성능 트렌드 그래프
- 실패 원인별 분류 및 알림

임베딩 처리 시간 추적:
- 배치별 처리 시간 메트릭
- 모델별 성능 비교
- 큐 적체 상황 모니터링

검색 성능 메트릭 수집:
- 응답 시간 P50/P95/P99
- 검색 정확도 A/B 테스트
- 사용자 클릭률 및 피드백

8.5 보안 및 개인정보 보호

크롤링 보안:
- IP 로테이션: 프록시 풀 자동 순환
- User-Agent 다양화: 브라우저 시뮬레이션
- robots.txt 준수: 자동 검증 및 준수
- Rate Limiting: 사이트별 QPS 제한


8. 품질/안전 체크리스트

알레르기 유실 방지: 오프라인 매핑 실패·저신뢰 메뉴만 벡터 안전망(τ↑) 재확인.

설명가능성: 추천 카드에 근거 노출
(예: "Keto 82(순탄수 6g) · 선호 '아보카도' +0.2 · 알레르기 매칭 없음/의심(마요 0.88)")

TTL/갱신: valid_until(14일) 만료 시 재수집 → 재풍부화 → 재임베딩 일괄 수행(파이프라인 통합).

사전 보강 루프: 안전망 의심 로그 상위 표현을 ingredient_aliases에 편입해 키워드 정밀도 지속 향상.