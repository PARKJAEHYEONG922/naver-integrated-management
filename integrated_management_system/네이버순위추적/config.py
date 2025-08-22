"""
순위 추적 기능별 설정
"""
from dataclasses import dataclass
from typing import Optional


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


# 기본 설정
default_config = RankTrackingConfig()


def load_rank_tracking_config() -> RankTrackingConfig:
    """순위 추적 설정 로드 (향후 파일/DB에서 로드 가능)"""
    # TODO: 실제로는 설정 파일이나 DB에서 로드
    return default_config


def save_rank_tracking_config(config: RankTrackingConfig) -> bool:
    """순위 추적 설정 저장"""
    # TODO: 설정 파일이나 DB에 저장
    return True