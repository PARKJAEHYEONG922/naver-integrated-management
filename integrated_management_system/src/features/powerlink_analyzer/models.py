"""
파워링크 분석기 데이터 모델
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class BidPosition:
    """입찰가와 위치 정보"""
    position: int  # 순위 (1위, 2위, ...)
    bid_price: int  # 입찰가 (원)


@dataclass
class KeywordAnalysisResult:
    """키워드 분석 결과"""
    keyword: str
    pc_search_volume: int       # PC 월검색량 
    mobile_search_volume: int   # Mobile 월검색량
    
    # PC 데이터
    pc_clicks: float  # PC 월평균 클릭수
    pc_ctr: float     # PC 월평균 클릭률 (%)
    pc_first_page_positions: int  # PC 1페이지 노출 위치 수
    pc_first_position_bid: int    # PC 1등 광고비
    pc_min_exposure_bid: int      # PC 최소노출가격
    pc_bid_positions: List[BidPosition]  # PC 입찰가 리스트
    
    # 모바일 데이터  
    mobile_clicks: float  # 모바일 월평균 클릭수
    mobile_ctr: float     # 모바일 월평균 클릭률 (%)
    mobile_first_page_positions: int  # 모바일 1페이지 노출 위치 수
    mobile_first_position_bid: int    # 모바일 1등 광고비
    mobile_min_exposure_bid: int      # 모바일 최소노출가격
    mobile_bid_positions: List[BidPosition]  # 모바일 입찰가 리스트
    
    # 추천순위 (실시간 계산됨)
    pc_recommendation_rank: int = 0
    mobile_recommendation_rank: int = 0
    
    # 분석 시간
    analyzed_at: datetime = None
    
    def __post_init__(self):
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now()


@dataclass
class AnalysisProgress:
    """분석 진행 상황"""
    current: int = 0
    total: int = 0
    current_keyword: str = ""
    status: str = "대기 중"
    current_step: str = ""  # 현재 진행 중인 세부 단계
    step_detail: str = ""   # 단계별 상세 정보
    _percentage: int = 0    # 직접 설정 가능한 백분율
    
    @property
    def percentage(self) -> int:
        # 직접 설정된 값이 있으면 사용, 없으면 계산
        if self._percentage > 0:
            return self._percentage
        if self.total == 0:
            return 0
        return int((self.current / self.total) * 100)
    
    @percentage.setter
    def percentage(self, value: int):
        """백분율 직접 설정"""
        self._percentage = value
    
    @property 
    def detailed_status(self) -> str:
        """상세한 상태 메시지"""
        if self.current_keyword and self.current_step:
            if self.step_detail:
                return f"{self.current_keyword} - {self.current_step} ({self.step_detail})"
            else:
                return f"{self.current_keyword} - {self.current_step}"
        elif self.current_keyword:
            return f"{self.current_keyword} - {self.status}"
        else:
            return self.status


# Repository 패턴 (CLAUDE.md Service → DB 분리)
class PowerLinkRepository:
    """PowerLink 분석 데이터 저장소 (Repository 패턴)"""
    
    def __init__(self):
        self._db = None
    
    @property
    def db(self):
        """DB 인스턴스 지연 로드"""
        if self._db is None:
            from src.foundation.db import get_db
            self._db = get_db()
        return self._db
    
    def list_sessions(self) -> list:
        """히스토리 세션 목록 조회"""
        return self.db.list_powerlink_sessions()
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """세션 정보 조회"""
        return self.db.get_powerlink_session(session_id)
    
    def get_session_keywords(self, session_id: int) -> Optional[Dict]:
        """세션 키워드 데이터 조회"""
        return self.db.get_powerlink_session_keywords(session_id)
    
    def delete_sessions(self, session_ids: list) -> bool:
        """세션 삭제"""
        return self.db.delete_powerlink_sessions(session_ids)
    
    def save_analysis_session(self, keywords_data: dict, session_name: str = None) -> int:
        """분석 세션 저장"""
        return self.db.save_powerlink_analysis_session(keywords_data, session_name)
    
    def check_duplicate_session_24h(self, keywords_data: dict) -> bool:
        """24시간 내 중복 세션 체크"""
        return self.db.check_powerlink_session_duplicate_24h(keywords_data)
    
    def get_analysis_sessions(self) -> List[dict]:
        """분석 세션 목록 조회 (히스토리용)"""
        try:
            sessions = self.list_sessions()
            # 히스토리 테이블에 맞는 형식으로 변환
            formatted_sessions = []
            for session in sessions:
                # created_at을 ISO 문자열로 보장
                raw_dt = session.get('created_at', '')
                if isinstance(raw_dt, datetime):
                    created_at = raw_dt.isoformat()
                else:
                    created_at = str(raw_dt) if raw_dt is not None else ''

                formatted_sessions.append({
                    'id': session.get('id'),                   # DB에서 반환하는 실제 키 사용
                    'session_id': session.get('id'),           # 호환성을 위해 유지 (같은 값)
                    'name': session.get('session_name', ''),   # UI가 기대하는 'name' 키 추가
                    'session_name': session.get('session_name', ''),  # 호환성을 위해 유지
                    'created_at': created_at,                  # ← UI가 읽는 표준 키
                    'keyword_count': session.get('keyword_count', 0)
                })
            return formatted_sessions
        except Exception as e:
            from src.foundation.logging import get_logger
            logger = get_logger("features.powerlink_analyzer.models")
            logger.error(f"분석 세션 목록 조회 실패: {e}")
            return []


# 완료 판단 기준 - 단일 출처 (Single Source of Truth)
MISSING_INT = -1      # 미수집/확정불가
MISSING_FLOAT = -1.0  # 미수집/확정불가

# 기본값 (크롤링 실패 시 사용하는 합리적 기본값)
DEFAULT_PC_POSITIONS = 8
DEFAULT_MOBILE_POSITIONS = 4


def is_nonneg(v) -> bool:
    """값이 0 이상인지 확인 (None과 음수는 False)"""
    return v is not None and v >= 0


def is_completed(result: "KeywordAnalysisResult") -> bool:
    """
    키워드 분석 완료 판단 기준을 한 곳에서 정의
    
    완성 기준:
    - 기본 데이터(검색량/클릭/CTR)가 0 이상
    - 1p 노출 포지션 수가 0 이상 (크롤 실패 시에도 기본값 8/4는 허용)
    - 최소노출가/1등가가 '수집 실패'가 아닌 값(>=0)
      (엑셀/랭킹에서 0도 합리적인 값으로 취급, 구분 필요시 MISSING_*로 -1 사용)
    """
    return all([
        is_nonneg(result.pc_search_volume),
        is_nonneg(result.mobile_search_volume),
        is_nonneg(result.pc_clicks),
        is_nonneg(result.pc_ctr),
        is_nonneg(result.mobile_clicks),
        is_nonneg(result.mobile_ctr),
        is_nonneg(result.pc_first_page_positions),
        is_nonneg(result.mobile_first_page_positions),
        is_nonneg(result.pc_first_position_bid),
        is_nonneg(result.pc_min_exposure_bid),
        is_nonneg(result.mobile_first_position_bid),
        is_nonneg(result.mobile_min_exposure_bid),
    ])