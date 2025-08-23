"""
설정 관리 - SQLite3 기반으로 통합 관리
API 설정과 앱 설정을 Foundation DB에서 관리
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    from PySide6.QtCore import QObject, Signal
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    QObject = object
    Signal = None

from .logging import get_logger

logger = get_logger("foundation.config")


@dataclass
class APIConfig:
    """API 설정 데이터 클래스"""
    # 네이버 검색광고 API
    searchad_access_license: str = ""
    searchad_secret_key: str = ""
    searchad_customer_id: str = ""
    
    # 네이버 쇼핑 API
    shopping_client_id: str = ""
    shopping_client_secret: str = ""
    
    # AI API
    openai_api_key: str = ""
    claude_api_key: str = ""
    gemini_api_key: str = ""
    current_ai_model: str = ""  # 현재 선택된 AI 모델
    
    def is_searchad_valid(self) -> bool:
        """검색광고 API 설정 유효성 확인"""
        return all([
            self.searchad_access_license,
            self.searchad_secret_key,
            self.searchad_customer_id
        ])
    
    def is_shopping_valid(self) -> bool:
        """쇼핑 API 설정 유효성 확인"""
        return all([
            self.shopping_client_id,
            self.shopping_client_secret
        ])
    
    def is_complete(self) -> bool:
        """API 설정이 완전한지 확인 (네이버 API 둘 다 필수)"""
        return self.is_searchad_valid() and self.is_shopping_valid()


class ConfigManager(QObject):
    """설정 관리자 - SQLite3 기반"""
    
    # API 설정 변경 시그널 (Qt가 사용 가능할 때만)
    if QT_AVAILABLE:
        api_config_changed = Signal()
        app_config_changed = Signal()
    
    def __init__(self):
        """설정 관리자 초기화 (DB 기반)"""
        if QT_AVAILABLE:
            super().__init__()
        # DB는 지연 로딩 (순환 import 방지)
        self._db = None
    
    def _get_db(self):
        """DB 인스턴스 지연 로딩"""
        if self._db is None:
            from .db import get_db
            self._db = get_db()
        return self._db
    
    def load_api_config(self) -> APIConfig:
        """API 설정 로드 (SQLite3에서)"""
        try:
            db = self._get_db()
            
            # 통합 API 설정 조회
            config_data = db.get_api_config('unified_api_config')
            
            if config_data:
                return APIConfig(**config_data)
            else:
                logger.info("API 설정이 없음, 기본값으로 초기화")
                return APIConfig()
                
        except Exception as e:
            logger.error(f"API 설정 로드 실패: {e}")
            return APIConfig()
    
    def save_api_config(self, config: APIConfig) -> bool:
        """API 설정 저장 (SQLite3에)"""
        try:
            db = self._get_db()
            config_dict = asdict(config)
            
            db.save_api_config('unified_api_config', config_dict)
            logger.info("API 설정 저장 완료")
            
            # API 설정 변경 시그널 발생 (Qt가 사용 가능할 때만)
            if QT_AVAILABLE and hasattr(self, 'api_config_changed'):
                self.api_config_changed.emit()
            
            return True
            
        except Exception as e:
            logger.error(f"API 설정 저장 실패: {e}")
            return False
    
    def load_app_config(self) -> Dict[str, Any]:
        """앱 설정 로드 (SQLite3에서)"""
        try:
            db = self._get_db()
            config_data = db.get_api_config('app_config')
            
            return config_data if config_data else {}
            
        except Exception as e:
            logger.error(f"앱 설정 로드 실패: {e}")
            return {}
    
    def save_app_config(self, config: Dict[str, Any]) -> bool:
        """앱 설정 저장 (SQLite3에)"""
        try:
            db = self._get_db()
            db.save_api_config('app_config', config)
            logger.info("앱 설정 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"앱 설정 저장 실패: {e}")
            return False
    
    def get_env_var(self, key: str, default: str = "") -> str:
        """환경변수 가져오기"""
        return os.getenv(key, default)
    
    def get_database_config(self) -> Dict[str, Any]:
        """데이터베이스 설정 반환"""
        return {
            "path": "data/app.db",  # SQLite3 파일 경로
            "wal_enabled": self.get_env_var("DB_WAL_ENABLED", "true").lower() == "true"
        }
    
    def migrate_from_json_files(self):
        """SQLite3로 마이그레이션"""
        try:
            from pathlib import Path
            import json
            
            config_dir = Path.cwd() / "config"
            api_config_file = config_dir / "api_config.json"
            app_config_file = config_dir / "app_config.json"
            
            # API 설정 마이그레이션
            if api_config_file.exists():
                logger.info("기존 API 설정 파일 발견, SQLite3로 마이그레이션 시작")
                with open(api_config_file, 'r', encoding='utf-8') as f:
                    api_data = json.load(f)
                    api_config = APIConfig(**api_data)
                    self.save_api_config(api_config)
                logger.info("API 설정 마이그레이션 완료")
            
            # 앱 설정 마이그레이션
            if app_config_file.exists():
                logger.info("기존 앱 설정 파일 발견, SQLite3로 마이그레이션 시작")
                with open(app_config_file, 'r', encoding='utf-8') as f:
                    app_data = json.load(f)
                    self.save_app_config(app_data)
                logger.info("앱 설정 마이그레이션 완료")
                
        except Exception as e:
            logger.warning(f"설정 마이그레이션 실패 (무시 가능): {e}")


# 전역 설정 관리자 인스턴스
config_manager = ConfigManager()