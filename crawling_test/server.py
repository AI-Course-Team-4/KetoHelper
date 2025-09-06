from flask import Flask, request, jsonify, send_from_directory
import json
import re
import time
from datetime import datetime
import os
import logging

# MCP Playwright-fetch 스타일 크롤링을 위한 import
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# 새로운 모듈들
from config import validate_config, get_crawling_headers, CRAWLING_DELAY, CRAWLING_TIMEOUT, FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from database_adapter import DatabaseAdapter
from embedding_service import EmbeddingService

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 서비스 인스턴스
db_adapter = None
embedding_service = None

def init_services():
    """서비스 초기화"""
    global db_adapter, embedding_service
    
    try:
        # 환경 설정 검증
        validate_config()
        logger.info("환경 설정 검증 완료")
        
        # 데이터베이스 어댑터 초기화
        db_adapter = DatabaseAdapter()
        if not db_adapter.test_connection():
            raise Exception("데이터베이스 연결 실패")
        
        # 임베딩 서비스 초기화
        embedding_service = EmbeddingService()
        
        logger.info("모든 서비스 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {e}")
        return False

# 메뉴 데이터 정규화 함수
def normalize_menu_data(menu_text):
    if not menu_text:
        return ""
    
    # 불필요한 문자 제거 (특수문자, 과도한 공백 등)
    normalized = re.sub(r'[^\w\s가-힣]', '', menu_text)
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    
    return normalized

