"""
크롤러 설정 및 등록
"""

from services.crawler.crawler_factory import crawler_factory
from services.crawler.diningcode_crawler import DiningcodeCrawler
from services.crawler.selenium_diningcode_crawler import SeleniumDiningcodeCrawler

def register_crawlers():
    """사용 가능한 크롤러들을 팩토리에 등록"""
    # 다이닝코드 크롤러 등록 (기본 httpx 버전)
    crawler_factory.register('diningcode', DiningcodeCrawler)
    
    # Selenium 무한 스크롤 크롤러 등록
    crawler_factory.register('selenium_diningcode', SeleniumDiningcodeCrawler)

    # 향후 추가할 크롤러들
    # crawler_factory.register('siksin', SiksinCrawler)
    # crawler_factory.register('mangoplate', MangoPlateCrawler)

# 시스템 시작시 자동 등록
register_crawlers()