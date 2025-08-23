"""
통합 관리 시스템 메인 진입점
플러그인 로딩 및 애플리케이션 시작
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.foundation.logging import get_logger
from src.foundation.config import config_manager

logger = get_logger("main")


def load_features(app):
    """기능 모듈들 로드 및 등록"""
    try:
        # 키워드 분석 기능 로드 및 등록
        logger.info("키워드 분석 모듈 로드 시작")
        from src.features.keyword_analysis import register as register_keyword_analysis
        register_keyword_analysis(app)
        logger.info("키워드 분석 모듈 로드 완료")
        
        # 네이버상품 순위추적 기능 로드 및 등록
        logger.info("순위추적 모듈 로드 시작")
        from src.features.rank_tracking import register as register_rank_tracking
        register_rank_tracking(app)
        logger.info("순위추적 모듈 로드 완료")
        
        # 네이버 카페 DB 추출 기능 로드 및 등록
        logger.info("네이버 카페 모듈 로드 시작")
        from src.features.naver_cafe import register as register_naver_cafe
        register_naver_cafe(app)
        logger.info("네이버 카페 모듈 로드 완료")
        
        # PowerLink 분석기 기능 로드 및 등록
        logger.info("PowerLink 분석기 모듈 로드 시작")
        from src.features.powerlink_analyzer import register as register_powerlink
        register_powerlink(app)
        logger.info("PowerLink 분석기 모듈 로드 완료")
        
        # 네이버 상품명 생성기 기능 로드 및 등록
        logger.info("네이버 상품명 생성기 모듈 로드 시작")
        from src.features.naver_product_title_generator.ui_main import NaverProductTitleGeneratorWidget
        naver_product_widget = NaverProductTitleGeneratorWidget()
        app.add_feature_tab(naver_product_widget, "네이버 상품명 생성기")
        logger.info("네이버 상품명 생성기 모듈 로드 완료")
        
        logger.info("모든 기능 모듈 로드 및 등록 완료")
        
    except Exception as e:
        import traceback
        logger.error(f"기능 모듈 로드 실패: {e}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        raise


def main():
    """메인 함수"""
    try:
        logger.info("통합 관리 시스템 시작")
        
        # 1단계: 공용 DB 초기화
        from src.foundation.db import init_db
        init_db()  # 공용 DB 초기화 (모든 모듈이 사용)
        logger.info("공용 데이터베이스 초기화 완료")
        
        # 2단계: 설정 로드 (SQLite3에서)
        api_config = config_manager.load_api_config()
        app_config = config_manager.load_app_config()
        logger.info("설정 로드 완료 (SQLite3 기반)")
        
        # 3단계: API 상태 확인 (모듈 로드 전에 수행)
        from src.desktop.api_checker import check_api_status_on_startup
        check_api_status_on_startup()
        logger.info("API 상태 확인 완료")
        
        # 4단계: 데스크톱 앱 실행
        from src.desktop.app import run_app
        run_app(load_features)
        
    except Exception as e:
        logger.error(f"애플리케이션 시작 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()