# HTML 파일 서빙
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# 개선된 크롤링 함수 (CSS 셀렉터 기반)
def crawl_siksin_restaurant(restaurant_name):
    """
    개선된 식신 사이트 크롤링 함수
    정확한 CSS 셀렉터를 사용하여 데이터 추출
    """
    try:
        print(f"크롤링 시작: {restaurant_name}")
        
        # 1. 검색 페이지에서 식당 찾기
        encoded_name = quote(restaurant_name)
        search_url = f"https://www.siksinhot.com/search?keywords={encoded_name}"
        
        headers = get_crawling_headers()
        
        logger.info(f"검색 페이지 요청: {search_url}")
        time.sleep(CRAWLING_DELAY)  # 서버 부담 방지
        
        response = requests.get(search_url, headers=headers, timeout=CRAWLING_TIMEOUT)
        if response.status_code != 200:
            logger.error(f"검색 페이지 요청 실패: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        first_link = soup.find('a', href=re.compile(r'/P/\d+'))
        
        if not first_link:
            logger.warning("검색 결과를 찾을 수 없습니다.")
            return None
            
        restaurant_url = first_link['href']
        if not restaurant_url.startswith('http'):
            restaurant_url = f"https://www.siksinhot.com{restaurant_url}"
        
        logger.info(f"식당 페이지 URL: {restaurant_url}")
        time.sleep(CRAWLING_DELAY)  # 서버 부담 방지
        
        # 2. 식당 페이지 데이터 추출
        restaurant_response = requests.get(restaurant_url, headers=headers, timeout=CRAWLING_TIMEOUT)
        if restaurant_response.status_code != 200:
            logger.error(f"식당 페이지 요청 실패: {restaurant_response.status_code}")
            return None
        
        restaurant_soup = BeautifulSoup(restaurant_response.content, 'html.parser')
        
        # 3. 식당명 추출 (h1 태그에서)
        name_element = restaurant_soup.find('h1')
        name = name_element.get_text().strip() if name_element else restaurant_name
        print(f"추출된 식당명: {name}")
        
        # 4. 주소 정보 추출 (정확한 CSS 셀렉터 사용)
        # 도로명 주소 추출
        road_address = "주소 정보 없음"
        address_span = restaurant_soup.find('span', class_='address-text')
        if address_span:
            road_address = address_span.get_text().strip()
            print(f"추출된 도로명 주소: {road_address}")
        
        # 지번 주소 추출
        jibun_address = "지번 주소 정보 없음"
        address_info_div = restaurant_soup.find('div', class_='address-info')
        if address_info_div:
            address_text = address_info_div.get_text()
            jibun_match = re.search(r'지번([^복사]+)', address_text)
            if jibun_match:
                jibun_address = jibun_match.group(1).strip()
                print(f"추출된 지번 주소: {jibun_address}")
        
        # 5. 메뉴 정보 추출 (li.menu-list에서)
        menu_items = restaurant_soup.find_all('li', class_='menu-list')
        print(f"발견된 메뉴 항목 수: {len(menu_items)}")
        
        menu_list = []
        for menu_li in menu_items:
            menu_text = menu_li.get_text().strip()
            
            # 가격 추출
            price_pattern = r'(\d+,?\d*)\s*원'
            price_match = re.search(price_pattern, menu_text)
            price = None
            if price_match:
                price_str = price_match.group(1)
                price = int(price_str.replace(',', ''))
            
            # 메뉴명 추출 (가격 부분 제거)
            menu_name = re.sub(r'\d+,?\d*\s*원.*$', '', menu_text).strip()
            
            if menu_name and len(menu_name) > 0:
                menu_item = {"name": menu_name}
                if price is not None:
                    menu_item["price"] = price
                menu_list.append(menu_item)
        
        print(f"추출된 메뉴 (가격 포함): {menu_list}")
        
        # 6. JSON 형태로 데이터 구조화는 이미 완료됨
        
        return {
            'restaurant_name': name,
            'address': {
                'road_address': road_address,
                'jibun_address': jibun_address
            },
            'menu': menu_list if menu_list else [{"name": "메뉴 정보를 찾을 수 없습니다"}]
        }
        
    except Exception as e:
        print(f"크롤링 오류: {str(e)}")
        return None

# 크롤링 요청 처리
@app.route('/crawl', methods=['POST'])
def crawl_restaurant():
    try:
        data = request.get_json()
        restaurant_name = data.get('restaurantName', '').strip()
        
        if not restaurant_name:
            return jsonify({'error': '음식점 이름을 입력해주세요.'}), 400
        
        print(f"크롤링 요청 받음: {restaurant_name}")
        
        # 실제 식신 사이트 크롤링
        crawled_data = crawl_siksin_restaurant(restaurant_name)
        
        if not crawled_data:
            return jsonify({'error': '해당 음식점을 찾을 수 없습니다. 다른 이름으로 시도해보세요.'}), 404
        
        # Supabase에 저장 (임베딩 생성은 별도 배치 처리)
        save_result = save_to_supabase(crawled_data)
        
        return jsonify({
            'success': True,
            'data': crawled_data,
            'restaurant_id': save_result['restaurant_id'],
            'menuCount': save_result['menu_count'],
            'message': '크롤링 완료! 임베딩은 별도 배치로 처리됩니다.'
        })
        
    except Exception as e:
        logger.error(f"서버 오류: {str(e)}")
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

# 통계 및 모니터링 엔드포인트
@app.route('/stats')
def get_stats():
    """시스템 통계 조회"""
    try:
        if not db_adapter:
            return jsonify({'error': '서비스가 초기화되지 않았습니다'}), 503
        
        stats = db_adapter.get_statistics()
        embedding_stats = embedding_service.get_embedding_stats()
        
        return jsonify({
            'database': stats,
            'embedding': embedding_stats,
            'status': 'healthy'
        })
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs')
def get_crawling_logs():
    """크롤링 로그 조회"""
    try:
        if not db_adapter:
            return jsonify({'error': '서비스가 초기화되지 않았습니다'}), 503
        
        limit = request.args.get('limit', 20, type=int)
        logs = db_adapter.get_crawling_logs(limit=limit)
        
        return jsonify({
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        logger.error(f"로그 조회 실패: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """헬스체크 엔드포인트"""
    try:
        if not db_adapter or not embedding_service:
            return jsonify({
                'status': 'unhealthy',
                'message': '서비스가 초기화되지 않았습니다'
            }), 503
        
        db_healthy = db_adapter.test_connection()
        
        return jsonify({
            'status': 'healthy' if db_healthy else 'degraded',
            'database': db_healthy,
            'services': {
                'database_adapter': db_adapter is not None,
                'embedding_service': embedding_service is not None
            }
        })
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# 임베딩 관리 API 엔드포인트들
@app.route('/embeddings/status')
def get_embedding_status():
    """임베딩 상태 조회"""
    try:
        if not db_adapter:
            return jsonify({'error': '서비스가 초기화되지 않았습니다'}), 503
        
        stats = db_adapter.get_statistics()
        
        total_menus = stats.get('menus_count', 0)
        with_embedding = stats.get('menus_with_embedding', 0)
        without_embedding = total_menus - with_embedding
        coverage_percentage = (with_embedding / total_menus * 100) if total_menus > 0 else 0
        
        return jsonify({
            'total_menus': total_menus,
            'with_embedding': with_embedding,
            'without_embedding': without_embedding,
            'coverage_percentage': round(coverage_percentage, 1),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"임베딩 상태 조회 실패: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/embeddings/pending')
def get_pending_embeddings():
    """임베딩이 필요한 메뉴 목록 조회"""
    try:
        if not db_adapter:
            return jsonify({'error': '서비스가 초기화되지 않았습니다'}), 503
        
        limit = request.args.get('limit', 10, type=int)
        restaurant_id = request.args.get('restaurant_id')
        
        # 임베딩이 없는 메뉴 조회
        query = db_adapter.client.table('menus').select(
            'id, name, restaurant_id, created_at, restaurants(name, address)'
        ).is_('embedding', 'null')
        
        if restaurant_id:
            query = query.eq('restaurant_id', restaurant_id)
        
        query = query.limit(limit).order('created_at', desc=True)
        result = query.execute()
        
        pending_menus = []
        for menu in result.data or []:
            restaurant_info = menu.get('restaurants', {})
            pending_menus.append({
                'menu_id': menu['id'],
                'menu_name': menu['name'],
                'restaurant_id': menu['restaurant_id'],
                'restaurant_name': restaurant_info.get('name', ''),
                'restaurant_address': restaurant_info.get('address', ''),
                'created_at': menu['created_at']
            })
        
        return jsonify({
            'pending_menus': pending_menus,
            'count': len(pending_menus),
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"대기 중인 임베딩 조회 실패: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/embeddings/process', methods=['POST'])
def process_embeddings():
    """배치 임베딩 처리 실행"""
    try:
        if not embedding_service:
            return jsonify({'error': '임베딩 서비스가 초기화되지 않았습니다'}), 503
        
        data = request.get_json() or {}
        limit = data.get('limit')
        restaurant_id = data.get('restaurant_id')
        
        logger.info(f"배치 임베딩 처리 시작 - limit: {limit}, restaurant_id: {restaurant_id}")
        
        # 임베딩이 없는 메뉴들 처리
        if restaurant_id:
            # 특정 식당만 처리
            query = db_adapter.client.table('menus').select(
                'id'
            ).eq('restaurant_id', restaurant_id).is_('embedding', 'null')
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            menu_ids = [menu['id'] for menu in result.data or []]
            
            if menu_ids:
                embedding_result = embedding_service.process_new_menus(menu_ids)
            else:
                embedding_result = {'processed': 0, 'success': 0, 'failed': 0}
        else:
            # 모든 대기 중인 메뉴 처리
            embedding_result = embedding_service.process_menus_without_embedding()
        
        logger.info(f"배치 임베딩 처리 완료: {embedding_result}")
        
        return jsonify({
            'success': True,
            'result': embedding_result,
            'message': f"처리 완료: 성공 {embedding_result.get('success', 0)}개, 실패 {embedding_result.get('failed', 0)}개"
        })
        
    except Exception as e:
        logger.error(f"배치 임베딩 처리 실패: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/embeddings/restaurant/<restaurant_id>/process', methods=['POST'])
def process_restaurant_embeddings(restaurant_id):
    """특정 식당의 임베딩 처리"""
    try:
        if not embedding_service:
            return jsonify({'error': '임베딩 서비스가 초기화되지 않았습니다'}), 503
        
        logger.info(f"식당별 임베딩 처리 시작: {restaurant_id}")
        
        # 해당 식당의 임베딩이 없는 메뉴 ID 조회
        result = db_adapter.client.table('menus').select('id').eq(
            'restaurant_id', restaurant_id
        ).is_('embedding', 'null').execute()
        
        menu_ids = [menu['id'] for menu in result.data or []]
        
        if not menu_ids:
            return jsonify({
                'success': True,
                'message': '해당 식당의 모든 메뉴가 이미 임베딩을 가지고 있습니다.',
                'result': {'processed': 0, 'success': 0, 'failed': 0}
            })
        
        # 임베딩 처리
        embedding_result = embedding_service.process_new_menus(menu_ids)
        
        return jsonify({
            'success': True,
            'restaurant_id': restaurant_id,
            'result': embedding_result,
            'message': f"식당 임베딩 처리 완료: 성공 {embedding_result.get('success', 0)}개"
        })
        
    except Exception as e:
        logger.error(f"식당별 임베딩 처리 실패: {e}")
        return jsonify({'error': str(e)}), 500

# Supabase 저장 함수 (정규화된 3개 테이블 구조)
def save_to_supabase(data):
    """크롤링 데이터를 Supabase에 저장하고 임베딩 생성"""
    try:
        # 1. 식당 데이터 변환
        restaurant_data = transform_restaurant_data(data)
        
        # 2. 식당 저장 (중복 체크)
        restaurant_id = db_adapter.upsert_restaurant(restaurant_data)
        if not restaurant_id:
            raise Exception("식당 저장 실패")
        
        # 3. 메뉴 데이터 변환
        menu_data_list = transform_menu_data(data, restaurant_id)
        
        # 4. 메뉴 배치 저장
        menu_ids = db_adapter.insert_menus_batch(menu_data_list)
        if not menu_ids:
            raise Exception("메뉴 저장 실패")
        
        # 5. 크롤링 로그 저장
        log_data = {
            'restaurant_id': restaurant_id,
            'site': 'siksin',
            'status': 'success',
            'menus_count': len(menu_ids)
        }
        db_adapter.insert_crawling_log(log_data)
        
        logger.info(f"데이터 저장 완료: 식당 {restaurant_id}, 메뉴 {len(menu_ids)}개")
        logger.info("임베딩은 별도 배치 프로세스에서 처리됩니다")
        
        return {
            'restaurant_id': restaurant_id,
            'menu_count': len(menu_ids)
        }
        
    except Exception as e:
        # 실패 로그 저장
        if 'restaurant_id' in locals():
            error_log_data = {
                'restaurant_id': restaurant_id,
                'site': 'siksin',
                'status': 'failed',
                'menus_count': 0,
                'error_message': str(e)
            }
            db_adapter.insert_crawling_log(error_log_data)
        
        logger.error(f"Supabase 저장 실패: {e}")
        raise e

def transform_restaurant_data(crawled_data):
    """크롤링 데이터를 restaurants 테이블 형식으로 변환"""
    road_address = crawled_data['address']['road_address'] if isinstance(crawled_data['address'], dict) else crawled_data['address']
    jibun_address = crawled_data['address'].get('jibun_address') if isinstance(crawled_data['address'], dict) else None
    
    return {
        'name': crawled_data['restaurant_name'],
        'address': road_address,
        'jibun_address': jibun_address,
        'source': 'siksin_crawler',
        'metadata': {
            'crawled_at': datetime.now().isoformat(),
            'original_data': crawled_data,
            'site': 'siksin'
        }
    }

def transform_menu_data(crawled_data, restaurant_id):
    """크롤링 데이터를 menus 테이블 형식으로 변환"""
    restaurant_name = crawled_data['restaurant_name']
    road_address = crawled_data['address']['road_address'] if isinstance(crawled_data['address'], dict) else crawled_data['address']
    
    menu_data_list = []
    for menu_item in crawled_data['menu']:
        if isinstance(menu_item, dict):
            menu_name = menu_item.get('name', '')
            menu_price = menu_item.get('price')
        else:
            menu_name = menu_item
            menu_price = None
        
        normalized_menu = normalize_menu_data(menu_name)
        if normalized_menu:  # 정규화된 메뉴가 비어있지 않은 경우만 처리
            # 검색용 텍스트 생성
            menu_text = f"{restaurant_name} {normalized_menu} {road_address}"
            
            menu_data = {
                'restaurant_id': restaurant_id,
                'name': normalized_menu,
                'price': menu_price,
                'menu_text': menu_text
            }
            menu_data_list.append(menu_data)
    
    return menu_data_list

if __name__ == '__main__':
    # 서비스 초기화
    if not init_services():
        logger.error("서비스 초기화 실패. 서버를 시작할 수 없습니다.")
        exit(1)
    
    logger.info(f"서버가 시작되었습니다. http://{FLASK_HOST}:{FLASK_PORT} 에서 확인하세요.")
    logger.info("Supabase 연동 크롤링 시스템 V2 실행 중...")
    
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
