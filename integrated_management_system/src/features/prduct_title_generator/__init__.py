"""
네이버 상품명 생성기 모듈
- 네이버 개발자 API로 상위 상품명 수집
- AI 토큰화를 통한 키워드 추출
- SEO 최적화된 상품명 자동 생성

피처 등록:
def register(app):
    # 앱에 네이버 상품명 생성기 기능 등록
"""
from .ui_main import ProductTitleGeneratorWidget
from .service import product_title_service
from .models import AnalysisResult, GeneratedTitle


def register(app):
    """앱에 네이버 상품명 생성기 기능 등록"""
    try:
        # 메인 앱의 탭에 상품명 생성기 위젯 추가
        title_generator_widget = ProductTitleGeneratorWidget()
        app.add_feature_tab(title_generator_widget, "네이버 상품명 만들기")
        
        # 로깅
        from src.foundation.logging import get_logger
        logger = get_logger("features.prduct_title_generator")
        logger.info("네이버 상품명 생성기 피처 등록 완료")
        
    except Exception as e:
        from src.foundation.logging import get_logger
        logger = get_logger("features.prduct_title_generator")
        logger.error(f"네이버 상품명 생성기 피처 등록 실패: {e}")
        raise