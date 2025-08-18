"""
키워드 분석 기능별 설정 (단순화)
메모리 기반으로 변경되어 복잡한 설정 제거
"""
from .models import AnalysisConfig


# 기본 분석 설정
DEFAULT_ANALYSIS_CONFIG = AnalysisConfig(
    max_workers=3,
    delay_between_requests=0.5,
    include_competition=True,
    include_category=True,
    timeout=30
)


def get_default_config() -> AnalysisConfig:
    """기본 분석 설정 반환"""
    return DEFAULT_ANALYSIS_CONFIG


def create_fast_config() -> AnalysisConfig:
    """빠른 분석용 설정"""
    return AnalysisConfig(
        max_workers=5,
        delay_between_requests=0.3,
        include_competition=True,
        include_category=True,
        timeout=20
    )


def create_safe_config() -> AnalysisConfig:
    """안전한 분석용 설정 (느리지만 안정적)"""
    return AnalysisConfig(
        max_workers=2,
        delay_between_requests=1.0,
        include_competition=True,
        include_category=True,
        timeout=60
    )