"""
🏭 파서 팩토리
- 사이트별 파서 인스턴스 생성
- 플러그인 아키텍처 지원
- 파서 등록 및 관리
"""

from typing import Dict, Type, Optional, List
from abc import ABC

from .base_parser import BaseParser
from .siksin_parser import SiksinParser
from ..utils.config_loader import get_config
from ..utils.logger import get_logger
from ..utils.http_client import HttpClient


class ParserRegistry:
    """파서 등록 레지스트리"""
    
    def __init__(self):
        self._parsers: Dict[str, Type[BaseParser]] = {}
        self._instances: Dict[str, BaseParser] = {}
        self.logger = get_logger("parser_factory")
        
        # 기본 파서들 등록
        self.register_default_parsers()
    
    def register_default_parsers(self):
        """기본 파서들 등록"""
        self.register("siksin", SiksinParser)
        # 향후 추가 파서들
        # self.register("diningcode", DiningcodeParser)
        # self.register("mangoplate", MangoplateParser)
    
    def register(self, site: str, parser_class: Type[BaseParser]):
        """파서 클래스 등록"""
        if not issubclass(parser_class, BaseParser):
            raise ValueError(f"파서 클래스는 BaseParser를 상속해야 합니다: {parser_class}")
        
        self._parsers[site] = parser_class
        self.logger.info(f"파서 등록: {site} -> {parser_class.__name__}")
    
    def unregister(self, site: str):
        """파서 등록 해제"""
        if site in self._parsers:
            del self._parsers[site]
            
        if site in self._instances:
            del self._instances[site]
            
        self.logger.info(f"파서 등록 해제: {site}")
    
    def get_parser_class(self, site: str) -> Optional[Type[BaseParser]]:
        """파서 클래스 반환"""
        return self._parsers.get(site)
    
    def create_parser(self, site: str, http_client: Optional[HttpClient] = None) -> Optional[BaseParser]:
        """파서 인스턴스 생성"""
        parser_class = self._parsers.get(site)
        if not parser_class:
            self.logger.error(f"등록되지 않은 사이트: {site}")
            return None
        
        try:
            # 파서 인스턴스 생성
            if hasattr(parser_class, '__init__'):
                # http_client 매개변수 지원 여부 확인
                import inspect
                sig = inspect.signature(parser_class.__init__)
                if 'http_client' in sig.parameters:
                    parser = parser_class(http_client=http_client)
                else:
                    parser = parser_class()
            else:
                parser = parser_class()
            
            self.logger.info(f"파서 생성: {site} -> {parser.__class__.__name__}")
            return parser
            
        except Exception as e:
            self.logger.error(f"파서 생성 실패: {site} - {e}")
            return None
    
    def get_or_create_parser(self, site: str, http_client: Optional[HttpClient] = None) -> Optional[BaseParser]:
        """파서 인스턴스 반환 (캐시됨)"""
        # 이미 생성된 인스턴스가 있으면 반환
        if site in self._instances:
            parser = self._instances[site]
            # HTTP 클라이언트 업데이트
            if http_client and hasattr(parser, 'http_client'):
                parser.http_client = http_client
            return parser
        
        # 새 인스턴스 생성
        parser = self.create_parser(site, http_client)
        if parser:
            self._instances[site] = parser
        
        return parser
    
    def get_supported_sites(self) -> List[str]:
        """지원되는 사이트 목록"""
        return list(self._parsers.keys())
    
    def is_supported(self, site: str) -> bool:
        """사이트 지원 여부"""
        return site in self._parsers
    
    def get_parser_info(self, site: str) -> Optional[Dict[str, any]]:
        """파서 정보 반환"""
        if site not in self._parsers:
            return None
        
        parser_class = self._parsers[site]
        
        # 임시 인스턴스 생성해서 정보 추출
        try:
            temp_parser = self.create_parser(site)
            if temp_parser and hasattr(temp_parser, 'get_site_info'):
                info = temp_parser.get_site_info()
            else:
                info = {}
            
            return {
                'site': site,
                'class_name': parser_class.__name__,
                'module': parser_class.__module__,
                'supported': True,
                **info
            }
            
        except Exception as e:
            return {
                'site': site,
                'class_name': parser_class.__name__,
                'module': parser_class.__module__,
                'supported': False,
                'error': str(e)
            }
    
    def get_all_parser_info(self) -> Dict[str, Dict[str, any]]:
        """모든 파서 정보 반환"""
        info = {}
        for site in self._parsers.keys():
            info[site] = self.get_parser_info(site)
        return info
    
    def clear_instances(self):
        """모든 파서 인스턴스 캐시 제거"""
        self._instances.clear()
        self.logger.info("파서 인스턴스 캐시 제거")


