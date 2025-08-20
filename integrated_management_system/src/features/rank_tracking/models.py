"""
순위 추적 데이터 모델 및 설정
DTOs, 엔티티, 상수/Enum, DDL/간단 레포 헬퍼
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.foundation.db import get_db
from src.foundation.logging import get_logger

logger = get_logger("features.rank_tracking.models")


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


@dataclass
class RankTrackingConfig:
    """순위 추적 설정"""
    
    # 순위 확인 설정
    max_rank_pages: int = 10              # 최대 검색 페이지 (1000위까지)
    rank_check_interval: float = 2.0      # 순위 확인 간 지연시간 (초)
    max_workers: int = 3                  # 병렬 처리 최대 워커 수
    
    # 키워드 분석 설정  
    category_sample_size: int = 40        # 카테고리 분석 샘플 수
    auto_update_volume: bool = True       # 월검색량 자동 업데이트
    
    # UI 설정
    auto_refresh_interval: int = 300      # 자동 새로고침 간격 (초, 0=비활성화)
    show_rank_trend: bool = True          # 순위 변화 추이 표시
    
    # 알림 설정
    rank_change_threshold: int = 5        # 순위 변화 알림 임계값
    enable_notifications: bool = False    # 알림 활성화
    
    def __post_init__(self):
        """설정 유효성 검사"""
        if self.max_rank_pages < 1:
            self.max_rank_pages = 1
        elif self.max_rank_pages > 10:
            self.max_rank_pages = 10
        
        if self.rank_check_interval < 1.0:
            self.rank_check_interval = 1.0
        
        if self.max_workers < 1:
            self.max_workers = 1
        elif self.max_workers > 5:
            self.max_workers = 5
        
        if self.category_sample_size < 10:
            self.category_sample_size = 10
        elif self.category_sample_size > 100:
            self.category_sample_size = 100


# 기본 설정 인스턴스
default_config = RankTrackingConfig()


# === DDL 및 레포 헬퍼 === 
class RankTrackingRepository:
    """순위 추적 DB 헬퍼 클래스"""
    
    def __init__(self):
        self.db = get_db()
    
    def create_tables(self) -> bool:
        """테이블 생성"""
        try:
            self.db.execute_script("""
                CREATE TABLE IF NOT EXISTS tracking_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL UNIQUE,
                    current_name TEXT NOT NULL,
                    product_url TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    category TEXT DEFAULT '',
                    price INTEGER DEFAULT 0,
                    store_name TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    image_url TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tracking_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    monthly_volume INTEGER DEFAULT 0,
                    category TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES tracking_projects (id),
                    UNIQUE(project_id, keyword)
                );
                
                CREATE TABLE IF NOT EXISTS ranking_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL,
                    rank INTEGER,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES tracking_keywords (id)
                );
                
                CREATE TABLE IF NOT EXISTS basic_info_change_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    change_type TEXT DEFAULT 'auto',
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES tracking_projects (id)
                );
                
                CREATE TABLE IF NOT EXISTS keyword_management_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    action TEXT NOT NULL,
                    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES tracking_projects (id)
                );
            """)
            return True
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")
            return False
    
    def insert_project(self, project: TrackingProject) -> Optional[int]:
        """프로젝트 삽입"""
        try:
            result = self.db.execute_query("""
                INSERT INTO tracking_projects 
                (product_id, current_name, product_url, is_active, category, price, store_name, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project.product_id, project.current_name, project.product_url,
                project.is_active, project.category, project.price,
                project.store_name, project.description, project.image_url
            ))
            return result.lastrowid if result else None
        except Exception as e:
            logger.error(f"프로젝트 삽입 실패: {e}")
            return None
    
    def insert_keyword(self, keyword: TrackingKeyword) -> Optional[int]:
        """키워드 삽입"""
        try:
            result = self.db.execute_query("""
                INSERT INTO tracking_keywords 
                (project_id, keyword, is_active, monthly_volume, category)
                VALUES (?, ?, ?, ?, ?)
            """, (
                keyword.project_id, keyword.keyword, keyword.is_active,
                keyword.monthly_volume, keyword.category
            ))
            return result.lastrowid if result else None
        except Exception as e:
            logger.error(f"키워드 삽입 실패: {e}")
            return None
    
    def insert_ranking_history(self, history: RankingHistory) -> Optional[int]:
        """순위 이력 삽입"""
        try:
            result = self.db.execute_query("""
                INSERT INTO ranking_history (keyword_id, rank, checked_at)
                VALUES (?, ?, ?)
            """, (history.keyword_id, history.rank, history.checked_at))
            return result.lastrowid if result else None
        except Exception as e:
            logger.error(f"순위 이력 삽입 실패: {e}")
            return None


# 전역 레포지토리 인스턴스
rank_tracking_repository = RankTrackingRepository()


# === 설정 관련 함수 ===
def load_rank_tracking_config() -> RankTrackingConfig:
    """순위 추적 설정 로드 (향후 파일/DB에서 로드 가능)"""
    # TODO: 실제로는 설정 파일이나 DB에서 로드
    return default_config


def save_rank_tracking_config(config: RankTrackingConfig) -> bool:
    """순위 추적 설정 저장"""
    # TODO: 설정 파일이나 DB에 저장
    return True