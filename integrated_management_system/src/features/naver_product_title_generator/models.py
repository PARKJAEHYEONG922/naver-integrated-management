"""
네이버 상품명 생성기 데이터 모델 (간소화)
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class AnalysisStep(Enum):
    """분석 단계"""
    PRODUCT_INPUT = 1      # 제품명 입력
    BASIC_ANALYSIS = 2     # 기초분석 (검색량, 카테고리)
    ADVANCED_ANALYSIS = 3  # 심화분석 (AI 분석)
    TITLE_GENERATION = 4   # 상품명 생성


@dataclass
class ProductInput:
    """1단계: 사용자가 입력한 제품명"""
    product_name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.product_name = self.product_name.strip()


@dataclass
class KeywordBasicData:
    """2단계: 기초분석 결과 (키워드별)"""
    keyword: str
    search_volume: int      # 월 검색량
    category: str          # 카테고리 (+ 비율)
    total_products: int = 0    # 전체상품수 (3단계에서 추가됨)
    is_selected: bool = False  # 사용자 선택 여부
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductNameData:
    """2단계: 수집된 상품명 정보"""
    rank: int
    title: str
    keyword: str                    # 검색에 사용된 키워드
    price: int = 0
    mall_name: str = ""
    category: str = ""
    product_id: str = ""
    image_url: str = ""
    link: str = ""
    avg_rank: float = 0.0          # 평균 순위 (여러 키워드에서 발견된 경우)
    keywords_found_in: List[str] = field(default_factory=list)  # 발견된 키워드들
    keyword_count: int = 1         # 키워드 개수
    final_rank: int = 0            # 최종 순위 (중복 제거 후)
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass
class AIAnalysisResult:
    """3단계: AI 심화분석 결과 (추후 구현)"""
    keyword: str
    related_keywords: List[str] = field(default_factory=list)
    seo_score: float = 0.0
    confidence: float = 0.0
    market_trend: str = ""
    is_selected: bool = False
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class GeneratedTitle:
    """4단계: 생성된 상품명 (추후 구현)"""
    title: str
    seo_score: float = 0.0
    estimated_search: int = 0
    character_count: int = 0
    keywords_used: List[str] = field(default_factory=list)
    generation_reason: str = ""
    final_rank: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.character_count == 0:
            self.character_count = len(self.title)


@dataclass
class SessionData:
    """세션 데이터 (간소화)"""
    session_id: str
    product_input: Optional[ProductInput] = None
    basic_analysis_results: List[KeywordBasicData] = field(default_factory=list)
    selected_category: str = ""  # 1단계에서 사용자가 선택한 카테고리
    selected_basic_keywords: List[str] = field(default_factory=list)  # 1단계에서 사용자가 선택한 키워드들
    collected_product_names: List[ProductNameData] = field(default_factory=list)  # 2단계 추가
    ai_analysis_results: List[AIAnalysisResult] = field(default_factory=list)
    generated_titles: List[GeneratedTitle] = field(default_factory=list)
    current_step: AnalysisStep = AnalysisStep.PRODUCT_INPUT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_timestamp(self):
        """업데이트 시간 갱신"""
        self.updated_at = datetime.now()


# 간소화된 Repository
class ProductTitleRepository:
    """상품명 생성기 데이터 저장소 (간소화)"""
    
    def __init__(self):
        self._sessions = {}  # 임시 메모리 저장소
    
    def create_session(self, product_name: str) -> str:
        """새 세션 생성"""
        import uuid
        session_id = str(uuid.uuid4())
        return session_id
    
    def save_session(self, session_data: SessionData) -> bool:
        """세션 저장 (메모리)"""
        self._sessions[session_data.session_id] = session_data
        return True
    
    def load_session(self, session_id: str) -> Optional[SessionData]:
        """세션 로드"""
        return self._sessions.get(session_id)


# 헬퍼 함수들
def create_new_session(product_name: str) -> SessionData:
    """새 세션 생성"""
    session_id = repository.create_session(product_name)
    product_input = ProductInput(product_name=product_name)
    
    return SessionData(
        session_id=session_id,
        product_input=product_input,
        current_step=AnalysisStep.PRODUCT_INPUT
    )


def validate_product_name(product_name: str) -> bool:
    """제품명 검증"""
    if not product_name or not product_name.strip():
        return False
    
    cleaned = product_name.strip()
    return 2 <= len(cleaned) <= 100


def calculate_title_score(title: str, keywords: List[str]) -> float:
    """상품명 점수 계산 (추후 구현)"""
    return 50.0  # 임시 기본값


# 전역 리포지터리 인스턴스
repository = ProductTitleRepository()