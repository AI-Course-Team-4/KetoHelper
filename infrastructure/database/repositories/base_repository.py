"""
기본 Repository 구현체
"""

from typing import List, Optional, Type, TypeVar, Dict, Any, Callable
from uuid import UUID
import asyncpg
import logging
from abc import ABC

from infrastructure.database.connection import DatabasePool
from core.interfaces.repository_interface import RepositoryInterface

T = TypeVar('T')
logger = logging.getLogger(__name__)

class BaseRepository(RepositoryInterface[T], ABC):
    """기본 Repository 구현체"""

    def __init__(self, db_pool: DatabasePool, entity_class: Type[T], table_name: str):
        self.db_pool = db_pool
        self.entity_class = entity_class
        self.table_name = table_name

    async def save(self, entity: T) -> T:
        """엔티티 저장 (INSERT 또는 UPDATE)"""
        # 엔티티가 이미 존재하는지 확인
        exists = await self.exists(entity.id)

        if exists:
            return await self.update(entity)
        else:
            return await self._insert(entity)

    async def save_batch(self, entities: List[T]) -> List[T]:
        """엔티티 일괄 저장"""
        if not entities:
            return []

        saved_entities = []
        async with self.db_pool.transaction() as conn:
            for entity in entities:
                saved_entity = await self._save_with_connection(entity, conn)
                saved_entities.append(saved_entity)

        return saved_entities

    async def _save_with_connection(self, entity: T, conn: asyncpg.Connection) -> T:
        """연결을 사용한 엔티티 저장"""
        exists_query = f"SELECT 1 FROM {self.table_name} WHERE id = $1"
        exists = await conn.fetchval(exists_query, entity.id)

        if exists:
            return await self._update_with_connection(entity, conn)
        else:
            return await self._insert_with_connection(entity, conn)

    async def find_by_id(self, entity_id: UUID) -> Optional[T]:
        """ID로 엔티티 조회"""
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        row = await self.db_pool.fetchrow(query, entity_id)

        if row:
            return self._row_to_entity(row)
        return None

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """전체 엔티티 조회"""
        query = f"""
        SELECT * FROM {self.table_name}
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """
        rows = await self.db_pool.fetch(query, limit, offset)
        return [self._row_to_entity(row) for row in rows]

    async def update(self, entity: T) -> T:
        """엔티티 업데이트"""
        async with self.db_pool.acquire() as conn:
            return await self._update_with_connection(entity, conn)

    async def delete(self, entity_id: UUID) -> bool:
        """엔티티 삭제"""
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        result = await self.db_pool.execute(query, entity_id)

        # DELETE 명령의 결과는 "DELETE n" 형식
        return result.endswith(" 1")

    async def exists(self, entity_id: UUID) -> bool:
        """엔티티 존재 여부 확인"""
        query = f"SELECT 1 FROM {self.table_name} WHERE id = $1"
        result = await self.db_pool.fetchval(query, entity_id)
        return result is not None

    async def count(self, **filters) -> int:
        """엔티티 개수 조회"""
        where_clause, params = self._build_where_clause(**filters)
        query = f"SELECT COUNT(*) FROM {self.table_name}{where_clause}"

        return await self.db_pool.fetchval(query, *params)

    async def find_with_filters(self, limit: int = 100, offset: int = 0, **filters) -> List[T]:
        """필터를 사용한 엔티티 조회"""
        where_clause, params = self._build_where_clause(**filters)
        query = f"""
        SELECT * FROM {self.table_name}{where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """

        rows = await self.db_pool.fetch(query, *params, limit, offset)
        return [self._row_to_entity(row) for row in rows]

    def _build_where_clause(self, **filters) -> tuple[str, list]:
        """WHERE 절 생성"""
        if not filters:
            return "", []

        conditions = []
        params = []
        param_index = 1

        for key, value in filters.items():
            if value is not None:
                conditions.append(f"{key} = ${param_index}")
                params.append(value)
                param_index += 1

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    async def _insert(self, entity: T) -> T:
        """엔티티 삽입"""
        async with self.db_pool.acquire() as conn:
            return await self._insert_with_connection(entity, conn)

    async def _insert_with_connection(self, entity: T, conn: asyncpg.Connection) -> T:
        """연결을 사용한 엔티티 삽입"""
        columns, values, placeholders = self._prepare_insert_data(entity)

        query = f"""
        INSERT INTO {self.table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING *
        """

        row = await conn.fetchrow(query, *values)
        return self._row_to_entity(row)

    async def _update_with_connection(self, entity: T, conn: asyncpg.Connection) -> T:
        """연결을 사용한 엔티티 업데이트"""
        # updated_at 필드가 있으면 자동 갱신
        if hasattr(entity, 'update_timestamp'):
            entity.update_timestamp()

        columns, values = self._prepare_update_data(entity)

        set_clause = ', '.join([f"{col} = ${i+2}" for i, col in enumerate(columns)])
        query = f"""
        UPDATE {self.table_name}
        SET {set_clause}
        WHERE id = $1
        RETURNING *
        """

        row = await conn.fetchrow(query, entity.id, *values)
        if row:
            return self._row_to_entity(row)
        else:
            raise ValueError(f"Entity with id {entity.id} not found for update")

    def _prepare_insert_data(self, entity: T) -> tuple[list, list, list]:
        """INSERT를 위한 데이터 준비"""
        entity_dict = self._entity_to_dict(entity)

        columns = list(entity_dict.keys())
        values = list(entity_dict.values())
        placeholders = [f"${i+1}" for i in range(len(values))]

        return columns, values, placeholders

    def _prepare_update_data(self, entity: T) -> tuple[list, list]:
        """UPDATE를 위한 데이터 준비"""
        entity_dict = self._entity_to_dict(entity)

        # id는 WHERE 절에서 사용하므로 제외
        if 'id' in entity_dict:
            del entity_dict['id']

        columns = list(entity_dict.keys())
        values = list(entity_dict.values())

        return columns, values

    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """엔티티를 딕셔너리로 변환"""
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        elif hasattr(entity, '__dict__'):
            return entity.__dict__.copy()
        else:
            raise ValueError(f"Cannot convert entity {type(entity)} to dict")

    def _row_to_entity(self, row: asyncpg.Record) -> T:
        """DB 레코드를 엔티티로 변환"""
        row_dict = dict(row)

        # 엔티티 클래스에 from_dict 메서드가 있으면 사용
        if hasattr(self.entity_class, 'from_dict'):
            return self.entity_class.from_dict(row_dict)
        else:
            # 기본 생성자 사용
            return self.entity_class(**row_dict)

    async def execute_raw_query(self, query: str, *params) -> Any:
        """원시 쿼리 실행"""
        return await self.db_pool.execute(query, *params)

    async def fetch_raw_query(self, query: str, *params) -> List[asyncpg.Record]:
        """원시 쿼리로 데이터 조회"""
        return await self.db_pool.fetch(query, *params)

    async def fetchrow_raw_query(self, query: str, *params) -> Optional[asyncpg.Record]:
        """원시 쿼리로 단일 레코드 조회"""
        return await self.db_pool.fetchrow(query, *params)

    async def fetchval_raw_query(self, query: str, *params) -> Any:
        """원시 쿼리로 단일 값 조회"""
        return await self.db_pool.fetchval(query, *params)