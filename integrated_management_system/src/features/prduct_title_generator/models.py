"""
네이버 상품명 생성기 모델
DTO/엔티티, Enum, 상수, 테이블 DDL, 간단 레포 헬퍼
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Any

from src.foundation.db import get_db


class AIProvider(Enum):
    """AI 제공자"""
    OPENAI = "openai"
    GEMINI = "gemini" 
    CLAUDE = "claude"


class AnalysisStatus(Enum):
    """분석 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProductInfo:
    """상품 정보 DTO"""
    title: str
    category1: str = ""
    category2: str = ""
    category3: str = ""
    category4: str = ""
    price: int = 0
    
    @property
    def main_category(self) -> str:
        """메인 카테고리 반환 (가장 구체적인 카테고리)"""
        for i in range(4, 0, -1):
            category = getattr(self, f'category{i}', '').strip()
            if category:
                return category
        return ""


@dataclass
class KeywordInfo:
    """키워드 정보 DTO"""
    keyword: str
    search_volume: int = 0
    category: str = ""
    category_match: bool = False
    word_count: int = 1
    
    def __post_init__(self):
        self.word_count = self.keyword.count(' ') + 1


@dataclass
class GeneratedTitle:
    """생성된 상품명 DTO"""
    title: str
    seo_score: float
    estimated_volume: int
    keywords_used: List[str]
    
    @property
    def char_count(self) -> int:
        """글자수 (계산 필드)"""
        return len(self.title)


@dataclass
class AnalysisResult:
    """분석 결과 DTO"""
    brand: str
    keyword: str
    spec: str
    main_category: str
    category_ratio: float
    final_tokens: List[str]
    search_volumes: Dict[str, int]
    status: AnalysisStatus
    created_at: str
    
    @property
    def total_volume(self) -> int:
        """총 검색량 합계"""
        return sum(self.search_volumes.values())
    
    @property
    def avg_volume(self) -> float:
        """평균 검색량"""
        if not self.search_volumes:
            return 0.0
        return self.total_volume / len(self.search_volumes)


