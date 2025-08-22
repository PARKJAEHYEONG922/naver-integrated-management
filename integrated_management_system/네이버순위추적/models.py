"""
순위 추적 데이터 모델 (단순한 dataclass)
SQLAlchemy ORM 제거하고 원본 방식의 단순한 모델들
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TrackingProject:
    """추적 프로젝트 모델"""
    product_id: str
    current_name: str
    product_url: str
    is_active: bool = True
    category: str = ""
    price: int = 0
    store_name: str = ""
    description: str = ""
    image_url: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class TrackingKeyword:
    """추적 키워드 모델"""
    project_id: int
    keyword: str
    is_active: bool = True
    monthly_volume: int = 0
    category: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class RankingResult:
    """순위 검색 결과 DTO"""
    keyword: str = ""
    product_id: str = ""
    rank: Optional[int] = None
    success: bool = False
    total_results: int = 0
    error_message: Optional[str] = None
    keyword_id: Optional[int] = None
    checked_at: Optional[datetime] = None


@dataclass  
class ProductInfo:
    """상품 정보 DTO"""
    product_id: str = ""
    name: str = ""
    price: int = 0
    category: str = ""
    store_name: str = ""
    description: str = ""
    image_url: str = ""
    url: str = ""


@dataclass
class BasicInfoChangeHistory:
    """기본정보 변경 이력"""
    project_id: int
    field_name: str
    old_value: Optional[str]
    new_value: str
    change_type: str = "auto"
    id: Optional[int] = None
    changed_at: Optional[datetime] = None


@dataclass
class KeywordManagementHistory:
    """키워드 관리 이력"""
    project_id: int
    keyword: str
    action: str
    id: Optional[int] = None
    action_date: Optional[datetime] = None


@dataclass
class RankingHistory:
    """순위 기록"""
    keyword_id: int
    rank: Optional[int]
    id: Optional[int] = None
    checked_at: Optional[datetime] = None