"""
키워드 분석 기능
네이버 API를 통한 키워드 검색량, 경쟁강도, 카테고리 분석
"""

from .service import KeywordAnalysisService

def register(app):
    """애플리케이션에 키워드 분석 기능 등록"""
    from src.foundation.logging import get_logger
    
    logger = get_logger("features.keyword_analysis")
    
    try:
        # 키워드 분석은 DB를 사용하지 않음 (메모리 기반)
        from .ui_main import KeywordAnalysisWidget
        
        # 키워드 분석 위젯 생성
        widget = KeywordAnalysisWidget()
        
        # 앱에 탭으로 추가 (기존 키워드 검색기 탭을 교체)
        app.add_feature_tab(widget, "키워드 검색기")
        
        logger.info("키워드 분석 기능이 등록되었습니다")
        
    except Exception as e:
        logger.error(f"키워드 분석 기능 등록 실패: {e}")
        raise

# 외부 노출 인터페이스
__all__ = ['KeywordAnalysisService', 'register']