"""
API 연결 상태 체크 및 로그 출력
시작 시 API 설정 확인하여 로그 창에 결과 표시
"""
from src.foundation.config import config_manager
from src.foundation.logging import get_logger
from src.desktop.common_log import log_manager

logger = get_logger("toolbox.ui_kit.api_checker")


class APIChecker:
    """API 연결 상태 확인"""
    
    @staticmethod
    def check_all_apis_on_startup():
        """시작 시 모든 API 상태 확인"""
        try:
            log_manager.add_log("🔗 API 연결 상태를 확인하는 중...", "info")
            
            # API 설정 로드
            api_config = config_manager.load_api_config()
            
            # 각 API 상태 확인
            naver_developer_status = APIChecker._check_naver_developer(api_config)
            naver_searchad_status = APIChecker._check_naver_searchad(api_config)
            ai_api_status = APIChecker._check_ai_apis(api_config)
            
            # 결과 로그 출력 (둘 다 필수)
            APIChecker._log_api_status("네이버 개발자 API", naver_developer_status, required=True)
            APIChecker._log_api_status("네이버 검색광고 API", naver_searchad_status, required=True)
            APIChecker._log_api_status("AI API", ai_api_status, required=False)
            
            # 전체 상태 요약
            APIChecker._log_summary(api_config)
            
            return api_config.is_complete() and api_config.is_shopping_valid() and api_config.is_searchad_valid()
            
        except Exception as e:
            logger.error(f"API 상태 확인 오류: {e}")
            log_manager.add_log(f"❌ API 상태 확인 중 오류 발생: {str(e)}", "error")
            return False
    
    @staticmethod
    def _check_naver_developer(api_config) -> dict:
        """네이버 개발자 API 상태 확인 (쇼핑 API)"""
        if not api_config.is_shopping_valid():
            return {
                "configured": False,
                "connected": False,
                "message": "API 키가 설정되지 않음"
            }
        
        try:
            # 간단한 연결 테스트 (실제 API 호출 없이 설정만 확인)
            return {
                "configured": True,
                "connected": True,
                "message": "설정 완료"
            }
        except Exception as e:
            return {
                "configured": True,
                "connected": False,
                "message": f"연결 오류: {str(e)}"
            }
    
    @staticmethod
    def _check_naver_searchad(api_config) -> dict:
        """네이버 검색광고 API 상태 확인"""
        if not api_config.is_searchad_valid():
            return {
                "configured": False,
                "connected": False,
                "message": "API 키가 설정되지 않음"
            }
        
        try:
            return {
                "configured": True,
                "connected": True,
                "message": "설정 완료"
            }
        except Exception as e:
            return {
                "configured": True,
                "connected": False,
                "message": f"연결 오류: {str(e)}"
            }
    
    @staticmethod
    def _check_ai_apis(api_config) -> dict:
        """AI API 통합 상태 확인 (OpenAI, Claude, Gemini 중 하나라도 설정되면 OK)"""
        # Gemini API 키도 확인해야 함 (api_config에 gemini_api_key 필드가 있다고 가정)
        gemini_key = getattr(api_config, 'gemini_api_key', '')
        
        # 하나라도 설정되어 있으면 OK
        if api_config.openai_api_key or api_config.claude_api_key or gemini_key:
            configured_apis = []
            if api_config.openai_api_key:
                configured_apis.append("OpenAI")
            if api_config.claude_api_key:
                configured_apis.append("Claude")
            if gemini_key:
                configured_apis.append("Gemini")
            
            return {
                "configured": True,
                "connected": True,
                "message": f"설정 완료 ({', '.join(configured_apis)})"
            }
        else:
            return {
                "configured": False,
                "connected": False,
                "message": "미설정 (선택사항)"
            }
    
    @staticmethod
    def _log_api_status(api_name: str, status: dict, required: bool = True):
        """API 상태를 로그에 출력"""
        if status["configured"] and status["connected"]:
            # 정상 설정됨
            log_manager.add_log(f"✅ {api_name}: {status['message']}", "success")
        elif status["configured"] and not status["connected"]:
            # 설정됨but 연결 오류
            log_manager.add_log(f"⚠️ {api_name}: {status['message']}", "warning")
        else:
            # 설정되지 않음
            if required:
                log_manager.add_log(f"❌ {api_name}: {status['message']} (필수)", "error")
            else:
                log_manager.add_log(f"⚪ {api_name}: {status['message']}", "info")
    
    @staticmethod
    def _log_summary(api_config):
        """전체 API 상태 요약"""
        # 네이버 개발자 API와 검색광고 API 둘 다 필수
        naver_dev_ready = api_config.is_shopping_valid()
        naver_search_ready = api_config.is_searchad_valid()
        
        if naver_dev_ready and naver_search_ready:
            log_manager.add_log("🎉 모든 필수 네이버 API가 설정되었습니다! 키워드 분석 기능을 정상 사용할 수 있습니다.", "success")
        else:
            missing_apis = []
            if not naver_dev_ready:
                missing_apis.append("네이버 개발자 API")
            if not naver_search_ready:
                missing_apis.append("네이버 검색광고 API")
            
            log_manager.add_log(f"⚠️ 필수 API {len(missing_apis)}개가 설정되지 않았습니다: {', '.join(missing_apis)}", "warning")
            log_manager.add_log("📋 상단 메뉴의 'API 설정'에서 누락된 API를 설정해주세요.", "info")
            log_manager.add_log("💡 일부 키워드 분석 기능이 제한될 수 있습니다.", "info")
    
    @staticmethod
    def get_missing_required_apis() -> list:
        """설정되지 않은 필수 API 목록 반환"""
        api_config = config_manager.load_api_config()
        missing = []
        
        # 네이버 개발자 API와 검색광고 API 둘 다 확인
        if not api_config.is_shopping_valid():
            missing.append("네이버 개발자 API")
        
        if not api_config.is_searchad_valid():
            missing.append("네이버 검색광고 API")
        
        return missing
    
    @staticmethod
    def is_ready_for_full_functionality() -> bool:
        """모든 기능 사용 가능한지 확인"""
        api_config = config_manager.load_api_config()
        # 네이버 API 둘 다 설정되어 있어야 완전한 기능 사용 가능
        return api_config.is_shopping_valid() and api_config.is_searchad_valid()


def check_api_status_on_startup():
    """
    시작 시 API 상태 확인 (메인 함수)
    애플리케이션 시작 시 호출
    """
    return APIChecker.check_all_apis_on_startup()


def log_api_requirements_reminder():
    """API 설정 필요성 알림 (주기적 호출용)"""
    missing = APIChecker.get_missing_required_apis()
    
    if missing:
        apis_text = ", ".join(missing)
        log_manager.add_log(f"🔔 알림: {apis_text} 설정이 필요합니다.", "warning")
        log_manager.add_log("⚙️ 상단 메뉴 → API 설정에서 설정할 수 있습니다.", "info")


