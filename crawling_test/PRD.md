# 강남역 음식점 메뉴 크롤링 시스템 PRD

## 1. 제품 개요
사용자가 입력한 강남역 주변 음식점명을 기반으로 '식신' 사이트에서 메뉴 정보를 자동 수집하여 로컬 데이터베이스에 저장하는 웹 기반 크롤링 시스템

## 2. 핵심 기능

### 2.1 프론트엔드 인터페이스
- **UI**: 반응형 HTML/CSS/JavaScript 웹 인터페이스
- **기능**: 식당명 입력 폼, 검색 버튼, 실시간 결과 표시
- **사용성**: 직관적이고 단순한 사용자 경험
- **결과 표시**: 크롤링 결과를 구조화된 형태로 실시간 표시
- **JSON 미리보기**: 수집된 데이터의 JSON 구조 확인 가능

### 2.2 음식점 검색 및 크롤링
- **입력**: 사용자가 음식점명 직접 입력
- **처리**: '식신' 사이트 자동 검색 및 상세 페이지 접근
- **기술**: Requests + BeautifulSoup4 기반 정확한 CSS 셀렉터 활용
- **안정성**: HTML 구조 분석을 통한 정확한 데이터 추출

### 2.3 데이터 수집 및 저장
- **수집 데이터**: 
  - 식당명 (정확한 공식 명칭)
  - 도로명 주소 및 지번 주소 (분리 저장)
  - 메뉴명 및 가격 정보 (숫자 형태로 저장)
- **임시 저장**: 구조화된 JSON 형태로 처리
- **최종 저장**: SQLite 로컬 DB에 관계형으로 저장

### 2.4 데이터 전처리 및 정규화
- **메뉴명 정규화**: 불필요한 특수문자 및 공백 제거
- **가격 추출**: "12,000 원" → 12000 (숫자 형태로 변환)
- **주소 분리**: 도로명 주소와 지번 주소 개별 추출
- **데이터 정제**: 일관된 형태로 데이터 표준화

## 3. 기술 요구사항

### 3.1 크롤링 정책 및 안정성
- **속도 제한**: 요청 간 2-3초 지연으로 서버 부담 최소화
- **안정성**: 봇 차단 방지를 위한 User-Agent 헤더 설정
- **오류 처리**: 네트워크 오류 및 페이지 구조 변경에 대한 예외 처리
- **타임아웃**: 10초 타임아웃으로 무한 대기 방지

### 3.2 데이터베이스 설계
- **타입**: SQLite (로컬 파일 기반)
- **테이블 구조**:
  - `restaurants`: 식당 기본 정보 (id, name, address, created_at)
  - `menus`: 메뉴 정보 (id, restaurant_id, menu_name, price, created_at)
- **관계**: 1:N 관계 (하나의 식당에 여러 메뉴)
- **인덱싱**: 검색 성능 최적화

### 3.3 개발 환경 및 기술 스택
- **OS**: Windows 10/11 환경
- **Shell**: PowerShell 스크립트 지원
- **백엔드**: Python Flask 웹 서버
- **프론트엔드**: HTML5, CSS3, Vanilla JavaScript
- **크롤링**: Requests + BeautifulSoup4
- **데이터베이스**: SQLite3
- **패키지 관리**: pip + requirements.txt

## 4. 데이터 플로우 및 처리 과정
```
사용자 입력 → Flask API 호출 → 식신 사이트 검색 → 
CSS 셀렉터 기반 데이터 추출 → JSON 구조화 → 
데이터 정규화 → SQLite 저장 → 웹 UI 결과 표시
```

### 4.1 상세 처리 단계
1. **사용자 입력**: 웹 인터페이스를 통한 식당명 입력
2. **검색 요청**: 식신 사이트 검색 페이지 접근
3. **링크 추출**: 첫 번째 검색 결과의 상세 페이지 URL 추출
4. **상세 정보 크롤링**: 
   - `h1` 태그에서 식당명 추출
   - `span.address-text`에서 도로명 주소 추출
   - `div.address-info`에서 지번 주소 추출
   - `li.menu-list`에서 메뉴명과 가격 추출
5. **데이터 정제**: 정규식을 통한 불필요한 문자 제거
6. **DB 저장**: 관계형 구조로 SQLite에 저장
7. **결과 반환**: JSON 형태로 클라이언트에 응답

## 5. 데이터 구조 명세

### 5.1 JSON 출력 형식
```json
{
  "restaurant_name": "강남교자",
  "address": {
    "road_address": "서울특별시 서초구 강남대로69길 11",
    "jibun_address": "서울특별시 서초구 서초동 1308-1"
  },
  "menu": [
    {
      "name": "교자만두",
      "price": 12000
    },
    {
      "name": "칼국수",
      "price": 11000
    }
  ]
}
```

### 5.2 데이터베이스 스키마
```sql
-- 식당 테이블
CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 메뉴 테이블  
CREATE TABLE menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER,
    menu_name TEXT NOT NULL,
    price INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
);
```

## 6. 프로젝트 구조 및 파일 구성
```
crawling_test/
├── index.html              # 프론트엔드 웹 인터페이스
├── server.py               # Flask 백엔드 서버 및 크롤링 로직
├── requirements.txt        # Python 패키지 의존성
├── start_server.ps1        # PowerShell 실행 스크립트
├── restaurant_menu.db      # SQLite 데이터베이스 (자동 생성)
├── PRD.md                  # 제품 요구사항 문서 (본 문서)
└── README.md              # 프로젝트 설명서 및 사용 가이드
```

## 7. 실행 방법 및 사용법

### 7.1 시스템 요구사항
- Windows 10/11
- Python 3.7 이상
- PowerShell 실행 권한

### 7.2 실행 단계
1. **PowerShell 실행**: `.\start_server.ps1`
2. **브라우저 접속**: `http://localhost:5000`
3. **식당명 입력**: 검색하고 싶은 식당명 입력
4. **결과 확인**: 크롤링된 데이터 및 JSON 구조 확인

### 7.3 주요 기능 사용법
- **메뉴 검색**: "강남교자", "도치피자" 등 식당명 입력
- **결과 확인**: 식당 정보, 주소, 메뉴 목록 및 가격 표시
- **JSON 데이터**: 하단에 구조화된 JSON 데이터 표시
- **데이터베이스**: SQLite 파일에 자동 저장

## 8. 성공 기준 및 품질 지표
- **정확성**: 입력한 음식점명으로 정확한 메뉴 및 가격 정보 수집 (95% 이상)
- **안정성**: 서버 차단 없이 안정적인 크롤링 수행 (연속 10회 성공)
- **완성도**: 식당명, 주소(도로명/지번), 메뉴명, 가격 모든 데이터 수집
- **사용성**: 직관적인 웹 인터페이스를 통한 쉬운 사용 (클릭 3회 이내)
- **성능**: 평균 5-8초 내 결과 반환
- **저장 완료**: 정제된 데이터의 SQLite 저장 및 관계형 구조 유지

## 9. 향후 확장 계획
- **다중 사이트 지원**: 다른 맛집 사이트 크롤링 추가
- **검색 필터**: 지역별, 가격대별 검색 기능
- **데이터 분석**: 가격 통계 및 인기 메뉴 분석
- **API 제공**: RESTful API를 통한 외부 연동
- **배치 처리**: 대량 식당 데이터 일괄 수집
