"""
로그 설정 및 출력 관리
프로젝트 전체 로깅을 중앙에서 관리
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LogManager:
    """로그 관리자"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """로그 관리자 초기화"""
        if log_dir is None:
            # integrated_management_system 내부의 logs 폴더 (절대 경로)
            current_file = Path(__file__).resolve()  # 현재 파일의 절대 경로
            project_root = current_file.parent.parent.parent  # src/foundation/logging.py -> integrated_management_system
            log_dir = project_root / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """로깅 설정"""
        # 로그 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러 (CRITICAL만 출력 - 거의 출력 안됨)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 파일 핸들러 (일반 로그)
        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 에러 파일 핸들러
        error_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """특정 모듈용 로거 가져오기"""
        return logging.getLogger(name)


# 전역 로그 관리자
log_manager = LogManager()


def get_logger(name: str) -> logging.Logger:
    """로거 가져오기 헬퍼 함수"""
    return log_manager.get_logger(name)


# 주요 모듈별 로거
foundation_logger = get_logger("foundation")
vendor_logger = get_logger("vendors")
toolbox_logger = get_logger("toolbox")
features_logger = get_logger("features")
desktop_logger = get_logger("desktop")