# 재사용 가능한 크롤링 시스템 설계 가이드

## 1. 기본 개념 (초보자용)

### 왜 데이터를 재사용해야 할까요?
- **시간 절약**: 매번 크롤링하지 않고 저장된 데이터 활용
- **비용 절약**: API 호출 횟수 줄임 (지오코딩 등)
- **안정성**: 웹사이트 차단 위험 감소
- **개발 효율성**: 테스트할 때마다 크롤링할 필요 없음

### 데이터 저장 전략
```
크롤링 → 원본 데이터 저장 → 정제/가공 → 최종 DB 저장
   ↓            ↓               ↓            ↓
웹사이트    JSON/CSV 파일    Python 처리   PostgreSQL
```

## 2. 데이터 저장 구조

### 2.1 폴더 구조
```
final_ETL/
├── data/
│   ├── raw/              # 원본 크롤링 데이터
│   │   ├── 2024-01-15_diningcode_raw.json
│   │   └── 2024-01-16_diningcode_raw.json
│   ├── processed/        # 정제된 데이터
│   │   ├── 2024-01-15_restaurants.csv
│   │   └── 2024-01-15_menus.csv
│   └── cache/           # 중간 캐시 데이터
│       └── geocoding_cache.json
├── scripts/
│   ├── crawl_diningcode.py
│   ├── process_data.py
│   └── load_to_db.py
└── config/
    └── settings.json
```

### 2.2 데이터 저장 방식

#### A) 원본 데이터 저장 (JSON)
```json
{
  "crawl_date": "2024-01-15T10:30:00",
  "source": "diningcode",
  "restaurants": [
    {
      "source_url": "https://www.diningcode.com/profile.php?rid=123",
      "name_raw": "강남 맛집",
      "addr_raw": "서울시 강남구 테헤란로 123",
      "phone_raw": "02-1234-5678",
      "menus_raw": [
        {"name": "김치찌개", "price": "8000원"},
        {"name": "된장찌개", "price": "7000원"}
      ],
      "crawl_timestamp": "2024-01-15T10:31:15"
    }
  ]
}
```

#### B) 캐시 데이터 (지오코딩)
```json
{
  "geocoding_cache": {
    "서울시 강남구 테헤란로 123": {
      "addr_norm": "서울 강남구 테헤란로 123",
      "lat": 37.4979,
      "lng": 127.0276,
      "cached_at": "2024-01-15T10:32:00"
    }
  }
}
```

## 3. 재사용 로직 구현

### 3.1 데이터 확인 함수
```python
import os
import json
from datetime import datetime, timedelta

def check_existing_data(source_name, max_age_days=7):
    """
    기존 데이터가 있는지 확인하고 사용 가능한지 판단

    Args:
        source_name: 'diningcode' 등
        max_age_days: 데이터 유효 기간 (일)

    Returns:
        dict: {'exists': bool, 'file_path': str, 'age_days': int}
    """
    data_dir = "data/raw"
    today = datetime.now().strftime("%Y-%m-%d")

    # 최근 파일들 확인
    for i in range(max_age_days + 1):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        file_path = f"{data_dir}/{check_date}_{source_name}_raw.json"

        if os.path.exists(file_path):
            return {
                'exists': True,
                'file_path': file_path,
                'age_days': i
            }

    return {'exists': False, 'file_path': None, 'age_days': None}

# 사용 예시
existing = check_existing_data('diningcode', max_age_days=3)
if existing['exists']:
    print(f"기존 데이터 발견: {existing['file_path']} (생성된지 {existing['age_days']}일)")
else:
    print("새로 크롤링 필요")
```

### 3.2 스마트 크롤링 함수
```python
def smart_crawl(force_new=False, max_age_days=3):
    """
    기존 데이터 확인 후 필요시에만 크롤링

    Args:
        force_new: True면 무조건 새로 크롤링
        max_age_days: 데이터 유효 기간
    """

    if not force_new:
        existing = check_existing_data('diningcode', max_age_days)

        if existing['exists']:
            print(f"✅ 기존 데이터 사용: {existing['file_path']}")
            return load_existing_data(existing['file_path'])

    print("🕷️ 새로운 크롤링 시작...")
    new_data = crawl_diningcode()  # 실제 크롤링 함수
    save_raw_data(new_data)       # 원본 데이터 저장
    return new_data

def load_existing_data(file_path):
    """기존 데이터 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_raw_data(data):
    """원본 데이터 저장"""
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = f"data/raw/{today}_diningcode_raw.json"

    os.makedirs("data/raw", exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 원본 데이터 저장: {file_path}")
```

