"""
기본 도메인 엔티티 클래스
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class BaseEnum(Enum):
    """기본 열거형 클래스"""

    @classmethod
    def choices(cls):
        """선택지 리스트 반환"""
        return [(item.value, item.name) for item in cls]

    @classmethod
    def values(cls):
        """값 리스트 반환"""
        return [item.value for item in cls]

@dataclass
class BaseEntity:
    """기본 엔티티 클래스"""
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """초기화 후 처리"""
        if isinstance(self.id, str):
            self.id = UUID(self.id)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, BaseEnum):
                result[key] = value.value
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """딕셔너리에서 생성"""
        # 타입 변환
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])

        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))

        return cls(**data)

    def update_timestamp(self):
        """업데이트 타임스탬프 갱신"""
        self.updated_at = datetime.utcnow()

@dataclass
class ValueObject:
    """값 객체 기본 클래스"""

    def __post_init__(self):
        """값 객체 불변성 보장"""
        # 값 객체는 생성 후 수정 불가
        object.__setattr__(self, '_frozen', True)

    def __setattr__(self, name, value):
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError(f"Cannot modify immutable value object: {name}")
        super().__setattr__(name, value)

class AggregateRoot(BaseEntity):
    """애그리게이트 루트 기본 클래스"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._domain_events: list = []

    def add_domain_event(self, event):
        """도메인 이벤트 추가"""
        self._domain_events.append(event)

    def clear_domain_events(self):
        """도메인 이벤트 초기화"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    @property
    def domain_events(self):
        """도메인 이벤트 목록"""
        return self._domain_events.copy()