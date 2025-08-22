"""
키워드 분석 데이터 구조 (CLAUDE.md 구조 - DTO 전용)
데이터 모델/스키마만 포함. 포맷/판정/점수/통계 로직 없음.

# TODO: 표시는 toolbox.formatters 사용
# TODO: 판정/점수는 engine_local로 이동  
# TODO: 진행률 %는 toolbox.progress.calc_percentage 사용
# TODO: 선별/통계는 engine_local.*로 이동
"""
import math
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AnalysisScope(Enum):
    """분석 범위 설정"""
    COMPETITION_ONLY = "competition_only"  # 경쟁분석만
    CATEGORY_ONLY = "category_only"        # 카테고리만  
    FULL_ANALYSIS = "full_analysis"        # 전체 분석


@dataclass(slots=True)
class KeywordData:
    """키워드 검색 결과 DTO (Data Transfer Object)"""
    keyword: str
    category: str = ""
    search_volume: Optional[int] = None
    total_products: Optional[int] = None
    competition_strength: Optional[float] = None
    
    def __post_init__(self):
        """데이터 정규화 및 이상치 처리"""
        # 음수 값을 0으로 클램프
        if self.search_volume is not None and self.search_volume < 0:
            self.search_volume = 0
        if self.total_products is not None and self.total_products < 0:
            self.total_products = 0
        
        # competition_strength 이상치 처리
        if self.competition_strength is not None:
            try:
                # float 변환 시도
                self.competition_strength = float(self.competition_strength)
                
                # NaN/Inf/음수 안전 처리
                if math.isnan(self.competition_strength) or math.isinf(self.competition_strength):
                    self.competition_strength = None
                elif self.competition_strength < 0:
                    self.competition_strength = 0.0
            except (TypeError, ValueError):
                self.competition_strength = None
    
    # TODO: 표시용 포맷은 toolbox.formatters.format_int, format_float, format_competition 사용
    # TODO: 별도 판정 로직이 필요하면 engine_local에 추가(현재는 미사용)
    # TODO: 점수 계산은 engine_local.opportunity_score로 이동
    # TODO: 유효성 검사는 engine_local.has_valid_data로 이동


@dataclass(slots=True)
class AnalysisPolicy:
    """분석 정책 파라미터(판정/계산 없음)"""
    scope: AnalysisScope = AnalysisScope.FULL_ANALYSIS
    min_search_volume: int = 100
    max_competition_threshold: float = 1.0
    
    def should_analyze_competition(self) -> bool:
        """경쟁 분석 여부 판단"""
        return self.scope in (AnalysisScope.COMPETITION_ONLY, AnalysisScope.FULL_ANALYSIS)
    
    def should_analyze_category(self) -> bool:
        """카테고리 분석 여부 판단"""
        return self.scope in (AnalysisScope.CATEGORY_ONLY, AnalysisScope.FULL_ANALYSIS)
    
    # TODO: 수익성 판단은 engine_local.is_keyword_viable(keyword_data, policy)로 이동


@dataclass(slots=True)
class AnalysisResult:
    """분석 결과 DTO (Data Transfer Object)"""
    keywords: List[KeywordData]
    policy: AnalysisPolicy
    start_time: datetime
    end_time: datetime
    
    @property
    def duration(self) -> float:
        """소요 시간 (초)"""
        # 음수 시간 방지 (시계 드리프트 등)
        duration_seconds = (self.end_time - self.start_time).total_seconds()
        return max(0.0, duration_seconds)


# 공개 API 정의
__all__ = [
    "AnalysisScope",
    "KeywordData",
    "AnalysisPolicy",
    "AnalysisResult",
]

# TODO: 선별/통계는 engine_local.*로 이동
# - successful_count          → engine_local.count_successful
# - failed_count              → engine_local.count_failed
# - viable_keywords           → engine_local.select_viable
# - high_opportunity_keywords → engine_local.top_high_opportunity
# - get_summary_stats         → engine_local.summary_stats