class ProductTitleRepository:
    """상품명 생성기 레포지토리"""
    
    def __init__(self):
        self._ensure_tables()
    
    def _ensure_tables(self):
        """테이블 생성"""
        with get_db().get_connection() as conn:
            # 분석 이력 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    spec TEXT,
                    main_category TEXT,
                    category_ratio REAL,
                    token_count INTEGER,
                    total_volume INTEGER,
                    status TEXT NOT NULL CHECK(status IN ('pending','processing','completed','failed')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 키워드 분석 결과 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS keyword_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    search_volume INTEGER DEFAULT 0,
                    category TEXT,
                    category_match INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES analysis_history (id) ON DELETE CASCADE
                )
            """)
            
            # 생성된 상품명 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generated_titles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    seo_score REAL NOT NULL DEFAULT 0.0,
                    estimated_volume INTEGER NOT NULL DEFAULT 0,
                    char_count INTEGER NOT NULL DEFAULT 0,
                    keywords_used TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES analysis_history (id) ON DELETE CASCADE
                )
            """)
            
            # updated_at 자동 업데이트 트리거 추가
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS update_analysis_history_timestamp
                AFTER UPDATE ON analysis_history
                FOR EACH ROW
                BEGIN
                    UPDATE analysis_history 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """)
            
            # 성능 최적화를 위한 인덱스 추가
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at ON analysis_history(created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_keyword_analysis_lookup ON keyword_analysis(analysis_id, search_volume DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_generated_titles_lookup ON generated_titles(analysis_id, seo_score DESC)")
            
            # 데이터 무결성을 위한 추가 인덱스
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_keyword_analysis_analysis_kw ON keyword_analysis(analysis_id, keyword)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_history_status_created ON analysis_history(status, created_at DESC)")
    
    def save_analysis_result(self, result: AnalysisResult) -> int:
        """분석 결과 저장"""
        with get_db().get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO analysis_history 
                (brand, keyword, spec, main_category, category_ratio, token_count, total_volume, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.brand,
                result.keyword,
                result.spec,
                result.main_category,
                result.category_ratio,
                len(result.final_tokens),
                result.total_volume,
                result.status.value
            ))
            
            analysis_id = cursor.lastrowid
            
            # 키워드 분석 결과 저장 (category, category_match 포함)
            for token in result.final_tokens:
                volume = result.search_volumes.get(token, 0)
                word_count = token.count(' ') + 1
                
                # 카테고리 매칭 여부 계산 (메인 카테고리와 일치하는지)
                category_match = result.main_category.lower() in token.lower() if result.main_category else False
                
                conn.execute("""
                    INSERT INTO keyword_analysis 
                    (analysis_id, keyword, search_volume, category, category_match, word_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (analysis_id, token, volume, result.main_category, int(category_match), word_count))
            
            return analysis_id
    
    def save_generated_titles(self, analysis_id: int, titles: List[GeneratedTitle]) -> None:
        """생성된 상품명 저장"""
        with get_db().get_connection() as conn:
            for title in titles:
                keywords_used = ','.join(title.keywords_used) if title.keywords_used else ''
                conn.execute("""
                    INSERT INTO generated_titles 
                    (analysis_id, title, seo_score, estimated_volume, char_count, keywords_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    title.title,
                    title.seo_score,
                    title.estimated_volume,
                    title.char_count,
                    keywords_used
                ))
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 분석 이력 조회"""
        with get_db().get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, brand, keyword, spec, main_category, category_ratio,
                       token_count, total_volume, status, created_at
                FROM analysis_history
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_analysis_detail(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """분석 상세 정보 조회"""
        with get_db().get_connection() as conn:
            # 기본 정보
            cursor = conn.execute("""
                SELECT * FROM analysis_history WHERE id = ?
            """, (analysis_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [col[0] for col in cursor.description]
            analysis = dict(zip(columns, row))
            
            # 키워드 분석 결과 (category, category_match 포함)
            cursor = conn.execute("""
                SELECT keyword, search_volume, category, category_match, word_count
                FROM keyword_analysis 
                WHERE analysis_id = ?
                ORDER BY search_volume DESC
            """, (analysis_id,))
            
            analysis['keywords'] = [
                {
                    'keyword': row[0],
                    'search_volume': row[1],
                    'category': row[2],
                    'category_match': bool(row[3]) if row[3] is not None else False,
                    'word_count': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            # 생성된 상품명
            cursor = conn.execute("""
                SELECT title, seo_score, estimated_volume, char_count, keywords_used
                FROM generated_titles 
                WHERE analysis_id = ?
                ORDER BY seo_score DESC
            """, (analysis_id,))
            
            analysis['titles'] = [
                {
                    'title': row[0],
                    'seo_score': row[1],
                    'estimated_volume': row[2],
                    'char_count': row[3],
                    'keywords_used': row[4].split(',') if row[4] else []
                }
                for row in cursor.fetchall()
            ]
            
            return analysis


# 상수
DEFAULT_SEARCH_VOLUME_THRESHOLD = 100
DEFAULT_PRODUCT_COUNT = 40
MAX_KEYWORD_LENGTH = 20
MAX_TITLE_LENGTH = 50
TOP_N_TITLES = 5  # 상위 N개 제목 반환

# SEO 점수 가중치
SEO_WEIGHTS = {
    'keyword_inclusion': 30,    # 핵심 키워드 포함
    'token_coverage': 25,       # 선택된 토큰 포함도
    'length_optimization': 20,  # 제목 길이 최적화
    'brand_inclusion': 15,      # 브랜드명 포함
    'readability': 10          # 읽기 쉬운 구조
}

# 제목 길이 최적화 점수
TITLE_LENGTH_SCORES = {
    'optimal': (20, 35, 20),   # (최소, 최대, 점수)
    'good': (15, 40, 15),
    'acceptable': (10, 45, 10)
}