class ParserFactory:
    """파서 팩토리 - 싱글톤 패턴"""
    
    _instance = None
    _registry = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._registry = ParserRegistry()
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config = get_config()
            self.logger = get_logger("parser_factory")
            self.initialized = True
    
    def create_parser(self, site: str, http_client: Optional[HttpClient] = None) -> Optional[BaseParser]:
        """파서 생성"""
        return self._registry.create_parser(site, http_client)
    
    def get_parser(self, site: str, http_client: Optional[HttpClient] = None) -> Optional[BaseParser]:
        """파서 반환 (캐시됨)"""
        return self._registry.get_or_create_parser(site, http_client)
    
    def register_parser(self, site: str, parser_class: Type[BaseParser]):
        """파서 등록"""
        self._registry.register(site, parser_class)
    
    def unregister_parser(self, site: str):
        """파서 등록 해제"""
        self._registry.unregister(site)
    
    def get_supported_sites(self) -> List[str]:
        """지원되는 사이트 목록"""
        return self._registry.get_supported_sites()
    
    def is_supported(self, site: str) -> bool:
        """사이트 지원 여부"""
        return self._registry.is_supported(site)
    
    def get_parser_info(self, site: str = None) -> Dict[str, any]:
        """파서 정보 반환"""
        if site:
            return self._registry.get_parser_info(site)
        else:
            return self._registry.get_all_parser_info()
    
    def validate_site_config(self, site: str) -> Dict[str, any]:
        """사이트 설정 검증"""
        validation_result = {
            'site': site,
            'parser_available': False,
            'config_available': False,
            'config_valid': False,
            'errors': [],
            'warnings': []
        }
        
        # 파서 등록 여부 확인
        if self.is_supported(site):
            validation_result['parser_available'] = True
        else:
            validation_result['errors'].append(f"파서가 등록되지 않음: {site}")
            return validation_result
        
        # 설정 파일 존재 여부 확인
        try:
            parser_config = self.config.get_parser_config(site)
            validation_result['config_available'] = True
            
            # 필수 설정 확인
            required_sections = ['site', 'search', 'restaurant_detail']
            for section in required_sections:
                if section not in parser_config:
                    validation_result['errors'].append(f"필수 설정 섹션 누락: {section}")
            
            # 필수 필드 확인
            site_config = parser_config.get('site', {})
            required_site_fields = ['name', 'base_url']
            for field in required_site_fields:
                if field not in site_config:
                    validation_result['errors'].append(f"필수 사이트 설정 누락: {field}")
            
            # 검색 설정 확인
            search_config = parser_config.get('search', {})
            if 'selectors' not in search_config:
                validation_result['warnings'].append("검색 셀렉터 설정 누락")
            
            # 상세 설정 확인
            detail_config = parser_config.get('restaurant_detail', {})
            if 'selectors' not in detail_config:
                validation_result['warnings'].append("상세 셀렉터 설정 누락")
            
            # 에러가 없으면 유효한 설정
            if not validation_result['errors']:
                validation_result['config_valid'] = True
            
        except Exception as e:
            validation_result['errors'].append(f"설정 로드 실패: {str(e)}")
        
        return validation_result
    
    def health_check(self) -> Dict[str, any]:
        """팩토리 상태 확인"""
        supported_sites = self.get_supported_sites()
        health_status = {
            'factory_status': 'healthy',
            'supported_sites_count': len(supported_sites),
            'supported_sites': supported_sites,
            'site_validations': {}
        }
        
        # 각 사이트별 설정 검증
        for site in supported_sites:
            validation = self.validate_site_config(site)
            health_status['site_validations'][site] = validation
            
            # 전체 상태에 반영
            if validation['errors']:
                health_status['factory_status'] = 'degraded'
        
        return health_status


