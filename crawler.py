#!/usr/bin/env python3
"""
🕷️ 식당 크롤링 시스템 - MVP v1.0

사용법:
    python crawler.py --restaurant "강남 맛집" --site siksin
    python crawler.py --restaurant "강남역 맛집" --site siksin --max-results 10
    python crawler.py --help
"""

import sys
import asyncio
import click
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config_loader import get_config
from src.utils.logger import setup_logging, get_logger


@click.group()
@click.option('--config', '-c', type=str, help='설정 파일 경로')
@click.option('--debug', '-d', is_flag=True, help='디버그 모드')
@click.pass_context
def cli(ctx, config, debug):
    """🕷️ 식당 크롤링 시스템 - MVP v1.0"""
    
    # 컨텍스트 초기화
    ctx.ensure_object(dict)
    
    # 설정 초기화
    try:
        app_config = get_config(config)
        ctx.obj['config'] = app_config
        
        # 디버그 모드 설정
        if debug:
            app_config.app.debug = True
        
        # 로깅 설정
        setup_logging(config)
        
    except Exception as e:
        click.echo(f"❌ 설정 초기화 실패: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--restaurant', '-r', required=True, help='크롤링할 식당명 (예: "강남 맛집")')
@click.option('--site', '-s', default='siksin', 
              type=click.Choice(['siksin', 'diningcode', 'mangoplate']),
              help='크롤링 대상 사이트')
@click.option('--max-results', '-m', default=10, help='최대 결과 수')
@click.option('--save-raw', is_flag=True, help='원본 HTML 저장')
@click.pass_context
def crawl(ctx, restaurant, site, max_results, save_raw):
    """🔍 식당 크롤링 실행"""
    
    config = ctx.obj['config']
    logger = get_logger("crawler")
    
    click.echo(f"🕷️ 크롤링 시작: {restaurant} ({site})")
    click.echo(f"📊 최대 결과: {max_results}개")
    
    try:
        # 크롤링 실행 (비동기)
        result = asyncio.run(
            run_crawling(config, restaurant, site, max_results, save_raw)
        )
        
        # 결과 출력
        click.echo(f"\n✅ 크롤링 완료!")
        click.echo(f"   📍 식당: {result['restaurants_found']}개")
        click.echo(f"   🍽️ 메뉴: {result['menus_found']}개")
        click.echo(f"   ⏱️ 소요시간: {result['duration']:.2f}초")
        
        if result['errors']:
            click.echo(f"   ⚠️ 에러: {len(result['errors'])}건")
            for error in result['errors'][:3]:  # 최대 3개만 표시
                click.echo(f"      - {error}")
                
    except KeyboardInterrupt:
        click.echo("\n🛑 사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"크롤링 실패: {e}")
        click.echo(f"❌ 크롤링 실패: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """📊 시스템 상태 확인"""
    
    config = ctx.obj['config']
    
    click.echo("📊 시스템 상태")
    click.echo("=" * 50)
    click.echo(f"앱 이름: {config.app.name}")
    click.echo(f"버전: {config.app.version}")
    click.echo(f"디버그 모드: {config.app.debug}")
    click.echo(f"데이터베이스: {config.database.host}:{config.database.port}")
    click.echo(f"로그 레벨: {config.logging.level}")
    
    click.echo("\n🕷️ 크롤러 설정")
    click.echo(f"동시 탭 수: {config.crawler.max_concurrent_tabs}")
    click.echo(f"페이지 타임아웃: {config.crawler.page_timeout}초")
    click.echo(f"속도 제한: {config.crawler.rate_limits}")
    
    # TODO: 데이터베이스 연결 테스트
    # TODO: 크롤링 통계 표시


@cli.command()
@click.pass_context  
def config_test(ctx):
    """🔧 설정 파일 테스트"""
    
    config = ctx.obj['config']
    
    click.echo("🔧 설정 파일 테스트")
    click.echo("=" * 50)
    
    try:
        # 데이터베이스 URL 테스트
        db_url = config.get_database_url()
        click.echo(f"✅ 데이터베이스 URL: {db_url}")
        
        # 파서 설정 테스트
        for site in ['siksin']:
            try:
                parser_config = config.get_parser_config(site)
                click.echo(f"✅ {site} 파서 설정: OK")
            except Exception as e:
                click.echo(f"❌ {site} 파서 설정: {e}")
        
        # 사용자 에이전트 테스트
        user_agent = config.get_user_agent()
        click.echo(f"✅ 사용자 에이전트: {user_agent[:50]}...")
        
        click.echo("\n✅ 모든 설정이 정상입니다!")
        
    except Exception as e:
        click.echo(f"❌ 설정 테스트 실패: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--site', '-s', default='all', help='통계를 볼 사이트 (all, siksin, etc.)')
@click.pass_context
def stats(ctx, site):
    """📈 크롤링 통계 조회"""
    
    click.echo(f"📈 크롤링 통계 ({site})")
    click.echo("=" * 50)
    
    # TODO: 데이터베이스에서 통계 조회
    click.echo("아직 구현되지 않았습니다.")
    click.echo("데이터베이스 연동 후 구현 예정")


async def run_crawling(config, restaurant_keyword, site, max_results, save_raw):
    """실제 크롤링 로직 (비동기)"""
    import time
    
    logger = get_logger("crawler")
    start_time = time.time()
    
    # TODO: 실제 크롤링 엔진 구현 후 교체
    logger.info(f"크롤링 시뮬레이션: {restaurant_keyword} ({site})")
    
    # 시뮬레이션: 가짜 결과 반환
    await asyncio.sleep(2)  # 크롤링 시뮬레이션
    
    duration = time.time() - start_time
    
    return {
        "restaurants_found": 5,
        "menus_found": 25,
        "duration": duration,
        "errors": []
    }


if __name__ == "__main__":
    # CLI 실행
    cli()