### 3.3 지오코딩 캐시 시스템
```python
def load_geocoding_cache():
    """지오코딩 캐시 로드"""
    cache_file = "data/cache/geocoding_cache.json"

    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {"geocoding_cache": {}}

def save_geocoding_cache(cache):
    """지오코딩 캐시 저장"""
    cache_file = "data/cache/geocoding_cache.json"
    os.makedirs("data/cache", exist_ok=True)

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def geocode_with_cache(address):
    """캐시를 활용한 지오코딩"""
    cache = load_geocoding_cache()

    # 캐시에 있는지 확인
    if address in cache["geocoding_cache"]:
        print(f"💾 캐시에서 주소 로드: {address}")
        return cache["geocoding_cache"][address]

    # 없으면 API 호출
    print(f"🌐 API 호출: {address}")
    result = call_kakao_geocoding_api(address)  # 실제 API 호출

    # 캐시에 저장
    cache["geocoding_cache"][address] = {
        **result,
        "cached_at": datetime.now().isoformat()
    }
    save_geocoding_cache(cache)

    return result
```

## 4. 실제 사용 예시

### 4.1 메인 스크립트 (main.py)
```python
#!/usr/bin/env python3
"""
재사용 가능한 크롤링 시스템 메인 스크립트
"""

import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='재사용 가능한 크롤링 시스템')
    parser.add_argument('--force-new', action='store_true',
                       help='기존 데이터 무시하고 새로 크롤링')
    parser.add_argument('--max-age', type=int, default=3,
                       help='데이터 유효 기간 (일, 기본값: 3)')
    parser.add_argument('--no-geocoding', action='store_true',
                       help='지오코딩 건너뛰기 (테스트용)')

    args = parser.parse_args()

    print("🚀 재사용 가능한 크롤링 시스템 시작")
    print(f"📅 실행 시간: {datetime.now()}")

    # 1. 스마트 크롤링 (필요시에만)
    raw_data = smart_crawl(
        force_new=args.force_new,
        max_age_days=args.max_age
    )

    # 2. 데이터 정제 (지오코딩 캐시 활용)
    processed_data = process_restaurants(
        raw_data,
        use_geocoding=not args.no_geocoding
    )

    # 3. CSV 저장
    save_to_csv(processed_data)

    # 4. DB 적재 (선택적)
    if input("DB에 적재하시겠습니까? (y/N): ").lower() == 'y':
        load_to_database(processed_data)

    print("✅ 완료!")

if __name__ == "__main__":
    main()
```

### 4.2 사용법
```bash
# 기본 사용 (3일 이내 데이터 있으면 재사용)
python main.py

# 무조건 새로 크롤링
python main.py --force-new

# 7일 이내 데이터까지 재사용
python main.py --max-age 7

# 지오코딩 없이 테스트
python main.py --no-geocoding
```

## 5. 초보자를 위한 팁

### 5.1 단계별 구현 순서
1. **1단계**: 원본 데이터 JSON 저장만 구현
2. **2단계**: 기존 파일 확인 로직 추가
3. **3단계**: 지오코딩 캐시 시스템 추가
4. **4단계**: 명령행 옵션 추가

### 5.2 디버깅 팁
```python
# 로그 추가
import logging

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

def smart_crawl_with_logs(force_new=False, max_age_days=3):
    logger = logging.getLogger(__name__)

    logger.info(f"크롤링 시작 - force_new: {force_new}, max_age: {max_age_days}")

    if not force_new:
        existing = check_existing_data('diningcode', max_age_days)
        logger.info(f"기존 데이터 확인 결과: {existing}")

        if existing['exists']:
            logger.info(f"기존 데이터 사용: {existing['file_path']}")
            return load_existing_data(existing['file_path'])

    logger.info("새로운 크롤링 시작")
    # ... 나머지 로직
```

### 5.3 에러 처리
```python
def safe_crawl():
    """안전한 크롤링 (에러 처리 포함)"""
    try:
        return smart_crawl()
    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")

        # 백업 데이터 찾기
        backup = check_existing_data('diningcode', max_age_days=30)
        if backup['exists']:
            print(f"🔄 백업 데이터 사용: {backup['file_path']}")
            return load_existing_data(backup['file_path'])

        raise Exception("크롤링 실패 및 백업 데이터 없음")
```

## 6. 다음 단계

이 시스템을 구현한 후:
1. **모니터링**: 데이터 품질 체크
2. **자동화**: 스케줄러로 정기 업데이트
3. **확장**: 다른 소스 추가 (식신 등)
4. **최적화**: 중복 제거 로직 개선

이렇게 하면 한 번 크롤링한 데이터를 효율적으로 재사용할 수 있습니다!