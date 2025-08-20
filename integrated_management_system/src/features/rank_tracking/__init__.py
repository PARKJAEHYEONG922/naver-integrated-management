"""
순위 추적 피처 모듈
네이버 쇼핑 키워드 순위 추적 및 관리 기능

피처 등록:
def register(app):
    # 앱에 순위 추적 기능 등록
"""
from .ui_main import RankTrackingWidget
from .service import rank_tracking_service
from .models import TrackingProject, TrackingKeyword


def register(app):
    """앱에 네이버상품 순위추적 기능 등록"""
    try:
        # 메인 앱의 탭에 순위 추적 위젯 추가
        rank_widget = RankTrackingWidget()
        app.add_feature_tab(rank_widget, "네이버상품 순위추적")
        
        # 로깅
        from src.foundation.logging import get_logger
        logger = get_logger("features.rank_tracking")
        logger.info("네이버상품 순위추적 피처 등록 완료")
        
    except Exception as e:
        from src.foundation.logging import get_logger
        logger = get_logger("features.rank_tracking")
        logger.error(f"네이버상품 순위추적 피처 등록 실패: {e}")