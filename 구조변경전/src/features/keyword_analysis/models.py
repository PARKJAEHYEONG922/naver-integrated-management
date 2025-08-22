"""
키워드 분석 데이터 모델 (단순한 dataclass)
DB 없이 메모리에서만 사용하는 모델들
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class KeywordData:
    """키워드 검색 결과 데이터 모델"""
    keyword: str
    category: str = ""
    search_volume: Optional[int] = None
    total_products: Optional[int] = None
    competition_strength: Optional[float] = None
    
    @property
    def formatted_volume(self) -> str:
        """포맷된 검색량"""
        return f"{self.search_volume:,}" if self.search_volume is not None else "N/A"
    
    @property
    def formatted_products(self) -> str:
        """포맷된 상품수"""
        return f"{self.total_products:,}" if self.total_products is not None else "N/A"
    
    @property
    def formatted_strength(self) -> str:
        """포맷된 경쟁강도"""
        if self.competition_strength is None or self.competition_strength == float('inf'):
            return "N/A"
        return f"{self.competition_strength:.2f}"


# APIConfig는 foundation/config.py로 통합됨 - 중복 제거


@dataclass
class AnalysisConfig:
    """분석 설정 데이터 모델"""
    max_workers: int = 3
    delay_between_requests: float = 0.5
    include_competition: bool = True
    include_category: bool = True
    timeout: int = 30


@dataclass
class AnalysisProgress:
    """분석 진행 상황 데이터 모델"""
    total_keywords: int = 0
    completed_keywords: int = 0
    failed_keywords: int = 0
    current_keyword: str = ""
    
    @property
    def progress_percentage(self) -> float:
        """진행률 (0-100)"""
        if self.total_keywords == 0:
            return 0.0
        return (self.completed_keywords + self.failed_keywords) / self.total_keywords * 100


@dataclass
class AnalysisResult:
    """분석 결과 데이터 모델"""
    keywords: List[KeywordData]
    config: AnalysisConfig
    start_time: datetime
    end_time: datetime
    
    @property
    def duration(self) -> float:
        """소요 시간 (초)"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def successful_count(self) -> int:
        """성공한 키워드 수"""
        return len([kw for kw in self.keywords if kw.search_volume is not None])
    
    @property
    def failed_count(self) -> int:
        """실패한 키워드 수"""
        return len(self.keywords) - self.successful_count


# DB 관련 임시 호환 클래스들 제거됨 - 메모리 기반으로 단순화