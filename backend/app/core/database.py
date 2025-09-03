from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

# 전역 데이터베이스 인스턴스
db = Database()

async def connect_to_mongo():
    """MongoDB에 연결"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.MONGODB_DATABASE]
        
        # 연결 테스트
        await db.client.admin.command('ping')
        logger.info(f"✅ MongoDB 연결 성공: {settings.MONGODB_DATABASE}")
        
    except Exception as e:
        logger.error(f"❌ MongoDB 연결 실패: {e}")
        raise

async def close_mongo_connection():
    """MongoDB 연결 종료"""
    if db.client:
        db.client.close()
        logger.info("📴 MongoDB 연결 종료")

def get_database() -> AsyncIOMotorDatabase:
    """데이터베이스 인스턴스 반환"""
    return db.database

def get_collection(collection_name: str):
    """컬렉션 반환"""
    return db.database[collection_name]
