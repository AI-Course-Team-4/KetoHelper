"""
캐시 관리자
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """캐시 관리자"""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or settings.get_data_path("cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 캐시 파일 경로들
        self.crawl_cache_file = self.cache_dir / "crawl_results.json"
        self.geocoding_cache_file = self.cache_dir / "geocoding_results.json"
        self.metadata_cache_file = self.cache_dir / "cache_metadata.json"

        # 메모리 캐시
        self._memory_cache: Dict[str, Any] = {}
        self._cache_metadata: Dict[str, Any] = {}

        # TTL 설정
        self.default_ttl = settings.cache.ttl
        self.geocoding_ttl = 30 * 24 * 3600  # 30일

    async def initialize(self):
        """캐시 매니저 초기화"""
        await self._load_cache_metadata()
        logger.info("Cache manager initialized")

    async def get_recent_crawl_data(
        self,
        source_name: str,
        max_age_hours: int = 24
    ) -> Optional[List[Dict[str, Any]]]:
        """최근 크롤링 데이터 조회"""
        cache_key = f"crawl_{source_name}"

        # 메모리 캐시 확인
        if cache_key in self._memory_cache:
            cached_data = self._memory_cache[cache_key]
            if self._is_cache_valid(cache_key, max_age_hours * 3600):
                logger.info(f"Using memory cached crawl data for {source_name}")
                return cached_data

        # 파일 캐시 확인
        file_data = await self._load_from_file_cache(self.crawl_cache_file, cache_key)
        if file_data and self._is_cache_valid(cache_key, max_age_hours * 3600):
            logger.info(f"Using file cached crawl data for {source_name}")
            # 메모리 캐시에도 저장
            self._memory_cache[cache_key] = file_data
            return file_data

        return None

    async def store_crawl_data(
        self,
        source_name: str,
        data: List[Dict[str, Any]]
    ):
        """크롤링 데이터 저장"""
        cache_key = f"crawl_{source_name}"

        # 메모리 캐시 저장
        self._memory_cache[cache_key] = data
        self._update_cache_metadata(cache_key)

        # 파일 캐시 저장
        await self._save_to_file_cache(self.crawl_cache_file, cache_key, data)

        logger.info(f"Cached crawl data for {source_name} ({len(data)} items)")

    async def get_geocoding_result(self, address: str) -> Optional[Dict[str, Any]]:
        """지오코딩 결과 조회"""
        cache_key = f"geo_{hash(address)}"

        # 메모리 캐시 확인
        if cache_key in self._memory_cache:
            cached_data = self._memory_cache[cache_key]
            if self._is_cache_valid(cache_key, self.geocoding_ttl):
                return cached_data

        # 파일 캐시 확인
        file_data = await self._load_from_file_cache(self.geocoding_cache_file, cache_key)
        if file_data and self._is_cache_valid(cache_key, self.geocoding_ttl):
            # 메모리 캐시에도 저장
            self._memory_cache[cache_key] = file_data
            return file_data

        return None

    async def store_geocoding_result(
        self,
        address: str,
        result: Dict[str, Any]
    ):
        """지오코딩 결과 저장"""
        cache_key = f"geo_{hash(address)}"

        # 주소 정보 추가
        result_with_meta = {
            **result,
            'cached_address': address,
            'cached_at': datetime.utcnow().isoformat()
        }

        # 메모리 캐시 저장
        self._memory_cache[cache_key] = result_with_meta
        self._update_cache_metadata(cache_key)

        # 파일 캐시 저장
        await self._save_to_file_cache(self.geocoding_cache_file, cache_key, result_with_meta)

        logger.debug(f"Cached geocoding result for: {address}")

    async def clear_expired_cache(self):
        """만료된 캐시 정리"""
        current_time = datetime.utcnow()
        expired_keys = []

        for key, metadata in self._cache_metadata.items():
            cached_at = datetime.fromisoformat(metadata.get('cached_at', '1970-01-01'))
            ttl = metadata.get('ttl', self.default_ttl)

            if (current_time - cached_at).total_seconds() > ttl:
                expired_keys.append(key)

        # 메모리 캐시에서 제거
        for key in expired_keys:
            self._memory_cache.pop(key, None)
            self._cache_metadata.pop(key, None)

        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        memory_count = len(self._memory_cache)
        metadata_count = len(self._cache_metadata)

        # 파일 캐시 크기 계산
        total_file_size = 0
        for cache_file in [self.crawl_cache_file, self.geocoding_cache_file]:
            if cache_file.exists():
                total_file_size += cache_file.stat().st_size

        # 캐시 히트율 계산 (메타데이터에서)
        total_requests = sum(
            meta.get('hit_count', 0) for meta in self._cache_metadata.values()
        )

        return {
            'memory_cache_count': memory_count,
            'file_cache_count': metadata_count,
            'total_file_size_mb': round(total_file_size / (1024 * 1024), 2),
            'total_requests': total_requests,
            'cache_directory': str(self.cache_dir)
        }

    async def clear_all_cache(self):
        """모든 캐시 정리"""
        # 메모리 캐시 정리
        self._memory_cache.clear()
        self._cache_metadata.clear()

        # 파일 캐시 정리
        for cache_file in [self.crawl_cache_file, self.geocoding_cache_file, self.metadata_cache_file]:
            if cache_file.exists():
                cache_file.unlink()

        logger.info("All cache cleared")

    def _is_cache_valid(self, cache_key: str, max_age_seconds: int) -> bool:
        """캐시 유효성 확인"""
        metadata = self._cache_metadata.get(cache_key)
        if not metadata:
            return False

        cached_at = datetime.fromisoformat(metadata.get('cached_at', '1970-01-01'))
        age = (datetime.utcnow() - cached_at).total_seconds()

        return age <= max_age_seconds

    def _update_cache_metadata(self, cache_key: str):
        """캐시 메타데이터 업데이트"""
        current_meta = self._cache_metadata.get(cache_key, {})

        self._cache_metadata[cache_key] = {
            'cached_at': datetime.utcnow().isoformat(),
            'hit_count': current_meta.get('hit_count', 0) + 1,
            'ttl': self.default_ttl
        }

    async def _load_cache_metadata(self):
        """캐시 메타데이터 로드"""
        if self.metadata_cache_file.exists():
            try:
                async with aiofiles.open(self.metadata_cache_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    self._cache_metadata = json.loads(content)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                self._cache_metadata = {}

    async def _save_cache_metadata(self):
        """캐시 메타데이터 저장"""
        try:
            async with aiofiles.open(self.metadata_cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self._cache_metadata, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    async def _load_from_file_cache(
        self,
        cache_file: Path,
        cache_key: str
    ) -> Optional[Any]:
        """파일 캐시에서 로드"""
        if not cache_file.exists():
            return None

        try:
            async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                cache_data = json.loads(content)
                return cache_data.get(cache_key)
        except Exception as e:
            logger.warning(f"Failed to load from file cache {cache_file}: {e}")
            return None

    async def _save_to_file_cache(
        self,
        cache_file: Path,
        cache_key: str,
        data: Any
    ):
        """파일 캐시에 저장"""
        try:
            # 기존 캐시 데이터 로드
            cache_data = {}
            if cache_file.exists():
                async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    cache_data = json.loads(content) if content.strip() else {}

            # 새 데이터 추가
            cache_data[cache_key] = data

            # 파일에 저장
            async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(cache_data, indent=2, ensure_ascii=False, default=str))

            # 메타데이터 저장
            await self._save_cache_metadata()

        except Exception as e:
            logger.error(f"Failed to save to file cache {cache_file}: {e}")

# 캐시 정리 백그라운드 태스크
async def cache_cleanup_task(cache_manager: CacheManager, interval_hours: int = 6):
    """캐시 정리 백그라운드 태스크"""
    while True:
        try:
            await cache_manager.clear_expired_cache()
            await asyncio.sleep(interval_hours * 3600)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Cache cleanup task error: {e}")
            await asyncio.sleep(300)  # 5분 후 재시도