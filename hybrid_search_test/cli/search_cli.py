"""
하이브리드 검색 테스트 CLI 도구
"""
import sys
import time
from typing import List, Dict, Any
from ..core.keyword_search import keyword_search_engine
from ..core.vector_search import vector_search_engine
from ..core.hybrid_search import hybrid_search_engine
from ..analysis.comparator import search_comparator
from ..utils.formatter import result_formatter
from ..utils.database import db_manager

class SearchCLI:
    """검색 CLI 도구"""
    
    def __init__(self):
        self.keyword_engine = keyword_search_engine
        self.vector_engine = vector_search_engine
        self.hybrid_engine = hybrid_search_engine
        self.comparator = search_comparator
        self.formatter = result_formatter
        self.db = db_manager
    
    def run(self):
        """CLI 메인 실행"""
        print("🔍 하이브리드 검색 테스트 도구")
        print("=" * 50)
        
        # 데이터베이스 연결 확인
        if not self._check_database_connection():
            return
        
        # 메인 메뉴 루프
        while True:
            self._show_main_menu()
            choice = input("\n선택하세요 (1-7): ").strip()
            
            if choice == '1':
                self._unified_search_test()
            elif choice == '2':
                self._single_search_test()
            elif choice == '3':
                self._comparison_test()
            elif choice == '4':
                self._custom_weight_test()
            elif choice == '5':
                self._database_info()
            elif choice == '6':
                self._sample_queries_test()
            elif choice == '7':
                print("👋 프로그램을 종료합니다.")
                break
            else:
                print("❌ 잘못된 선택입니다. 다시 시도해주세요.")
    
    def _unified_search_test(self):
        """통합 검색 테스트 - 3가지 방식 동시 실행"""
        print(f"\n🔍 통합 검색 테스트 (3가지 방식 동시 실행)")
        print("-" * 50)
        
        query = input("검색어를 입력하세요: ").strip()
        if not query:
            print("❌ 검색어를 입력해주세요.")
            return
        
        top_k = input("결과 수 (기본값: 10): ").strip()
        top_k = int(top_k) if top_k.isdigit() else 10
        
        print(f"\n🔍 '{query}' 통합 검색 실행 중...")
        print("=" * 60)
        
        try:
            # 3가지 검색 방식 동시 실행
            import time
            start_time = time.time()
            
            # 병렬로 검색 실행
            keyword_results = self.keyword_engine.search(query, top_k)
            vector_results = self.vector_engine.search(query, top_k)
            hybrid_results = self.hybrid_engine.search(query, top_k)
            
            total_time = (time.time() - start_time) * 1000
            
            # 결과 표시
            self._display_unified_results(query, keyword_results, vector_results, hybrid_results, total_time)
            
        except Exception as e:
            print(f"❌ 통합 검색 실패: {e}")
    
    def _display_unified_results(self, query: str, keyword_results: list, vector_results: list, hybrid_results: list, total_time: float):
        """통합 검색 결과 표시"""
        print(f"\n📊 '{query}' 검색 결과 (총 {total_time:.1f}ms)")
        print("=" * 80)
        
        # 각 검색 방식별 결과 요약
        search_types = [
            ("🔤 키워드 검색", keyword_results),
            ("🧠 벡터 검색", vector_results), 
            ("⚖️ 하이브리드 검색", hybrid_results)
        ]
        
        for search_name, results in search_types:
            print(f"\n{search_name}:")
            if results:
                top_score = results[0]['similarity_percentage']
                avg_score = sum(r['similarity_percentage'] for r in results) / len(results)
                print(f"  📊 결과 수: {len(results)}개")
                print(f"  🏆 최고 점수: {top_score:.1f}%")
                print(f"  📊 평균 점수: {avg_score:.1f}%")
                
                # 상위 3개 결과 표시
                print(f"  📋 상위 결과:")
                for i, result in enumerate(results[:3], 1):
                    print(f"    {i}. {result['title']} ({result['similarity_percentage']:.1f}%)")
            else:
                print(f"  ❌ 결과 없음")
        
        # 상세 결과 표시 여부
        show_details = input(f"\n상세 결과를 보시겠습니까? (y/n): ").strip().lower()
        if show_details == 'y':
            self._show_detailed_unified_results(keyword_results, vector_results, hybrid_results)
    
    def _show_detailed_unified_results(self, keyword_results: list, vector_results: list, hybrid_results: list):
        """상세 통합 검색 결과 표시"""
        print(f"\n📋 상세 검색 결과")
        print("=" * 80)
        
        # 모든 결과를 하나의 테이블로 표시
        all_results = []
        
        # 각 검색 방식의 결과를 수집
        for i, (search_type, results) in enumerate([
            ("키워드", keyword_results),
            ("벡터", vector_results),
            ("하이브리드", hybrid_results)
        ]):
            for j, result in enumerate(results[:5]):  # 상위 5개만
                all_results.append({
                    'rank': j + 1,
                    'search_type': search_type,
                    'title': result['title'],
                    'score': result['similarity_percentage'],
                    'recipe_id': result['recipe_id']
                })
        
        # 점수 순으로 정렬
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"{'순위':<4} {'검색방식':<8} {'점수':<6} {'제목':<40}")
        print("-" * 80)
        
        for i, result in enumerate(all_results[:15], 1):  # 상위 15개 표시
            title = result['title'][:37] + "..." if len(result['title']) > 40 else result['title']
            print(f"{i:<4} {result['search_type']:<8} {result['score']:<6.1f}% {title:<40}")
    
    def _check_database_connection(self) -> bool:
        """데이터베이스 연결 확인"""
        try:
            info = self.db.get_table_info()
            if 'error' in info:
                print(f"❌ 데이터베이스 연결 실패: {info['error']}")
                return False
            
            total_count = self.db.get_total_count()
            print(f"✅ 데이터베이스 연결 성공")
            print(f"📊 총 레시피 수: {total_count}개")
            return True
            
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False
    
    def _show_main_menu(self):
        """메인 메뉴 표시"""
        print(f"\n📋 메인 메뉴:")
        print("1. 통합 검색 (3가지 방식 동시 실행)")
        print("2. 단일 검색 테스트")
        print("3. 검색 방식 비교 테스트")
        print("4. 사용자 정의 가중치 테스트")
        print("5. 데이터베이스 정보 확인")
        print("6. 샘플 쿼리 테스트")
        print("7. 종료")
    
    def _single_search_test(self):
        """단일 검색 테스트"""
        print(f"\n🔍 단일 검색 테스트")
        print("-" * 30)
        
        query = input("검색어를 입력하세요: ").strip()
        if not query:
            print("❌ 검색어를 입력해주세요.")
            return
        
        search_type = input("검색 방식 (keyword/vector/hybrid): ").strip().lower()
        if search_type not in ['keyword', 'vector', 'hybrid']:
            print("❌ 잘못된 검색 방식입니다.")
            return
        
        top_k = input("결과 수 (기본값: 10): ").strip()
        top_k = int(top_k) if top_k.isdigit() else 10
        
        print(f"\n🔍 '{query}' 검색 중... ({search_type} 방식)")
        
        try:
            if search_type == 'keyword':
                results = self.keyword_engine.search(query, top_k)
            elif search_type == 'vector':
                results = self.vector_engine.search(query, top_k)
            else:  # hybrid
                results = self.hybrid_engine.search(query, top_k)
            
            if results:
                self.formatter.print_search_results(results, search_type, top_k)
            else:
                print("❌ 검색 결과가 없습니다.")
                
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
    
    def _comparison_test(self):
        """검색 방식 비교 테스트"""
        print(f"\n📊 검색 방식 비교 테스트")
        print("-" * 30)
        
        query = input("검색어를 입력하세요: ").strip()
        if not query:
            print("❌ 검색어를 입력해주세요.")
            return
        
        top_k = input("결과 수 (기본값: 10): ").strip()
        top_k = int(top_k) if top_k.isdigit() else 10
        
        print(f"\n🔍 '{query}' 검색 비교 중...")
        
        try:
            comparison = self.comparator.compare_all_search_methods(query, top_k)
            self.comparator.print_comparison_summary(comparison)
            
            # 상세 결과 표시 여부
            show_details = input("\n상세 결과를 보시겠습니까? (y/n): ").strip().lower()
            if show_details == 'y':
                self._show_detailed_results(comparison)
                
        except Exception as e:
            print(f"❌ 비교 테스트 실패: {e}")
    
    def _custom_weight_test(self):
        """사용자 정의 가중치 테스트"""
        print(f"\n⚖️ 사용자 정의 가중치 테스트")
        print("-" * 30)
        
        query = input("검색어를 입력하세요: ").strip()
        if not query:
            print("❌ 검색어를 입력해주세요.")
            return
        
        try:
            vector_weight = float(input("벡터 검색 가중치 (0.0-1.0, 기본값: 0.7): ").strip() or "0.7")
            keyword_weight = float(input("키워드 검색 가중치 (0.0-1.0, 기본값: 0.3): ").strip() or "0.3")
            
            if not (0 <= vector_weight <= 1 and 0 <= keyword_weight <= 1):
                print("❌ 가중치는 0.0-1.0 범위여야 합니다.")
                return
            
            top_k = input("결과 수 (기본값: 10): ").strip()
            top_k = int(top_k) if top_k.isdigit() else 10
            
            print(f"\n🔍 '{query}' 하이브리드 검색 중... (벡터: {vector_weight}, 키워드: {keyword_weight})")
            
            results = self.hybrid_engine.search_with_custom_weights(
                query, top_k, vector_weight, keyword_weight
            )
            
            if results:
                self.formatter.print_search_results(results, 'hybrid', top_k)
            else:
                print("❌ 검색 결과가 없습니다.")
                
        except ValueError:
            print("❌ 잘못된 가중치 값입니다.")
        except Exception as e:
            print(f"❌ 가중치 테스트 실패: {e}")
    
    def _database_info(self):
        """데이터베이스 정보 확인"""
        print(f"\n📊 데이터베이스 정보")
        print("-" * 30)
        
        try:
            # 기본 정보
            info = self.db.get_table_info()
            total_count = self.db.get_total_count()
            
            print(f"테이블명: {info.get('table_name', 'N/A')}")
            print(f"총 레시피 수: {total_count}개")
            print(f"데이터 존재: {'✅' if info.get('has_data') else '❌'}")
            
            # 샘플 데이터
            if info.get('has_data'):
                samples = self.db.get_sample_recipes(3)
                print(f"\n📋 샘플 레시피:")
                for i, sample in enumerate(samples, 1):
                    print(f"  {i}. {sample.get('title', 'N/A')} (ID: {sample.get('recipe_id', 'N/A')})")
            
            # 검색 엔진 통계
            print(f"\n🔍 검색 엔진 통계:")
            for engine_name, engine in [
                ('키워드', self.keyword_engine),
                ('벡터', self.vector_engine),
                ('하이브리드', self.hybrid_engine)
            ]:
                stats = engine.get_search_stats()
                print(f"  {engine_name}: {stats.get('search_method', 'N/A')}")
                
        except Exception as e:
            print(f"❌ 데이터베이스 정보 조회 실패: {e}")
    
    def _sample_queries_test(self):
        """샘플 쿼리 테스트"""
        print(f"\n🧪 샘플 쿼리 테스트")
        print("-" * 30)
        
        sample_queries = [
            "김치찌개",
            "파스타",
            "닭가슴살",
            "디저트",
            "매운 음식",
            "저칼로리",
            "한식",
            "간단한 요리"
        ]
        
        print("샘플 쿼리 목록:")
        for i, query in enumerate(sample_queries, 1):
            print(f"  {i}. {query}")
        
        try:
            choice = input(f"\n테스트할 쿼리 번호 (1-{len(sample_queries)}) 또는 직접 입력: ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(sample_queries):
                query = sample_queries[int(choice) - 1]
            else:
                query = choice
            
            if not query:
                print("❌ 쿼리를 입력해주세요.")
                return
            
            print(f"\n🔍 '{query}' 샘플 테스트 실행 중...")
            
            # 빠른 비교 테스트
            comparison = self.comparator.compare_all_search_methods(query, 5)
            self.comparator.print_comparison_summary(comparison)
            
        except Exception as e:
            print(f"❌ 샘플 쿼리 테스트 실패: {e}")
    
    def _show_detailed_results(self, comparison: Dict[str, Any]):
        """상세 결과 표시"""
        print(f"\n📋 상세 검색 결과")
        print("=" * 60)
        
        for search_type, results in comparison['results'].items():
            print(f"\n{search_type.upper()} 검색 결과:")
            for i, result in enumerate(results[:5], 1):
                print(f"  {i}. {result['title']} ({result['similarity_percentage']:.1f}%)")

def main():
    """CLI 메인 함수"""
    try:
        cli = SearchCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
