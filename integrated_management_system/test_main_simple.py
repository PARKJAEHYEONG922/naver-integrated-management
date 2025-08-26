"""
메인 앱 간단 테스트 - 키워드 분석과 네이버 카페만
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.foundation.logging import get_logger

logger = get_logger("main")

def load_features_simple(app):
    """간단한 기능 모듈들만 로드"""
    try:
        # 키워드 분석 기능 로드 및 등록
        logger.info("키워드 분석 모듈 로드 시작")
        from src.features.keyword_analysis import register as register_keyword_analysis
        register_keyword_analysis(app)
        logger.info("키워드 분석 모듈 로드 완료")
        
        # 네이버 카페 DB 추출 기능 로드 및 등록
        logger.info("네이버 카페 모듈 로드 시작")
        from src.features.naver_cafe import register as register_naver_cafe
        register_naver_cafe(app)
        logger.info("네이버 카페 모듈 로드 완료")
        
        logger.info("간단한 기능 모듈 로드 완료")
        
    except Exception as e:
        import traceback
        logger.error(f"기능 모듈 로드 실패: {e}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        raise

def main():
    """메인 함수"""
    try:
        logger.info("간단한 통합 관리 시스템 시작")
        
        # 1단계: 공용 DB 초기화
        from src.foundation.db import init_db
        init_db()
        logger.info("공용 데이터베이스 초기화 완료")
        
        # 2단계: 설정 로드 (SQLite3에서)
        from src.foundation.config import config_manager
        api_config = config_manager.load_api_config()
        app_config = config_manager.load_app_config()
        logger.info("설정 로드 완료 (SQLite3 기반)")
        
        # 3단계: API 상태 확인
        from src.desktop.api_checker import check_api_status_on_startup
        check_api_status_on_startup()
        logger.info("API 상태 확인 완료")
        
        # 4단계: 데스크톱 앱 실행
        from src.desktop.app import run_app
        run_app(load_features_simple)
        
    except Exception as e:
        import traceback
        logger.error(f"애플리케이션 시작 실패: {e}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()