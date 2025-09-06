"""
시스템 전체 테스트 스크립트
"""
import logging
import asyncio
import json
from typing import List, Dict, Any

from search_service import SearchService
from config import validate_config

logger = logging.getLogger(__name__)

class SystemTester:
    def __init__(self):
        """테스터 초기화"""
        self.search_service = SearchService()
    
    def test_queries(self, custom_queries: List[str] = None) -> Dict[str, Any]:
        """사용자 정의 질의 또는 기본 3개 질의 테스트"""
        if custom_queries:
            test_queries = [{"query": query, "description": f"'{query}' 검색"} for query in custom_queries]
        else:
            test_queries = [
                {"query": "매운", "description": "매운 음식 검색"},
                {"query": "신선한", "description": "신선한 음식 검색"},
                {"query": "달달한", "description": "달달한 음식 검색"}
            ]
        
        results = {
            "total_tests": len(test_queries),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n🔍 테스트 {i}: {test['description']}")
            print(f"검색어: '{test['query']}'")
            
            try:
                # 검색 수행
                search_results = self.search_service.search(test['query'], top_k=5)
                
                # 결과 검증
                if len(search_results) > 0:
                    print(f"✅ 성공: {len(search_results)}개 결과 반환")
                    results["passed_tests"] += 1
                    
                    # 상위 3개 결과 출력
                    print("📋 검색 결과 (상위 3개):")
                    for j, result in enumerate(search_results[:3], 1):
                        print(f"  {j}. {result['restaurant_name']} - {result['menu_name']}")
                        print(f"     주소: {result['address']}")
                        print(f"     가격: {result['price']:,}원" if result['price'] else "     가격: 미정")
                        print(f"     유사도: {result['score']:.4f}")
                        print()
                    
                    test_result = {
                        "query": test['query'],
                        "status": "passed",
                        "result_count": len(search_results),
                        "top_result": search_results[0] if search_results else None
                    }
                else:
                    print("❌ 실패: 검색 결과 없음")
                    results["failed_tests"] += 1
                    test_result = {
                        "query": test['query'],
                        "status": "failed",
                        "error": "No results returned"
                    }
                
                results["test_results"].append(test_result)
                
            except Exception as e:
                print(f"❌ 실패: 오류 발생 - {e}")
                results["failed_tests"] += 1
                results["test_results"].append({
                    "query": test['query'],
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def test_system_health(self) -> Dict[str, Any]:
        """시스템 전반적인 상태 테스트"""
        print("\n🏥 시스템 헬스체크")
        
        try:
            health = self.search_service.health_check()
            stats = self.search_service.get_search_stats()
            
            print(f"데이터베이스 연결: {'✅' if health['database_connected'] else '❌'}")
            print(f"검색 기능 동작: {'✅' if health['search_working'] else '❌'}")
            print(f"총 메뉴 수: {stats.get('total_menus', 0)}")
            print(f"검색 가능한 메뉴: {stats.get('searchable_menus', 0)}")
            print(f"검색 커버리지: {stats.get('search_coverage', 0):.1f}%")
            
            # 성공 기준 체크
            coverage = stats.get('search_coverage', 0)
            success_criteria_met = coverage >= 95
            
            return {
                "health_status": health['status'],
                "database_connected": health['database_connected'],
                "search_working": health['search_working'],
                "total_menus": stats.get('total_menus', 0),
                "searchable_menus": stats.get('searchable_menus', 0),
                "search_coverage": coverage,
                "success_criteria_met": success_criteria_met
            }
            
        except Exception as e:
            logger.error(f"헬스체크 실패: {e}")
            return {
                "health_status": "error",
                "error": str(e)
            }
    
    def run_full_test(self, custom_queries: List[str] = None) -> Dict[str, Any]:
        """전체 테스트 실행"""
        print("🚀 벡터 검색 시스템 V0 테스트 시작")
        print("=" * 50)
        
        # 1. 시스템 헬스체크
        health_results = self.test_system_health()
        
        # 2. 검색 기능 테스트
        search_results = self.test_queries(custom_queries)
        
        # 3. 전체 결과 정리
        overall_success = (
            health_results.get('success_criteria_met', False) and
            search_results.get('failed_tests', 1) == 0
        )
        
        final_results = {
            "overall_success": overall_success,
            "health_check": health_results,
            "search_tests": search_results,
            "summary": {
                "total_tests": search_results.get('total_tests', 0),
                "passed_tests": search_results.get('passed_tests', 0),
                "failed_tests": search_results.get('failed_tests', 0),
                "embedding_coverage": health_results.get('search_coverage', 0)
            }
        }
        
        # 4. 최종 결과 출력
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        if overall_success:
            print("🎉 전체 테스트 성공!")
            print("✅ PRD 성공 기준(DoD) 달성:")
            print(f"   - 데이터 적재 완료: ✅")
            print(f"   - 임베딩 커버리지 ≥95%: ✅ ({health_results.get('search_coverage', 0):.1f}%)")
            print(f"   - 3개 질의 정상 응답: ✅ ({search_results.get('passed_tests', 0)}/3)")
            print(f"   - 크래시/에러 없이 동작: ✅")
        else:
            print("⚠️ 일부 테스트 실패")
            print("❌ 실패 항목:")
            if health_results.get('search_coverage', 0) < 95:
                print(f"   - 임베딩 커버리지 부족: {health_results.get('search_coverage', 0):.1f}% (목표: 95%)")
            if search_results.get('failed_tests', 0) > 0:
                print(f"   - 검색 테스트 실패: {search_results.get('failed_tests', 0)}개")
        
        return final_results

def get_user_queries():
    """사용자로부터 검색 질의 입력받기"""
    print("\n🔍 검색 테스트 모드 선택:")
    print("1. 기본 테스트 (매운, 신선한, 달달한)")
    print("2. 사용자 정의 검색어")
    
    while True:
        choice = input("\n선택하세요 (1 또는 2): ").strip()
        
        if choice == "1":
            return None  # 기본 테스트
        elif choice == "2":
            queries = []
            print("\n검색어를 입력하세요 (빈 줄 입력 시 종료):")
            
            while True:
                query = input(f"검색어 {len(queries)+1}: ").strip()
                if not query:
                    break
                queries.append(query)
            
            if queries:
                return queries
            else:
                print("❌ 검색어가 입력되지 않았습니다. 기본 테스트로 진행합니다.")
                return None
        else:
            print("❌ 1 또는 2를 입력하세요.")

def interactive_search():
    """대화형 검색 모드"""
    print("\n🔍 대화형 검색 모드")
    print("검색어를 입력하세요 ('quit' 입력 시 종료)")
    
    try:
        tester = SystemTester()
        
        while True:
            query = input("\n검색어: ").strip()
            
            if query.lower() in ['quit', 'exit', '종료']:
                print("👋 검색을 종료합니다.")
                break
            
            if not query:
                print("❌ 검색어를 입력해주세요.")
                continue
            
            print(f"\n🔍 '{query}' 검색 중...")
            try:
                results = tester.search_service.search(query, top_k=5)
                
                if results:
                    print(f"✅ {len(results)}개 결과 발견:")
                    for i, result in enumerate(results, 1):
                        print(f"\n{i}. {result['restaurant_name']} - {result['menu_name']}")
                        print(f"   주소: {result['address']}")
                        print(f"   가격: {result['price']:,}원" if result['price'] else "   가격: 미정")
                        print(f"   카테고리: {result.get('category', '미분류')}")
                        print(f"   유사도: {result['score']:.4f}")
                else:
                    print("❌ 검색 결과가 없습니다.")
                    
            except Exception as e:
                print(f"❌ 검색 중 오류 발생: {e}")
    
    except Exception as e:
        print(f"❌ 대화형 검색 초기화 실패: {e}")

def main():
    """메인 실행 함수"""
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 벡터 검색 시스템 V0 테스트")
    print("=" * 50)
    print("1. 전체 시스템 테스트")
    print("2. 대화형 검색")
    
    while True:
        mode = input("\n모드를 선택하세요 (1 또는 2): ").strip()
        
        if mode == "1":
            # 전체 시스템 테스트
            try:
                validate_config()
                
                # 사용자 질의 입력받기
                custom_queries = get_user_queries()
                
                # 테스터 생성 및 실행
                tester = SystemTester()
                results = tester.run_full_test(custom_queries)
                
                # 결과를 JSON 파일로 저장
                with open('../test_results.json', 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n📄 상세 결과가 test_results.json에 저장되었습니다.")
                
                # 종료 코드 설정
                exit_code = 0 if results['overall_success'] else 1
                exit(exit_code)
                
            except Exception as e:
                print(f"❌ 테스트 실행 중 오류 발생: {e}")
                exit(1)
        
        elif mode == "2":
            # 대화형 검색
            try:
                validate_config()
                interactive_search()
                exit(0)
            except Exception as e:
                print(f"❌ 대화형 검색 실행 중 오류 발생: {e}")
                exit(1)
        
        else:
            print("❌ 1 또는 2를 입력하세요.")

if __name__ == "__main__":
    main()
