"""
SQLAlchemy 데이터베이스 모델 정의
Supabase PostgreSQL + pgvector 지원
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, TIMESTAMP, Date, ARRAY, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, DOUBLE_PRECISION
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
# from pgvector.sqlalchemy import Vector
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # pgvector가 설치되지 않은 경우 임시로 Text 타입 사용
    from sqlalchemy import Text as Vector
import uuid

from app.core.database import Base

class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nickname = Column(String(100))
    goals_kcal = Column(Integer)
    goals_carbs_g = Column(Integer)
    allergies = Column(ARRAY(String), default=[])
    dislikes = Column(ARRAY(String), default=[])
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # 관계
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    weights = relationship("Weight", back_populates="user", cascade="all, delete-orphan")

class Recipe(Base):
    """레시피 테이블"""
    __tablename__ = "recipes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    tags = Column(ARRAY(String), default=[])
    ketoized = Column(Boolean, default=False)
    macros = Column(JSONB)  # {kcal, carb, protein, fat}
    source = Column(Text)
    ingredients = Column(JSONB)  # [{name, amount, unit}]
    steps = Column(ARRAY(Text))
    tips = Column(ARRAY(Text))
    allergen_flags = Column(ARRAY(String), default=[])
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # 관계
    embeddings = relationship("RecipeEmbedding", back_populates="recipe", cascade="all, delete-orphan")

class RecipeEmbedding(Base):
    """레시피 임베딩 테이블 (pgvector)"""
    __tablename__ = "recipe_embeddings"
    
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    chunk_idx = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # OpenAI text-embedding-3-small 차원
    
    # 관계
    recipe = relationship("Recipe", back_populates="embeddings")

class PlaceCache(Base):
    """장소 캐시 테이블"""
    __tablename__ = "places_cache"
    
    place_id = Column(String(100), primary_key=True)
    name = Column(String(200))
    address = Column(String(500))
    category = Column(String(100))
    lat = Column(DOUBLE_PRECISION)
    lng = Column(DOUBLE_PRECISION)
    keto_score = Column(Integer)
    last_seen_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Message(Base):
    """대화 로그 테이블"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True))
    user_id = Column(UUID(as_uuid=True))
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text)
    tool_calls = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Plan(Base):
    """캘린더/플랜 테이블"""
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    slot = Column(String(20), nullable=False)  # breakfast|lunch|dinner|snack
    type = Column(String(20), nullable=False)  # recipe|place
    ref_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    location = Column(JSONB)  # {name, address}
    macros = Column(JSONB)    # {kcal, carb, protein, fat}
    notes = Column(Text)
    status = Column(String(20), nullable=False, default='planned')  # planned|done|skipped
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 제약 조건: 사용자별 날짜/슬롯 유니크
    __table_args__ = (
        UniqueConstraint('user_id', 'date', 'slot', name='uniq_plan_user_date_slot'),
    )
    
    # 관계
    user = relationship("User", back_populates="plans")

class Weight(Base):
    """체중 기록 테이블"""
    __tablename__ = "weights"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    date = Column(Date, primary_key=True)
    weight_kg = Column(DOUBLE_PRECISION)
    
    # 관계
    user = relationship("User", back_populates="weights")
