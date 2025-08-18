"""
키워드 분석 데이터 구조 + 비즈니스 도메인 로직 (CLAUDE.md 구조)
데이터 구조/스키마 + 비즈니스 도메인 로직 (I/O 로직 없음)
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AnalysisScope(Enum):
    """분석 범위 설정"""
    COMPETITION_ONLY = "competition_only"  # 검색량만
    CATEGORY_ONLY = "category_only"        # 카테고리만  
    FULL_ANALYSIS = "full_analysis"        # 전체 분석


@dataclass
class KeywordData:
    """키워드 검색 결과 데이터 모델 + 도메인 로직"""
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
    
    def is_high_volume(self) -> bool:
        """고주파 키워드 여부"""
        return self.search_volume is not None and self.search_volume >= 1000
    
    def is_low_competition(self) -> bool:
        """저경쟁 키워드 여부"""
        return (self.competition_strength is not None and 
                self.competition_strength != float('inf') and 
                self.competition_strength <= 0.5)
    
    def get_opportunity_score(self) -> float:
        """기회 점수 계산 (검색량 대비 경쟁도)"""
        if not self.search_volume or not self.competition_strength:
            return 0.0
        
        if self.competition_strength == float('inf'):
            return 0.0
            
        # 검색량이 높고 경쟁이 낮을수록 높은 점수
        return self.search_volume / (1 + self.competition_strength)
    
    def has_valid_data(self) -> bool:
        """유효한 데이터 여부"""
        return (self.search_volume is not None or 
                bool(self.category.strip()) or 
                self.total_products is not None)


@dataclass
class AnalysisPolicy:
    """분석 정책 (비즈니스 규칙)"""
    scope: AnalysisScope = AnalysisScope.FULL_ANALYSIS
    min_search_volume: int = 100
    max_competition_threshold: float = 1.0
    
    def should_analyze_competition(self) -> bool:
        """경쟁 분석 여부 판단"""
        return self.scope in [AnalysisScope.COMPETITION_ONLY, AnalysisScope.FULL_ANALYSIS]
    
    def should_analyze_category(self) -> bool:
        """카테고리 분석 여부 판단"""
        return self.scope in [AnalysisScope.CATEGORY_ONLY, AnalysisScope.FULL_ANALYSIS]
    
    def is_keyword_viable(self, keyword_data: KeywordData) -> bool:
        """키워드 수익성 판단"""
        if not keyword_data.search_volume:
            return False
        
        # 최소 검색량 충족
        if keyword_data.search_volume < self.min_search_volume:
            return False
            
        # 경쟁 강도 체크
        if (keyword_data.competition_strength is not None and 
            keyword_data.competition_strength > self.max_competition_threshold):
            return False
            
        return True


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
    """분석 결과 데이터 모델 + 비즈니스 로직"""
    keywords: List[KeywordData]
    policy: AnalysisPolicy
    start_time: datetime
    end_time: datetime
    
    @property
    def duration(self) -> float:
        """소요 시간 (초)"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def successful_count(self) -> int:
        """성공한 키워드 수 (유효 데이터 있음)"""
        return len([kw for kw in self.keywords if kw.has_valid_data()])
    
    @property
    def failed_count(self) -> int:
        """실패한 키워드 수"""
        return len(self.keywords) - self.successful_count
    
    @property
    def viable_keywords(self) -> List[KeywordData]:
        """수익성 있는 키워드 목록"""
        return [kw for kw in self.keywords if self.policy.is_keyword_viable(kw)]
    
    @property
    def high_opportunity_keywords(self) -> List[KeywordData]:
        """고기회 키워드 목록 (상위 20%)"""
        sorted_keywords = sorted(
            [kw for kw in self.keywords if kw.has_valid_data()],
            key=lambda x: x.get_opportunity_score(),
            reverse=True
        )
        top_count = max(1, len(sorted_keywords) // 5)  # 상위 20%
        return sorted_keywords[:top_count]
    
    def get_summary_stats(self) -> dict:
        """분석 결과 요약 통계"""
        valid_keywords = [kw for kw in self.keywords if kw.has_valid_data()]
        viable_keywords = self.viable_keywords
        
        if not valid_keywords:
            return {
                "total_count": len(self.keywords),
                "valid_count": 0,
                "viable_count": 0,
                "avg_search_volume": 0,
                "avg_competition": 0,
            }
        
        volumes = [kw.search_volume for kw in valid_keywords if kw.search_volume is not None]
        competitions = [kw.competition_strength for kw in valid_keywords 
                      if kw.competition_strength is not None and kw.competition_strength != float('inf')]
        
        return {
            "total_count": len(self.keywords),
            "valid_count": len(valid_keywords),
            "viable_count": len(viable_keywords),
            "avg_search_volume": sum(volumes) // len(volumes) if volumes else 0,
            "avg_competition": sum(competitions) / len(competitions) if competitions else 0,
            "duration_seconds": self.duration
        }