# 전역 팩토리 인스턴스
_parser_factory = None


def get_parser_factory() -> ParserFactory:
    """파서 팩토리 싱글톤 반환"""
    global _parser_factory
    if _parser_factory is None:
        _parser_factory = ParserFactory()
    return _parser_factory


def create_parser(site: str, http_client: Optional[HttpClient] = None) -> Optional[BaseParser]:
    """파서 생성 (편의 함수)"""
    factory = get_parser_factory()
    return factory.create_parser(site, http_client)


def get_parser(site: str, http_client: Optional[HttpClient] = None) -> Optional[BaseParser]:
    """파서 반환 (편의 함수)"""
    factory = get_parser_factory()
    return factory.get_parser(site, http_client)


def get_supported_sites() -> List[str]:
    """지원되는 사이트 목록 (편의 함수)"""
    factory = get_parser_factory()
    return factory.get_supported_sites()


def is_site_supported(site: str) -> bool:
    """사이트 지원 여부 (편의 함수)"""
    factory = get_parser_factory()
    return factory.is_supported(site)


# 커스텀 파서 등록 데코레이터
def register_parser(site: str):
    """파서 등록 데코레이터"""
    def decorator(parser_class: Type[BaseParser]):
        factory = get_parser_factory()
        factory.register_parser(site, parser_class)
        return parser_class
    return decorator


if __name__ == "__main__":
    # 팩토리 테스트
    factory = get_parser_factory()
    
    print("=== 파서 팩토리 테스트 ===")
    
    # 지원되는 사이트 확인
    sites = factory.get_supported_sites()
    print(f"지원 사이트: {sites}")
    
    # 각 사이트별 파서 정보
    for site in sites:
        info = factory.get_parser_info(site)
        print(f"\n{site} 파서:")
        print(f"  클래스: {info.get('class_name')}")
        print(f"  모듈: {info.get('module')}")
        print(f"  지원됨: {info.get('supported')}")
        if info.get('name'):
            print(f"  이름: {info.get('name')}")
        if info.get('base_url'):
            print(f"  기본 URL: {info.get('base_url')}")
    
    # 파서 생성 테스트
    print(f"\n=== 파서 생성 테스트 ===")
    siksin_parser = factory.create_parser("siksin")
    if siksin_parser:
        print(f"✅ 식신 파서 생성 성공: {siksin_parser.__class__.__name__}")
        print(f"   통계: {siksin_parser.get_stats()}")
    else:
        print(f"❌ 식신 파서 생성 실패")
    
    # 설정 검증 테스트
    print(f"\n=== 설정 검증 테스트 ===")
    for site in sites:
        validation = factory.validate_site_config(site)
        print(f"{site}: {'✅' if validation['config_valid'] else '❌'}")
        if validation['errors']:
            for error in validation['errors']:
                print(f"  에러: {error}")
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"  경고: {warning}")
    
    # 헬스 체크
    print(f"\n=== 헬스 체크 ===")
    health = factory.health_check()
    print(f"팩토리 상태: {health['factory_status']}")
    print(f"지원 사이트 수: {health['supported_sites_count']}")
    
    print("\n✅ 파서 팩토리 테스트 완료!")