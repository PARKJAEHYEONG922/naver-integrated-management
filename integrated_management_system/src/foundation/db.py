"""
공용 SQLite3 데이터베이스 헬퍼
- 모든 모듈이 사용하는 단일 DB 헬퍼
- 단순한 SQLite3 직접 사용 방식
- API 설정, 키워드 분석, 순위 추적 모든 데이터 통합 관리
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json
from contextlib import contextmanager

from .logging import get_logger

logger = get_logger("foundation.db")


class CommonDB:
    """공용 SQLite3 데이터베이스 헬퍼"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # 기본 DB 경로 설정 - integrated_management_system 내부의 data 폴더 (절대 경로)
            current_file = Path(__file__).resolve()  # 현재 파일의 절대 경로
            project_root = current_file.parent.parent.parent  # src/foundation/db.py -> integrated_management_system
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "app.db"
        
        self.db_path = db_path
        self.init_database()
        logger.info(f"공용 DB 초기화 완료: {db_path}")
    
    @contextmanager
    def get_connection(self):
        """DB 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            conn.execute("PRAGMA foreign_keys=ON;")  # SQLite 외래키 제약 활성화
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"DB 연결 오류: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """모든 테이블 초기화"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # API 설정 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL UNIQUE,
                    config_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            
            # 순위 추적 - 프로젝트 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL UNIQUE,
                    current_name TEXT NOT NULL,
                    product_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    category TEXT DEFAULT '',
                    price INTEGER DEFAULT 0,
                    store_name TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    image_url TEXT DEFAULT ''
                )
            """)
            
            # 순위 추적 - 키워드 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    category TEXT DEFAULT '',
                    monthly_volume INTEGER DEFAULT -1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    UNIQUE(project_id, keyword)
                )
            """)
            
            # 순위 추적 - 순위 결과 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ranking_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL,
                    rank_position INTEGER NOT NULL,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    page_number INTEGER DEFAULT 1,
                    total_results INTEGER DEFAULT 0,
                    competitor_data TEXT DEFAULT '{}',
                    FOREIGN KEY (keyword_id) REFERENCES keywords (id) ON DELETE CASCADE
                )
            """)
            
            # 기본정보 변경 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS basic_info_change_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    change_type TEXT DEFAULT 'auto',
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            """)
            
            # 키워드 관리 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_management_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    action TEXT NOT NULL,
                    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            """)
            
            # 카페 추출 작업 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cafe_extraction_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    cafe_name TEXT NOT NULL,
                    cafe_url TEXT NOT NULL,
                    board_name TEXT NOT NULL,
                    board_url TEXT NOT NULL,
                    start_page INTEGER DEFAULT 1,
                    end_page INTEGER DEFAULT 10,
                    status TEXT DEFAULT 'pending',
                    current_page INTEGER DEFAULT 1,
                    total_extracted INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    error_message TEXT DEFAULT ''
                )
            """)
            
            # 카페 추출 결과 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cafe_extraction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    article_count INTEGER DEFAULT 1,
                    article_url TEXT DEFAULT '',
                    article_title TEXT DEFAULT '',
                    article_date TEXT DEFAULT '',
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES cafe_extraction_tasks (task_id) ON DELETE CASCADE
                )
            """)
            
            # 카페 추출 히스토리 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cafe_extraction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES cafe_extraction_tasks (task_id) ON DELETE CASCADE
                )
            """)
            
            # 기존 테이블에 누락된 컬럼 추가 (ALTER TABLE)
            try:
                # keywords 테이블에 category, monthly_volume 컬럼 추가
                cursor.execute("ALTER TABLE keywords ADD COLUMN category TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # 컬럼이 이미 존재함
            
            try:
                cursor.execute("ALTER TABLE keywords ADD COLUMN monthly_volume INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # 컬럼이 이미 존재함
            
            # 인덱스 생성
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_product_id ON projects (product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_project_id ON keywords (project_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ranking_results_keyword_id ON ranking_results (keyword_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cafe_extraction_tasks_task_id ON cafe_extraction_tasks (task_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cafe_extraction_results_task_id ON cafe_extraction_results (task_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cafe_extraction_history_task_id ON cafe_extraction_history (task_id)")
            
            # 파워링크 분석 관련 테이블들
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS powerlink_analysis_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    keyword_count INTEGER NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS powerlink_keyword_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    pc_search_volume INTEGER,
                    mobile_search_volume INTEGER,
                    pc_clicks REAL,
                    pc_ctr REAL,
                    pc_first_page_positions INTEGER,
                    pc_first_position_bid INTEGER,
                    pc_min_exposure_bid INTEGER,
                    pc_recommendation_rank INTEGER,
                    mobile_clicks REAL,
                    mobile_ctr REAL,
                    mobile_first_page_positions INTEGER,
                    mobile_first_position_bid INTEGER,
                    mobile_min_exposure_bid INTEGER,
                    mobile_recommendation_rank INTEGER,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES powerlink_analysis_sessions (id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS powerlink_bid_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_result_id INTEGER NOT NULL,
                    device_type TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    bid_price INTEGER NOT NULL,
                    FOREIGN KEY (keyword_result_id) REFERENCES powerlink_keyword_results (id) ON DELETE CASCADE
                )
            """)
            
            # 파워링크 분석 인덱스
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_powerlink_sessions_created_at ON powerlink_analysis_sessions (created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_powerlink_keyword_results_session_id ON powerlink_keyword_results (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_powerlink_bid_positions_keyword_result_id ON powerlink_bid_positions (keyword_result_id)")
            
            # 파워링크 테이블 마이그레이션 (기존 monthly_search_volume을 PC/Mobile로 분리)
            self._migrate_powerlink_search_volumes(cursor)
            
            conn.commit()
            logger.debug("데이터베이스 테이블 및 인덱스 초기화 완료")
    
    def _migrate_powerlink_search_volumes(self, cursor):
        """파워링크 테이블 마이그레이션: monthly_search_volume을 PC/Mobile로 분리"""
        try:
            # 기존 monthly_search_volume 컬럼이 있는지 확인
            cursor.execute("PRAGMA table_info(powerlink_keyword_results)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            # PC/Mobile 검색량 컬럼이 없으면 추가
            if 'pc_search_volume' not in columns:
                cursor.execute("ALTER TABLE powerlink_keyword_results ADD COLUMN pc_search_volume INTEGER")
                logger.debug("PC 검색량 컬럼 추가 완료")
                
            if 'mobile_search_volume' not in columns:
                cursor.execute("ALTER TABLE powerlink_keyword_results ADD COLUMN mobile_search_volume INTEGER")
                logger.debug("Mobile 검색량 컬럼 추가 완료")
            
            # 기존 monthly_search_volume 데이터가 있다면 PC/Mobile로 분배 (50:50 비율)
            if 'monthly_search_volume' in columns:
                cursor.execute("""
                    UPDATE powerlink_keyword_results 
                    SET pc_search_volume = COALESCE(monthly_search_volume, 0) / 2,
                        mobile_search_volume = COALESCE(monthly_search_volume, 0) / 2
                    WHERE pc_search_volume IS NULL OR mobile_search_volume IS NULL
                """)
                rows_updated = cursor.rowcount
                if rows_updated > 0:
                    logger.debug(f"기존 검색량 데이터 {rows_updated}건을 PC/Mobile로 분리 완료")
                
                # 기존 컬럼 제거는 SQLite에서 복잡하므로 일단 그대로 두기
                # (향후 데이터 마이그레이션 시 필요하면 처리)
                
        except Exception as e:
            logger.warning(f"파워링크 검색량 마이그레이션 실패 (무시 가능): {e}")
    
    # ========== API 설정 관련 메서드 ==========
    
    def save_api_config(self, service_name: str, config_data: Dict[str, Any]) -> bool:
        """API 설정 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                config_json = json.dumps(config_data)
                current_time = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO api_configs 
                    (service_name, config_data, updated_at)
                    VALUES (?, ?, ?)
                """, (service_name, config_json, current_time))
                
                conn.commit()
                logger.debug(f"API 설정 저장: {service_name}")
                return True
                
        except Exception as e:
            logger.error(f"API 설정 저장 실패: {service_name}: {e}")
            return False
    
    def get_api_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """API 설정 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT config_data FROM api_configs WHERE service_name = ?
                """, (service_name,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row['config_data'])
                return None
                
        except Exception as e:
            logger.error(f"API 설정 조회 실패: {service_name}: {e}")
            return None
    
    def list_api_configs(self) -> List[Dict[str, Any]]:
        """모든 API 설정 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT service_name, created_at, updated_at 
                FROM api_configs 
                ORDER BY service_name
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== 프로젝트 관련 메서드 ==========
    
    def create_project(self, project_data: Dict[str, Any]) -> int:
        """프로젝트 생성"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO projects (
                    product_id, current_name, product_url, category, 
                    price, store_name, description, image_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data['product_id'],
                project_data['current_name'],
                project_data['product_url'],
                project_data.get('category', ''),
                project_data.get('price', 0),
                project_data.get('store_name', ''),
                project_data.get('description', ''),
                project_data.get('image_url', '')
            ))
            
            conn.commit()
            project_id = cursor.lastrowid
            logger.debug(f"프로젝트 생성: {project_id}")
            return project_id
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """프로젝트 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM projects WHERE id = ? AND is_active = 1
            """, (project_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_projects(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """프로젝트 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute("""
                    SELECT * FROM projects WHERE is_active = 1 ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT * FROM projects ORDER BY created_at DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_project(self, project_id: int, updates: Dict[str, Any]) -> bool:
        """프로젝트 업데이트"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 업데이트할 필드와 값 준비
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key != 'id':  # ID는 업데이트하지 않음
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            values.append(project_id)  # WHERE 절용
            
            query = f"""
                UPDATE projects 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.debug(f"프로젝트 업데이트: {project_id}")
            return success
    
    def delete_project(self, project_id: int) -> bool:
        """프로젝트 완전 삭제 (관련 데이터 모두 삭제)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 1. 순위 결과 삭제 (키워드 ID 기반)
                cursor.execute("""
                    DELETE FROM ranking_results 
                    WHERE keyword_id IN (
                        SELECT id FROM keywords WHERE project_id = ?
                    )
                """, (project_id,))
                
                # 2. 키워드 삭제
                cursor.execute("DELETE FROM keywords WHERE project_id = ?", (project_id,))
                
                # 3. 프로젝트 삭제
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"프로젝트 완전 삭제 완료: ID {project_id}")
                    return True
                else:
                    logger.warning(f"삭제할 프로젝트를 찾을 수 없음: ID {project_id}")
                    return False
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"프로젝트 삭제 실패: {e}")
                return False
    
    # ========== 키워드 관련 메서드 ==========
    
    def add_keyword(self, project_id: int, keyword: str, category: str = "", monthly_volume: int = -1) -> int:
        """키워드 추가 (중복 체크 포함)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 중복 체크 (단순함)
            cursor.execute("""
                SELECT id FROM keywords 
                WHERE project_id = ? AND LOWER(TRIM(keyword)) = LOWER(TRIM(?))
            """, (project_id, keyword))
            
            existing = cursor.fetchone()
            if existing:
                logger.debug(f"키워드 중복 건너뛰기: {keyword} (프로젝트 {project_id})")
                return 0  # 중복일 때는 0 반환
            
            # 새 키워드 추가
            cursor.execute("""
                INSERT INTO keywords (project_id, keyword, category, monthly_volume)
                VALUES (?, ?, ?, ?)
            """, (project_id, keyword, category, monthly_volume))
            keyword_id = cursor.lastrowid
            
            conn.commit()
            if keyword_id:
                logger.debug(f"키워드 추가: {keyword} (프로젝트 {project_id})")
                    
            return keyword_id
    
    def get_keywords(self, project_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """프로젝트의 키워드 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM keywords 
                WHERE project_id = ? 
                ORDER BY keyword
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_keyword_info(self, keyword_id: int, category: str = None, monthly_volume: int = None) -> bool:
        """키워드 정보 업데이트"""
        updates = {}
        if category is not None:
            updates['category'] = category
        if monthly_volume is not None:
            updates['monthly_volume'] = monthly_volume
        
        if not updates:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(keyword_id)
            
            query = f"""
                UPDATE keywords 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def update_keyword_by_text(self, project_id: int, keyword_text: str, category: str = None, monthly_volume: int = None) -> bool:
        """키워드 텍스트로 정보 업데이트"""
        updates = {}
        if category is not None:
            updates['category'] = category
        if monthly_volume is not None:
            updates['monthly_volume'] = monthly_volume
        
        if not updates:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.extend([project_id, keyword_text])
            
            query = f"""
                UPDATE keywords 
                SET {', '.join(set_clauses)}
                WHERE project_id = ? AND keyword = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def update_keyword_volume_and_category(self, project_id: int, keyword_text: str, monthly_volume: int, category: str) -> bool:
        """키워드의 월검색량과 카테고리를 동시에 업데이트 (원본 호환성)"""
        return self.update_keyword_by_text(project_id, keyword_text, category=category, monthly_volume=monthly_volume)
    
    def deactivate_keyword(self, keyword_id: int) -> bool:
        """키워드 비활성화"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE keywords SET is_active = 0 WHERE id = ?
            """, (keyword_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_keyword_by_text(self, project_id: int, keyword_text: str) -> bool:
        """키워드 텍스트로 키워드 완전 삭제"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 먼저 키워드 ID 찾기
            cursor.execute("""
                SELECT id FROM keywords 
                WHERE project_id = ? AND keyword = ?
            """, (project_id, keyword_text))
            
            keyword_row = cursor.fetchone()
            if not keyword_row:
                return False
            
            keyword_id = keyword_row[0]
            
            # 관련 순위 결과 먼저 삭제 (외래키 제약 때문)
            cursor.execute("DELETE FROM ranking_results WHERE keyword_id = ?", (keyword_id,))
            
            # 키워드 완전 삭제
            cursor.execute("""
                DELETE FROM keywords 
                WHERE project_id = ? AND keyword = ?
            """, (project_id, keyword_text))
            
            conn.commit()
            success = cursor.rowcount > 0
            
            if success:
                logger.info(f"키워드 완전 삭제: {keyword_text} (프로젝트 {project_id})")
                    
            return success
    
    def add_keyword_management_history(self, project_id: int, keyword: str, action: str):
        """키워드 관리 이력 추가"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO keyword_management_history (project_id, keyword, action)
                VALUES (?, ?, ?)
            """, (project_id, keyword, action))
            
            conn.commit()
    
    # ========== 순위 추적 관련 메서드 ==========
    
    def save_ranking_result(self, keyword_id: int, rank_position: int, page_number: int = 1, 
                          total_results: int = 0, competitor_data: Dict[str, Any] = None, search_date: str = None) -> int:
        """순위 결과 저장"""
        from datetime import datetime
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 전달받은 search_date가 있으면 사용, 없으면 현재 시간 생성
            if search_date:
                current_time = search_date
            else:
                # 현재 한국 시간으로 타임스탬프 생성 (UTC +9 적용)
                import pytz
                korea_tz = pytz.timezone('Asia/Seoul')
                current_time = datetime.now(korea_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO ranking_results (
                    keyword_id, rank_position, page_number, total_results, competitor_data, search_date
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                keyword_id, 
                rank_position, 
                page_number, 
                total_results,
                json.dumps(competitor_data or {}),
                current_time
            ))
            
            conn.commit()
            result_id = cursor.lastrowid
            logger.debug(f"순위 결과 저장: 키워드 {keyword_id}, 순위 {rank_position}, 시간 {current_time}")
            return result_id
    
    def get_latest_rankings(self, project_id: int) -> List[Dict[str, Any]]:
        """프로젝트의 최신 순위 결과"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT k.keyword, k.category, k.monthly_volume, 
                       r.rank_position, r.search_date, r.total_results
                FROM keywords k
                LEFT JOIN ranking_results r ON k.id = r.keyword_id AND r.id = (
                    SELECT id FROM ranking_results 
                    WHERE keyword_id = k.id 
                    ORDER BY search_date DESC 
                    LIMIT 1
                )
                WHERE k.project_id = ?
                ORDER BY k.keyword
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_ranking_history(self, keyword_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        """키워드의 순위 변화 이력"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT rank_position, search_date, total_results
                FROM ranking_results
                WHERE keyword_id = ?
                ORDER BY search_date DESC
                LIMIT ?
            """, (keyword_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_project_ranking_overview(self, project_id: int, limit: int = 10) -> dict:
        """프로젝트의 순위 현황 조회 (원본과 동일한 방식)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 최근 검색 시간들 조회 (각 실행별로 구분)
                cursor.execute("""
                    SELECT DISTINCT r.search_date
                    FROM ranking_results r
                    JOIN keywords k ON r.keyword_id = k.id
                    WHERE k.project_id = ?
                    ORDER BY r.search_date DESC
                    LIMIT ?
                """, (project_id, limit))
                
                dates = [row[0] for row in cursor.fetchall()]
                
                # 각 키워드별 날짜별 순위 조회
                if dates:
                    date_conditions = ','.join('?' * len(dates))
                    cursor.execute(f"""
                        SELECT 
                            k.id,
                            k.keyword,
                            k.category,
                            k.monthly_volume,
                            k.is_active,
                            r.rank_position,
                            r.search_date
                        FROM keywords k
                        LEFT JOIN ranking_results r ON k.id = r.keyword_id
                        WHERE k.project_id = ? AND (
                            r.search_date IS NULL OR 
                            r.search_date IN ({date_conditions})
                        )
                        ORDER BY k.keyword, r.search_date DESC
                    """, (project_id, *dates))
                else:
                    cursor.execute("""
                        SELECT 
                            k.id,
                            k.keyword,
                            k.category,
                            k.monthly_volume,
                            k.is_active,
                            NULL as rank_position,
                            NULL as search_date
                        FROM keywords k
                        WHERE k.project_id = ?
                        ORDER BY k.keyword
                    """, (project_id,))
                
                # 데이터 구조화
                keywords_data = {}
                for row in cursor.fetchall():
                    keyword_id, keyword, category, monthly_volume, is_active, rank_position, search_date = row
                    
                    if keyword_id not in keywords_data:
                        keywords_data[keyword_id] = {
                            'keyword': keyword,
                            'category': category or '',
                            'monthly_volume': monthly_volume or 0,
                            'is_active': bool(is_active),
                            'rankings': {}
                        }
                    
                    if search_date and search_date in dates:
                        keywords_data[keyword_id]['rankings'][search_date] = {
                            'rank': rank_position,
                            'checked_at': search_date
                        }
                
                return {
                    'dates': dates,
                    'keywords': keywords_data
                }
                
        except Exception as e:
            logger.error(f"프로젝트 순위 현황 조회 실패: {e}")
            return {'dates': [], 'keywords': {}}
    
    def delete_ranking_results_by_date(self, project_id: int, date_str: str) -> bool:
        """특정 날짜의 순위 결과 삭제 (원본과 동일한 방식)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 해당 프로젝트의 키워드 ID들 조회
                cursor.execute("""
                    SELECT id FROM keywords WHERE project_id = ?
                """, (project_id,))
                keyword_ids = [row[0] for row in cursor.fetchall()]
                
                if not keyword_ids:
                    return False
                
                # 실제 저장된 날짜들을 확인해보고 패턴 매칭으로 삭제
                cursor.execute("""
                    SELECT DISTINCT r.search_date
                    FROM ranking_results r
                    JOIN keywords k ON r.keyword_id = k.id
                    WHERE k.project_id = ?
                    ORDER BY r.search_date DESC
                    LIMIT 20
                """, (project_id,))
                stored_dates = [row[0] for row in cursor.fetchall()]
                logger.info(f"저장된 날짜들: {stored_dates}")
                logger.info(f"삭제 대상 날짜: {date_str}")
                
                # 정확한 매치를 시도하고, 실패하면 날짜만으로 매치
                placeholders = ','.join(['?'] * len(keyword_ids))
                
                # 먼저 정확한 매치 시도
                cursor.execute(f"""
                    DELETE FROM ranking_results 
                    WHERE keyword_id IN ({placeholders}) 
                    AND search_date = ?
                """, (*keyword_ids, date_str))
                
                deleted_count = cursor.rowcount
                
                # 정확한 매치가 실패하면 날짜 부분만으로 매치 (LIKE 사용)
                if deleted_count == 0:
                    logger.info(f"정확한 매치 실패, LIKE 패턴으로 재시도: {date_str[:10]}%")
                    cursor.execute(f"""
                        DELETE FROM ranking_results 
                        WHERE keyword_id IN ({placeholders}) 
                        AND search_date LIKE ?
                    """, (*keyword_ids, f"{date_str[:10]}%"))
                    deleted_count = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"날짜별 순위 데이터 삭제: 프로젝트 {project_id}, 날짜 {date_str}, 삭제 수 {deleted_count}")
                return deleted_count > 0
                    
        except Exception as e:
            logger.error(f"날짜별 순위 데이터 삭제 실패: {e}")
            return False
    
    # ========== Rank Tracking 호환성 메서드들 ==========
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """모든 프로젝트 조회 (rank_tracking 호환)"""
        return self.list_projects(active_only=True)
    
    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """프로젝트 ID로 조회 (rank_tracking 호환)"""
        return self.get_project(project_id)
    
    def get_project_by_product_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """상품 ID로 프로젝트 조회 (rank_tracking 호환)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM projects WHERE product_id = ?
            """, (product_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_project_keywords(self, project_id: int) -> List[Dict[str, Any]]:
        """프로젝트 키워드 목록 (rank_tracking 호환)"""
        return self.get_keywords(project_id, active_only=True)
    
    def get_keyword_management_history(self, project_id: int) -> List[Dict[str, Any]]:
        """키워드 관리 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT keyword, action, action_date as action_time
                FROM keyword_management_history
                WHERE project_id = ?
                ORDER BY action_date DESC
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_basic_info_change_history(self, project_id: int) -> List[Dict[str, Any]]:
        """기본정보 변경 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT field_name, old_value, new_value, changed_at as change_time
                FROM basic_info_change_history
                WHERE project_id = ?
                ORDER BY changed_at DESC
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def add_basic_info_change_record(self, project_id: int, field_name: str, old_value: str, new_value: str):
        """기본정보 변경 이력 추가"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO basic_info_change_history (project_id, field_name, old_value, new_value)
                VALUES (?, ?, ?, ?)
            """, (project_id, field_name, old_value, new_value))
            
            conn.commit()
    
    def get_ranking_history_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        """프로젝트의 순위 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT k.keyword, r.rank_position as rank, r.total_results as result_count, r.search_date as check_time
                FROM keywords k
                JOIN ranking_results r ON k.id = r.keyword_id
                WHERE k.project_id = ?
                ORDER BY r.search_date DESC
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    
    # ========== 카페 추출 관련 메서드 ==========
    
    def create_cafe_extraction_task(self, task_data: Dict[str, Any]) -> str:
        """카페 추출 작업 생성"""
        import uuid
        from datetime import datetime
        
        # task_id가 없으면 고유 ID 생성
        task_id = task_data.get('task_id', str(uuid.uuid4()))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cafe_extraction_tasks (
                    task_id, cafe_name, cafe_url, board_name, board_url,
                    start_page, end_page, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task_data.get('cafe_name', ''),
                task_data.get('cafe_url', ''),
                task_data.get('board_name', ''),
                task_data.get('board_url', ''),
                task_data.get('start_page', 1),
                task_data.get('end_page', 10),
                task_data.get('status', 'pending'),
                task_data.get('created_at', datetime.now().isoformat())
            ))
            
            conn.commit()
            logger.info(f"카페 추출 작업 생성: {task_id}")
            return task_id
    
    def get_cafe_extraction_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """카페 추출 작업 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM cafe_extraction_tasks WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_cafe_extraction_tasks(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """카페 추출 작업 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM cafe_extraction_tasks 
                    WHERE status = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (status, limit))
            else:
                cursor.execute("""
                    SELECT * FROM cafe_extraction_tasks 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_cafe_extraction_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """카페 추출 작업 업데이트"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 업데이트할 필드와 값 준비
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(task_id)  # WHERE 절용
            
            query = f"""
                UPDATE cafe_extraction_tasks 
                SET {', '.join(set_clauses)}
                WHERE task_id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.debug(f"카페 추출 작업 업데이트: {task_id}")
            return success
    
    def add_cafe_extraction_history(self, task_id: str, action: str, details: Dict[str, Any] = None):
        """카페 추출 히스토리 추가"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cafe_extraction_history (task_id, action, details)
                VALUES (?, ?, ?)
            """, (
                task_id,
                action,
                json.dumps(details or {})
            ))
            
            conn.commit()
    
    def get_cafe_extraction_history(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """카페 추출 히스토리 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM cafe_extraction_history 
                WHERE task_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (task_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history_item = dict(row)
                history_item['details'] = json.loads(history_item.get('details', '{}'))
                history.append(history_item)
            
            return history
    
    def delete_cafe_extraction_task(self, task_id: str) -> bool:
        """카페 추출 작업 삭제 (결과와 히스토리 포함)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 관련 데이터 모두 삭제
            cursor.execute("DELETE FROM cafe_extraction_history WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM cafe_extraction_results WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM cafe_extraction_tasks WHERE task_id = ?", (task_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.debug(f"카페 추출 작업 삭제: {task_id}")
            return success
    
    # ========== 일반적인 유틸리티 메서드 ==========
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """일반적인 SELECT 쿼리 실행"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """일반적인 INSERT/UPDATE/DELETE 쿼리 실행"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    # ========== 파워링크 분석 관련 메서드 ==========
    
    def save_powerlink_analysis_session(self, keywords_data: Dict[str, Any]) -> int:
        """파워링크 분석 세션 저장"""
        if not keywords_data:
            raise ValueError("저장할 키워드 데이터가 없습니다.")
        
        # 세션명 생성 (가장 검색량이 많은 키워드 기준)
        session_name = self._generate_powerlink_session_name(keywords_data)
        keyword_count = len(keywords_data)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 세션 저장
            cursor.execute("""
                INSERT INTO powerlink_analysis_sessions (session_name, keyword_count)
                VALUES (?, ?)
            """, (session_name, keyword_count))
            
            session_id = cursor.lastrowid
            
            # 키워드 결과들 저장
            for keyword, result in keywords_data.items():
                cursor.execute("""
                    INSERT INTO powerlink_keyword_results (
                        session_id, keyword, pc_search_volume, mobile_search_volume,
                        pc_clicks, pc_ctr, pc_first_page_positions, 
                        pc_first_position_bid, pc_min_exposure_bid, pc_recommendation_rank,
                        mobile_clicks, mobile_ctr, mobile_first_page_positions,
                        mobile_first_position_bid, mobile_min_exposure_bid, mobile_recommendation_rank,
                        analyzed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, result.keyword, result.pc_search_volume, result.mobile_search_volume,
                    result.pc_clicks, result.pc_ctr, result.pc_first_page_positions,
                    result.pc_first_position_bid, result.pc_min_exposure_bid, result.pc_recommendation_rank,
                    result.mobile_clicks, result.mobile_ctr, result.mobile_first_page_positions,
                    result.mobile_first_position_bid, result.mobile_min_exposure_bid, result.mobile_recommendation_rank,
                    result.analyzed_at.isoformat() if hasattr(result, 'analyzed_at') and result.analyzed_at else datetime.now().isoformat()
                ))
                
                keyword_result_id = cursor.lastrowid
                
                # PC 순위별 입찰가 정보 저장
                if hasattr(result, 'pc_bid_positions') and result.pc_bid_positions:
                    for bid_pos in result.pc_bid_positions:
                        cursor.execute("""
                            INSERT INTO powerlink_bid_positions (keyword_result_id, device_type, position, bid_price)
                            VALUES (?, ?, ?, ?)
                        """, (keyword_result_id, 'pc', bid_pos.position, bid_pos.bid_price))
                
                # 모바일 순위별 입찰가 정보 저장
                if hasattr(result, 'mobile_bid_positions') and result.mobile_bid_positions:
                    for bid_pos in result.mobile_bid_positions:
                        cursor.execute("""
                            INSERT INTO powerlink_bid_positions (keyword_result_id, device_type, position, bid_price)
                            VALUES (?, ?, ?, ?)
                        """, (keyword_result_id, 'mobile', bid_pos.position, bid_pos.bid_price))
            
            conn.commit()
            logger.debug(f"파워링크 분석 세션 저장: {session_id}")
            return session_id
    
    def _generate_powerlink_session_name(self, keywords_data: Dict[str, Any]) -> str:
        """파워링크 세션명 생성 (가장 검색량이 많은 키워드 기준)"""
        # 가장 검색량이 많은 키워드 찾기 (PC + Mobile 합계 기준)
        max_search_result = max(keywords_data.values(), 
                               key=lambda x: getattr(x, 'pc_search_volume', 0) + getattr(x, 'mobile_search_volume', 0))
        
        main_keyword = max_search_result.keyword
        other_count = len(keywords_data) - 1
        
        if other_count > 0:
            return f"{main_keyword} 외 {other_count}개"
        else:
            return main_keyword
    
    def check_powerlink_session_duplicate_24h(self, keywords_data: Dict[str, Any]) -> bool:
        """24시간 이내 동일한 키워드 세트 중복 확인"""
        current_keywords = set(keywords_data.keys())
        
        # 24시간 전 시간 계산
        from datetime import datetime, timedelta
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 24시간 이내 세션들만 조회
            cursor.execute("""
                SELECT id FROM powerlink_analysis_sessions 
                WHERE created_at >= ? 
                ORDER BY created_at DESC
            """, (twenty_four_hours_ago.isoformat(),))
            
            sessions = cursor.fetchall()
            
            for session_id, in sessions:
                # 각 세션의 키워드 목록 가져오기
                cursor.execute("""
                    SELECT keyword FROM powerlink_keyword_results 
                    WHERE session_id = ?
                """, (session_id,))
                
                session_keywords = set(row[0] for row in cursor.fetchall())
                
                # 완전히 동일한 키워드 세트인지 확인
                if current_keywords == session_keywords:
                    return True
            
            return False
    
    
    def get_all_powerlink_analysis_sessions(self) -> List[Dict[str, Any]]:
        """모든 파워링크 분석 세션 조회 (최신순)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_name, created_at, keyword_count
                FROM powerlink_analysis_sessions
                ORDER BY created_at DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'session_name': row[1],
                    'created_at': row[2],
                    'keyword_count': row[3]
                })
            
            return sessions
    
    def get_powerlink_session_keywords(self, session_id: int) -> Dict[str, Any]:
        """특정 파워링크 세션의 키워드 결과들 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 키워드 결과 조회
            cursor.execute("""
                SELECT kr.id, kr.keyword, kr.pc_search_volume, kr.mobile_search_volume,
                       kr.pc_clicks, kr.pc_ctr, kr.pc_first_page_positions, 
                       kr.pc_first_position_bid, kr.pc_min_exposure_bid, kr.pc_recommendation_rank,
                       kr.mobile_clicks, kr.mobile_ctr, kr.mobile_first_page_positions,
                       kr.mobile_first_position_bid, kr.mobile_min_exposure_bid, kr.mobile_recommendation_rank,
                       kr.analyzed_at
                FROM powerlink_keyword_results kr
                WHERE kr.session_id = ?
                ORDER BY kr.pc_recommendation_rank, kr.mobile_recommendation_rank
            """, (session_id,))
            
            keywords_data = {}
            keyword_result_ids = []
            
            for row in cursor.fetchall():
                keyword_result_id = row[0]
                keyword_result_ids.append(keyword_result_id)
                
                # KeywordAnalysisResult는 여기서 dict로 반환하고, service 레이어에서 변환
                result_dict = {
                    'keyword': row[1],
                    'pc_search_volume': row[2],
                    'mobile_search_volume': row[3],
                    'pc_clicks': row[4],
                    'pc_ctr': row[5],
                    'pc_first_page_positions': row[6],
                    'pc_first_position_bid': row[7],
                    'pc_min_exposure_bid': row[8],
                    'pc_recommendation_rank': row[9],
                    'mobile_clicks': row[10],
                    'mobile_ctr': row[11],
                    'mobile_first_page_positions': row[12],
                    'mobile_first_position_bid': row[13],
                    'mobile_min_exposure_bid': row[14],
                    'mobile_recommendation_rank': row[15],
                    'analyzed_at': row[16],
                    'pc_bid_positions': [],
                    'mobile_bid_positions': []
                }
                keywords_data[result_dict['keyword']] = result_dict
            
            # 모든 bid_positions를 한 번에 가져오기
            if keyword_result_ids:
                placeholders = ','.join('?' * len(keyword_result_ids))
                cursor.execute(f"""
                    SELECT kr.keyword, bp.device_type, bp.position, bp.bid_price
                    FROM powerlink_bid_positions bp
                    JOIN powerlink_keyword_results kr ON bp.keyword_result_id = kr.id
                    WHERE bp.keyword_result_id IN ({placeholders})
                    ORDER BY kr.keyword, bp.device_type, bp.position
                """, keyword_result_ids)
                
                # 결과를 그룹화해서 각 키워드에 할당
                for row in cursor.fetchall():
                    keyword, device_type, position, bid_price = row
                    bid_pos_dict = {'position': position, 'bid_price': bid_price}
                    
                    if keyword in keywords_data:
                        if device_type == 'pc':
                            keywords_data[keyword]['pc_bid_positions'].append(bid_pos_dict)
                        elif device_type == 'mobile':
                            keywords_data[keyword]['mobile_bid_positions'].append(bid_pos_dict)
            
            return keywords_data
    
    def delete_powerlink_analysis_session(self, session_id: int) -> bool:
        """파워링크 분석 세션 삭제"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # keyword_result_id들을 가져오기
                cursor.execute('SELECT id FROM powerlink_keyword_results WHERE session_id = ?', (session_id,))
                keyword_result_ids = [row[0] for row in cursor.fetchall()]
                
                # 순위별 입찰가 정보 삭제
                for keyword_result_id in keyword_result_ids:
                    cursor.execute('DELETE FROM powerlink_bid_positions WHERE keyword_result_id = ?', (keyword_result_id,))
                
                # 키워드 결과들 삭제
                cursor.execute('DELETE FROM powerlink_keyword_results WHERE session_id = ?', (session_id,))
                
                # 세션 삭제
                cursor.execute('DELETE FROM powerlink_analysis_sessions WHERE id = ?', (session_id,))
                
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    logger.debug(f"파워링크 분석 세션 삭제: {session_id}")
                return success
        except Exception as e:
            logger.error(f"파워링크 분석 세션 삭제 실패: {session_id}: {e}")
            return False
    
    def get_powerlink_session_info(self, session_id: int) -> Optional[Dict[str, Any]]:
        """특정 파워링크 세션 정보 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_name, created_at, keyword_count
                FROM powerlink_analysis_sessions
                WHERE id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'session_name': row[1],
                    'created_at': row[2],
                    'keyword_count': row[3]
                }
            return None
    
    # PowerLink UI 호환성 메서드들
    def list_powerlink_sessions(self) -> List[Dict[str, Any]]:
        """파워링크 세션 목록 (UI 호환)"""
        return self.get_all_powerlink_analysis_sessions()
    
    def delete_powerlink_session(self, session_id: int) -> bool:
        """파워링크 세션 삭제 (UI 호환)"""
        return self.delete_powerlink_analysis_session(session_id)
    
    def get_powerlink_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """파워링크 세션 정보 조회 (UI 호환)"""
        return self.get_powerlink_session_info(session_id)
    
    def delete_powerlink_sessions(self, session_ids: List[int]) -> bool:
        """파워링크 다중 세션 삭제 (UI 호환)"""
        try:
            success_count = 0
            for session_id in session_ids:
                if self.delete_powerlink_analysis_session(session_id):
                    success_count += 1
            
            # 모든 세션이 성공적으로 삭제되었으면 True
            return success_count == len(session_ids)
        except Exception as e:
            logger.error(f"파워링크 다중 세션 삭제 실패: {e}")
            return False
    
    
    def list_cafe_extraction_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """카페 추출 작업 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task_id, cafe_name, cafe_url, board_name, board_url,
                       start_page, end_page, status, created_at, total_extracted
                FROM cafe_extraction_tasks
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_cafe_extraction_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 카페 추출 작업 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task_id, cafe_name, cafe_url, board_name, board_url,
                       start_page, end_page, status, created_at, started_at,
                       completed_at, error_message, total_extracted
                FROM cafe_extraction_tasks
                WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_cafe_extraction_task_status(self, task_id: str, status: str, 
                                         current_page: Optional[int] = None,
                                         total_extracted: Optional[int] = None,
                                         error_message: Optional[str] = None) -> bool:
        """카페 추출 작업 상태 업데이트"""
        from datetime import datetime
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 동적으로 UPDATE 쿼리 생성
            set_clauses = ["status = ?"]
            values = [status]
            
            if status == 'extracting' and current_page is not None:
                set_clauses.extend(["current_page = ?", "started_at = ?"])
                values.extend([current_page, datetime.now().isoformat()])
            elif status == 'completed':
                set_clauses.append("completed_at = ?")
                values.append(datetime.now().isoformat())
            elif status == 'failed' and error_message:
                set_clauses.append("error_message = ?")
                values.append(error_message)
            
            if total_extracted is not None:
                set_clauses.append("total_extracted = ?")
                values.append(total_extracted)
            
            values.append(task_id)  # WHERE 절용
            
            query = f"""
                UPDATE cafe_extraction_tasks
                SET {', '.join(set_clauses)}
                WHERE task_id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def save_cafe_extraction_results(self, task_id: str, users: List[Dict[str, Any]]) -> int:
        """카페 추출 결과 저장"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 기존 결과 삭제 (재추출의 경우)
            cursor.execute("DELETE FROM cafe_extraction_results WHERE task_id = ?", (task_id,))
            
            # 새 결과 저장
            saved_count = 0
            for user in users:
                cursor.execute("""
                    INSERT INTO cafe_extraction_results (
                        task_id, user_id, nickname, article_count, first_seen, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    user.get('user_id', ''),
                    user.get('nickname', ''),
                    user.get('article_count', 1),
                    user.get('first_seen', ''),
                    user.get('last_seen', '')
                ))
                saved_count += 1
            
            conn.commit()
            logger.info(f"카페 추출 결과 저장: {saved_count}개 사용자")
            return saved_count
    
    def get_cafe_extraction_results(self, task_id: str) -> List[Dict[str, Any]]:
        """카페 추출 결과 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, nickname, article_count, first_seen, last_seen
                FROM cafe_extraction_results
                WHERE task_id = ?
                ORDER BY article_count DESC, nickname
            """, (task_id,))
            
            return [dict(row) for row in cursor.fetchall()]

    # ==========================================
    # 변경사항 이력 관리
    # ==========================================
    
    def get_basic_info_change_history(self, project_id: int) -> List[Dict[str, Any]]:
        """기본정보 변경 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    changed_at as change_time,
                    field_name,
                    old_value,
                    new_value,
                    CASE WHEN change_type = 'auto' THEN 1 ELSE 0 END as is_auto
                FROM basic_info_change_history
                WHERE project_id = ?
                ORDER BY changed_at DESC
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_keyword_management_history(self, project_id: int) -> List[Dict[str, Any]]:
        """키워드 관리 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    action_date as action_time,
                    keyword,
                    action
                FROM keyword_management_history
                WHERE project_id = ?
                ORDER BY action_date DESC
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_ranking_history_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        """프로젝트의 순위 이력 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rr.search_date as check_time,
                    k.keyword,
                    rr.rank_position as rank,
                    rr.total_results as result_count
                FROM ranking_results rr
                JOIN keywords k ON rr.keyword_id = k.id
                WHERE k.project_id = ?
                ORDER BY rr.search_date DESC, k.keyword
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]

    def add_basic_info_change_record(self, project_id: int, field_name: str, 
                                   old_value: str, new_value: str, is_auto: bool = True):
        """기본정보 변경 기록 추가"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            change_type = 'auto' if is_auto else 'manual'
            
            cursor.execute("""
                INSERT INTO basic_info_change_history 
                (project_id, field_name, old_value, new_value, change_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                project_id, 
                field_name, 
                old_value, 
                new_value, 
                change_type
            ))
            
            conn.commit()

    def add_keyword_management_record(self, project_id: int, keyword: str, action: str):
        """키워드 관리 기록 추가"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO keyword_management_history 
                (project_id, keyword, action)
                VALUES (?, ?, ?)
            """, (
                project_id, 
                keyword, 
                action  # 'add', 'delete', 'update'
            ))
            
            conn.commit()

    def get_keyword_rankings(self, keyword_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """특정 키워드의 순위 이력 조회 (최신순)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rank_position as rank,
                    total_results,
                    search_date as check_time
                FROM ranking_results 
                WHERE keyword_id = ?
                ORDER BY search_date DESC
                LIMIT ?
            """, (keyword_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== 카페 추출 관련 메서드 ====================
    
    def add_cafe_extraction_task(self, task_data: Dict[str, Any]) -> bool:
        """카페 추출 작업 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO cafe_extraction_tasks (
                        task_id, cafe_name, cafe_url, board_name, board_url,
                        start_page, end_page, status, current_page, total_extracted,
                        created_at, completed_at, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data.get('task_id'),
                    task_data.get('cafe_name'),
                    task_data.get('cafe_url'),
                    task_data.get('board_name'),
                    task_data.get('board_url'),
                    task_data.get('start_page', 1),
                    task_data.get('end_page', 10),
                    task_data.get('status', 'pending'),
                    task_data.get('current_page', 1),
                    task_data.get('total_extracted', 0),
                    task_data.get('created_at'),
                    task_data.get('completed_at'),
                    task_data.get('error_message', '')
                ))
                
                conn.commit()
                logger.info(f"카페 추출 작업 저장 완료: {task_data.get('task_id')}")
                return True
                
        except Exception as e:
            logger.error(f"카페 추출 작업 저장 실패: {e}")
            return False
    
    def get_cafe_extraction_tasks(self) -> List[Dict[str, Any]]:
        """모든 카페 추출 작업 조회 (최신순)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM cafe_extraction_tasks
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"카페 추출 작업 조회 실패: {e}")
            return []
    
    def delete_cafe_extraction_task(self, task_id: str) -> bool:
        """카페 추출 작업 삭제"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM cafe_extraction_tasks WHERE task_id = ?
                """, (task_id,))
                
                conn.commit()
                logger.info(f"카페 추출 작업 삭제 완료: {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"카페 추출 작업 삭제 실패: {e}")
            return False
    
    def add_cafe_extraction_result(self, result_data: Dict[str, Any]) -> bool:
        """카페 추출 결과 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO cafe_extraction_results (
                        task_id, user_id, nickname, article_count, 
                        article_url, article_title, article_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result_data.get('task_id'),
                    result_data.get('user_id'),
                    result_data.get('nickname'),
                    result_data.get('article_count', 1),
                    result_data.get('article_url', ''),
                    result_data.get('article_title', ''),
                    result_data.get('article_date', '')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"카페 추출 결과 저장 실패: {e}")
            return False
    
    def get_cafe_extraction_results(self, task_id: str) -> List[Dict[str, Any]]:
        """특정 작업의 추출 결과 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM cafe_extraction_results
                    WHERE task_id = ?
                    ORDER BY extracted_at ASC
                """, (task_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"카페 추출 결과 조회 실패: {e}")
            return []
    
    


# 전역 DB 인스턴스 (싱글톤 패턴)
_db_instance: Optional[CommonDB] = None


def get_db() -> CommonDB:
    """공용 DB 인스턴스 반환 (싱글톤)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = CommonDB()
    return _db_instance


def init_db(db_path: Optional[Path] = None):
    """DB 초기화 (애플리케이션 시작시 호출)"""
    global _db_instance
    _db_instance = CommonDB(db_path)
    logger.info("공용 DB 초기화 완료")




# 편의성을 위한 함수들
def save_api_config(service_name: str, config_data: Dict[str, Any]):
    """API 설정 저장 (편의 함수)"""
    get_db().save_api_config(service_name, config_data)


def get_api_config(service_name: str) -> Optional[Dict[str, Any]]:
    """API 설정 조회 (편의 함수)"""
    return get_db().get_api_config(service_name)