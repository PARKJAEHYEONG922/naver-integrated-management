"""
순위 추적 데이터 모델 및 설정
DTOs, 엔티티, 상수/Enum, DDL/간단 레포 헬퍼
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from src.foundation.db import get_db
from src.foundation.logging import get_logger

logger = get_logger("features.rank_tracking.models")


# === 상수/Enum 클래스들 ===

# 순위 관련 상수
RANK_OUT_OF_RANGE = 999  # 200위 밖 표시값
MAX_RANK_PAGES = 10      # 최대 검색 페이지 (1000위까지)
DEFAULT_SAMPLE_SIZE = 40 # 카테고리 분석 기본 샘플 수
class KeywordAction(Enum):
    """키워드 관리 액션"""
    ADDED = "added"
    DELETED = "deleted"
    UPDATED = "updated"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"


class ChangeType(Enum):
    """기본정보 변경 타입"""
    AUTO = "auto"
    MANUAL = "manual"
    SYSTEM = "system"


class RankCheckStatus(Enum):
    """랭킹 점검 상태"""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    monthly_volume: int = -1
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
    change_type: str = ChangeType.AUTO.value
    id: Optional[int] = None
    changed_at: Optional[datetime] = None


@dataclass
class KeywordManagementHistory:
    """키워드 관리 이력"""
    project_id: int
    keyword: str
    action: str  # KeywordAction.value 사용
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
class RankingCheckLog:
    """랭킹 점검 로그"""
    project_id: int
    status: str  # RankCheckStatus.value 사용
    total_keywords: int = 0
    successful_keywords: int = 0
    failed_keywords: int = 0
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0
    id: Optional[int] = None


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
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (price >= 0),
                    CHECK (length(current_name) > 0),
                    CHECK (length(product_url) > 0),
                    CHECK (is_active IN (0,1))
                );
                
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    monthly_volume INTEGER DEFAULT -1,
                    category TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    UNIQUE(project_id, keyword),
                    CHECK (monthly_volume >= -1),
                    CHECK (length(keyword) > 0),
                    CHECK (is_active IN (0,1))
                );
                
                CREATE TABLE IF NOT EXISTS ranking_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL,
                    rank_position INTEGER,
                    page_number INTEGER DEFAULT 1,
                    total_results INTEGER DEFAULT 0,
                    competitor_data TEXT DEFAULT '{}',
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES keywords (id) ON DELETE CASCADE,
                    CHECK (rank_position IS NULL OR rank_position >= 1)
                );
                
                CREATE TABLE IF NOT EXISTS basic_info_change_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    change_type TEXT DEFAULT 'auto',
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    CHECK (change_type IN ('auto','manual','system'))
                );
                
                CREATE TABLE IF NOT EXISTS keyword_management_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    action TEXT NOT NULL,
                    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    CHECK (action IN ('added','deleted','updated','activated','deactivated'))
                );
                
                CREATE TABLE IF NOT EXISTS ranking_check_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    total_keywords INTEGER DEFAULT 0,
                    successful_keywords INTEGER DEFAULT 0,
                    failed_keywords INTEGER DEFAULT 0,
                    error_message TEXT DEFAULT '',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    CHECK (status IN ('started', 'completed', 'failed', 'cancelled')),
                    CHECK (total_keywords >= 0),
                    CHECK (successful_keywords >= 0),
                    CHECK (failed_keywords >= 0)
                );
                
                -- 성능 최적화 인덱스들
                CREATE INDEX IF NOT EXISTS idx_ranking_results_keyword_time 
                    ON ranking_results(keyword_id, search_date DESC);
                
                CREATE INDEX IF NOT EXISTS idx_keywords_project_active 
                    ON keywords(project_id, is_active);
                
                CREATE INDEX IF NOT EXISTS idx_projects_active 
                    ON projects(is_active);
                
                CREATE INDEX IF NOT EXISTS idx_basic_info_change_project_time 
                    ON basic_info_change_history(project_id, changed_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_keyword_management_project_time 
                    ON keyword_management_history(project_id, action_date DESC);
                
                CREATE INDEX IF NOT EXISTS idx_ranking_check_logs_project_time 
                    ON ranking_check_logs(project_id, started_at DESC);
                """)
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")
            return False
    
    def insert_project(self, project: TrackingProject) -> Optional[int]:
        """프로젝트 삽입"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO projects 
                    (product_id, current_name, product_url, is_active, category, price, store_name, description, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project.product_id, project.current_name, project.product_url,
                    int(project.is_active), project.category, project.price,
                    project.store_name, project.description, project.image_url
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"프로젝트 삽입 실패: {e}")
            return None
    
    def insert_keyword(self, keyword: TrackingKeyword) -> Optional[int]:
        """키워드 삽입"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO keywords 
                    (project_id, keyword, is_active, monthly_volume, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    keyword.project_id, keyword.keyword, int(keyword.is_active),
                    keyword.monthly_volume, keyword.category
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"키워드 삽입 실패: {e}")
            return None
    
    def insert_ranking_history(self, history: RankingHistory) -> Optional[int]:
        """순위 이력 삽입"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ranking_results (keyword_id, rank_position, search_date)
                    VALUES (?, ?, ?)
                """, (history.keyword_id, history.rank, history.checked_at))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"순위 이력 삽입 실패: {e}")
            return None
    
    def insert_ranking_check_log(self, log: RankingCheckLog) -> Optional[int]:
        """랭킹 점검 로그 삽입"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ranking_check_logs 
                    (project_id, status, total_keywords, successful_keywords, failed_keywords, 
                     error_message, started_at, completed_at, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log.project_id, log.status, log.total_keywords, 
                    log.successful_keywords, log.failed_keywords, log.error_message,
                    log.started_at, log.completed_at, log.duration_seconds
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"랭킹 점검 로그 삽입 실패: {e}")
            return None
    
    def get_latest_rank(self, keyword_id: int) -> Optional[int]:
        """키워드의 최신 순위 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT rank_position FROM ranking_results
                    WHERE keyword_id = ?
                    ORDER BY search_date DESC
                    LIMIT 1
                """, (keyword_id,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"최신 순위 조회 실패: {e}")
            return None
    
    def get_keyword_trend(self, keyword_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        """키워드 순위 트렌드 조회 (최근 N개)"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT rank_position, search_date
                    FROM ranking_results
                    WHERE keyword_id = ?
                    ORDER BY search_date DESC
                    LIMIT ?
                """, (keyword_id, limit))
                rows = cursor.fetchall()
                return [{'rank': row[0], 'checked_at': row[1]} for row in rows]
        except Exception as e:
            logger.error(f"키워드 트렌드 조회 실패: {e}")
            return []
    
    def get_project_keywords(self, project_id: int, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """프로젝트의 키워드 목록 조회"""
        try:
            where_clause = "WHERE project_id = ?"
            params = [project_id]
            
            if is_active is not None:
                where_clause += " AND is_active = ?"
                params.append(is_active)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT id, project_id, keyword, is_active, monthly_volume, category, created_at
                    FROM keywords 
                    {where_clause}
                    ORDER BY created_at DESC
                """, tuple(params))
                
                rows = cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'project_id': row[1],
                        'keyword': row[2],
                        'is_active': row[3],
                        'monthly_volume': row[4],
                        'category': row[5],
                        'created_at': row[6]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"프로젝트 키워드 조회 실패: {e}")
            return []
    
    def get_all_projects(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """모든 프로젝트 조회"""
        try:
            where_clause = ""
            params = []
            
            if is_active is not None:
                where_clause = "WHERE is_active = ?"
                params.append(is_active)
            
            query = f"""
                SELECT id, product_id, current_name, product_url, is_active, 
                       category, price, store_name, description, image_url, created_at
                FROM projects 
                {where_clause}
                ORDER BY created_at DESC
            """
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                
                return [
                    {
                        'id': row[0],
                        'product_id': row[1],
                        'current_name': row[2],
                        'product_url': row[3],
                        'is_active': row[4],
                        'category': row[5],
                        'price': row[6],
                        'store_name': row[7],
                        'description': row[8],
                        'image_url': row[9],
                        'created_at': row[10]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"모든 프로젝트 조회 실패: {e}")
            return []
    
    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """프로젝트 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, product_id, current_name, product_url, is_active, 
                           category, price, store_name, description, image_url, created_at
                    FROM projects 
                    WHERE id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'product_id': row[1],
                        'current_name': row[2],
                        'product_url': row[3],
                        'is_active': row[4],
                        'category': row[5],
                        'price': row[6],
                        'store_name': row[7],
                        'description': row[8],
                        'image_url': row[9],
                        'created_at': row[10]
                    }
                return None
        except Exception as e:
            logger.error(f"프로젝트 조회 실패: {e}")
            return None
    
    def get_project_by_product_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """상품 ID로 프로젝트 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, product_id, current_name, product_url, is_active, 
                           category, price, store_name, description, image_url, created_at
                    FROM projects 
                    WHERE product_id = ?
                """, (product_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'product_id': row[1],
                        'current_name': row[2],
                        'product_url': row[3],
                        'is_active': row[4],
                        'category': row[5],
                        'price': row[6],
                        'store_name': row[7],
                        'description': row[8],
                        'image_url': row[9],
                        'created_at': row[10]
                    }
                return None
        except Exception as e:
            logger.error(f"상품 ID로 프로젝트 조회 실패: {e}")
            return None
    
    def update_keyword(self, keyword_id: int, **kwargs) -> bool:
        """키워드 업데이트"""
        try:
            # 업데이트할 필드들 구성
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in ['keyword', 'is_active', 'monthly_volume', 'category']:
                    update_fields.append(f"{field} = ?")
                    # BOOLEAN 필드는 int로 변환
                    if field == 'is_active':
                        params.append(int(value))
                    else:
                        params.append(value)
            
            if not update_fields:
                return True
            
            params.append(keyword_id)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE keywords 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, tuple(params))
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"키워드 업데이트 실패: {e}")
            return False
    
    def delete_keyword(self, keyword_id: int) -> bool:
        """키워드 삭제 (CASCADE로 인해 관련 순위 이력도 자동 삭제)"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM keywords WHERE id = ?
                """, (keyword_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"키워드 삭제 실패: {e}")
            return False
    
    def delete_project(self, project_id: int) -> bool:
        """프로젝트 삭제 (CASCADE로 인해 모든 관련 데이터 자동 삭제)"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM projects WHERE id = ?
                """, (project_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"프로젝트 삭제 실패: {e}")
            return False
    
    def start_rank_check_log(self, project_id: int, total_keywords: int) -> Optional[int]:
        """랭킹 점검 시작 로그"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ranking_check_logs (project_id, status, total_keywords, started_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (project_id, RankCheckStatus.STARTED.value, total_keywords))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"랭킹 점검 시작 로그 실패: {e}")
            return None

    def finish_rank_check_log(self, log_id: int, *, success: bool,
                              successful_keywords: int, failed_keywords: int,
                              error_message: str = "") -> bool:
        """랭킹 점검 완료 로그"""
        try:
            status = RankCheckStatus.COMPLETED.value if success else RankCheckStatus.FAILED.value
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ranking_check_logs
                    SET status = ?, successful_keywords = ?, failed_keywords = ?,
                        error_message = ?, completed_at = CURRENT_TIMESTAMP,
                        duration_seconds = CAST((strftime('%s', CURRENT_TIMESTAMP) - strftime('%s', started_at)) AS INTEGER)
                    WHERE id = ?
                """, (status, successful_keywords, failed_keywords, error_message, log_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"랭킹 점검 완료 로그 실패: {e}")
            return False
    
    def add_keyword(self, project_id: int, keyword: str) -> int:
        """키워드 추가"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO keywords (project_id, keyword, is_active)
                    VALUES (?, ?, 1)
                """, (project_id, keyword))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"키워드 추가 실패: {e}")
            return 0
    
    def update_keyword_volume_and_category(self, project_id: int, keyword: str, monthly_volume: int, category: str) -> bool:
        """키워드 볼륨 및 카테고리 업데이트"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE keywords 
                    SET monthly_volume = ?, category = ?
                    WHERE project_id = ? AND keyword = ?
                """, (monthly_volume, category, project_id, keyword))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"키워드 볼륨/카테고리 업데이트 실패: {e}")
            return False
    
    def delete_keyword_by_text(self, project_id: int, keyword: str) -> bool:
        """키워드 텍스트로 삭제"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM keywords 
                    WHERE project_id = ? AND keyword = ?
                """, (project_id, keyword))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"키워드 삭제 실패: {e}")
            return False
    
    def delete_keyword_by_id(self, keyword_id: int) -> bool:
        """키워드 ID로 삭제"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM keywords WHERE id = ?
                """, (keyword_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"키워드 삭제 실패: {e}")
            return False
    
    def get_project_ranking_overview(self, project_id: int) -> dict:
        """프로젝트 순위 현황 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 최근 날짜들 조회 (시간 포함)
                cursor.execute("""
                    SELECT DISTINCT r.search_date as date
                    FROM ranking_results r
                    JOIN keywords k ON r.keyword_id = k.id
                    WHERE k.project_id = ?
                    ORDER BY date DESC
                    LIMIT 10
                """, (project_id,))
                
                dates = [row[0] for row in cursor.fetchall()]
                
                # 키워드별 순위 데이터 조회 (시간 포함)
                cursor.execute("""
                    SELECT k.keyword, r.rank_position, r.search_date as date
                    FROM ranking_results r
                    JOIN keywords k ON r.keyword_id = k.id
                    WHERE k.project_id = ?
                    ORDER BY k.keyword, r.search_date DESC
                """, (project_id,))
                
                # 키워드별로 그룹화
                keywords = {}
                for row in cursor.fetchall():
                    keyword, rank, date = row
                    if keyword not in keywords:
                        keywords[keyword] = {}
                    keywords[keyword][date] = rank
                
                return {
                    'dates': dates,
                    'keywords': keywords
                }
        except Exception as e:
            logger.error(f"순위 현황 조회 실패: {e}")
            return {'dates': [], 'keywords': {}}
    
    def add_keyword_management_history(self, project_id: int, keyword: str, action: str) -> bool:
        """키워드 관리 이력 추가"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO keyword_management_history (project_id, keyword, action)
                    VALUES (?, ?, ?)
                """, (project_id, keyword, action))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"키워드 관리 이력 추가 실패: {e}")
            return False
    
    def get_keyword_management_history(self, project_id: int) -> List[Dict[str, Any]]:
        """키워드 관리 이력 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT keyword, action, action_date
                    FROM keyword_management_history
                    WHERE project_id = ?
                    ORDER BY action_date DESC
                """, (project_id,))
                
                return [
                    {
                        'keyword': row[0],
                        'action': row[1],
                        'action_time': row[2]  # UI에서 사용하는 키명으로 변경
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"키워드 관리 이력 조회 실패: {e}")
            return []
    
    def get_basic_info_change_history(self, project_id: int) -> List[Dict[str, Any]]:
        """기본정보 변경 이력 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT field_name, old_value, new_value, change_type, changed_at
                    FROM basic_info_change_history
                    WHERE project_id = ?
                    ORDER BY changed_at DESC
                """, (project_id,))
                
                return [
                    {
                        'field_name': row[0],
                        'old_value': row[1],
                        'new_value': row[2],
                        'change_type': row[3],
                        'change_time': row[4]  # UI에서 사용하는 키명으로 변경
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"기본정보 변경 이력 조회 실패: {e}")
            return []
    
    def get_ranking_history_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        """프로젝트 순위 이력 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT k.keyword, r.rank_position, r.search_date
                    FROM ranking_results r
                    JOIN keywords k ON r.keyword_id = k.id
                    WHERE k.project_id = ?
                    ORDER BY r.search_date DESC
                """, (project_id,))
                
                return [
                    {
                        'keyword': row[0],
                        'rank': row[1],
                        'checked_at': row[2]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"프로젝트 순위 이력 조회 실패: {e}")
            return []
    
    def get_ranking_history(self, keyword_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """키워드 순위 이력 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT rank_position, search_date, total_results
                    FROM ranking_results
                    WHERE keyword_id = ?
                    ORDER BY search_date DESC
                    LIMIT ?
                """, (keyword_id, limit))
                
                return [
                    {
                        'rank': row[0],
                        'checked_at': row[1],
                        'total_results': row[2]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"키워드 순위 이력 조회 실패: {e}")
            return []
    
    def get_keyword_ranking_history(self, project_id: int, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """키워드 텍스트로 순위 이력 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.rank_position, r.search_date, r.total_results
                    FROM ranking_results r
                    JOIN keywords k ON r.keyword_id = k.id
                    WHERE k.project_id = ? AND k.keyword = ?
                    ORDER BY r.search_date DESC
                    LIMIT ?
                """, (project_id, keyword, limit))
                
                return [
                    {
                        'keyword': keyword,
                        'rank': row[0],
                        'rank_position': row[0],
                        'created_at': row[1],
                        'search_date': row[1],
                        'total_results': row[2]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"키워드 순위 이력 조회 실패: {e}")
            return []
    
    def save_ranking_result(self, keyword_id: int, rank_position: int, page_number: int = 1, 
                           total_results: int = 0, competitor_data: dict = None, 
                           search_date: str = None) -> int:
        """순위 결과 저장"""
        try:
            import json
            competitor_json = json.dumps(competitor_data or {})
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if search_date:
                    cursor.execute("""
                        INSERT INTO ranking_results 
                        (keyword_id, rank_position, page_number, total_results, competitor_data, search_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (keyword_id, rank_position, page_number, total_results, competitor_json, search_date))
                else:
                    cursor.execute("""
                        INSERT INTO ranking_results 
                        (keyword_id, rank_position, page_number, total_results, competitor_data)
                        VALUES (?, ?, ?, ?, ?)
                    """, (keyword_id, rank_position, page_number, total_results, competitor_json))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"순위 결과 저장 실패: {e}")
            return 0
    
    def get_keywords(self, project_id: int) -> List[Dict[str, Any]]:
        """프로젝트 키워드 목록 조회 (service.py 호환)"""
        return self.get_project_keywords(project_id)
    
    def update_keyword_by_text(self, project_id: int, keyword: str, **kwargs) -> bool:
        """키워드 텍스트로 업데이트"""
        try:
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in ['category', 'monthly_volume']:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                return True
            
            params.extend([project_id, keyword])
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE keywords 
                    SET {', '.join(update_fields)}
                    WHERE project_id = ? AND keyword = ?
                """, tuple(params))
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"키워드 업데이트 실패: {e}")
            return False
    
    def delete_ranking_results_by_date(self, project_id: int, date_str: str) -> bool:
        """특정 날짜의 순위 결과 삭제"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM ranking_results 
                    WHERE keyword_id IN (
                        SELECT id FROM keywords WHERE project_id = ?
                    ) AND DATE(search_date) = DATE(?)
                """, (project_id, date_str))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"날짜별 순위 결과 삭제 실패: {e}")
            return False
    
    def add_basic_info_change_record(self, project_id: int, field_name: str, old_value: str, 
                                   new_value: str, is_auto: bool = True) -> bool:
        """기본정보 변경 기록 추가"""
        try:
            change_type = 'auto' if is_auto else 'manual'
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO basic_info_change_history 
                    (project_id, field_name, old_value, new_value, change_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (project_id, field_name, old_value, new_value, change_type))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"기본정보 변경 기록 추가 실패: {e}")
            return False
    
    def update_project_info(self, project_id: int, new_info: Dict[str, Any]) -> bool:
        """프로젝트 정보 업데이트"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE projects
                       SET current_name = ?,
                           price        = ?,
                           category     = ?,
                           store_name   = ?
                     WHERE id = ?
                """, (
                    new_info.get('current_name', ''),
                    int(new_info.get('price', 0) or 0),
                    new_info.get('category', ''),
                    new_info.get('store_name', ''),
                    project_id
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"프로젝트 정보 업데이트 실패: {e}")
            return False




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