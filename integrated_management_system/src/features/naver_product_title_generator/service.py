"""
네이버 상품명 생성기 서비스
세션 관리 및 간단한 오케스트레이션
"""
from typing import Optional
from datetime import datetime

from src.foundation.logging import get_logger
from src.foundation.exceptions import BaseApplicationError

from .models import SessionData, create_new_session, validate_product_name, repository

logger = get_logger("features.naver_product_title_generator.service")


class ProductTitleGeneratorService:
    """상품명 생성기 메인 서비스 (간소화)"""
    
    def __init__(self):
        self.current_session: Optional[SessionData] = None
    
    def start_new_session(self, product_name: str) -> SessionData:
        """새 세션 시작"""
        try:
            # 입력 검증
            if not validate_product_name(product_name):
                raise BaseApplicationError("유효하지 않은 제품명입니다. 2-100자 사이로 입력해주세요.")
            
            # 텍스트 정리
            cleaned_name = product_name.strip()
            if not cleaned_name:
                raise BaseApplicationError("제품명이 비어있습니다.")
            
            # 새 세션 생성
            self.current_session = create_new_session(cleaned_name)
            
            logger.info(f"새 세션 시작: {self.current_session.session_id} - {cleaned_name}")
            return self.current_session
            
        except Exception as e:
            logger.error(f"세션 시작 실패: {e}")
            raise BaseApplicationError(f"세션 시작에 실패했습니다: {e}")
    
    def get_current_session(self) -> Optional[SessionData]:
        """현재 세션 조회"""
        return self.current_session
    
    def reset_session(self):
        """세션 초기화"""
        self.current_session = None
        logger.info("세션이 초기화되었습니다")
    
    def save_session(self) -> bool:
        """현재 세션 저장"""
        try:
            if self.current_session:
                repository.save_session(self.current_session)
                logger.info(f"세션 저장 완료: {self.current_session.session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"세션 저장 실패: {e}")
            return False


# 전역 서비스 인스턴스
product_title_service = ProductTitleGeneratorService()