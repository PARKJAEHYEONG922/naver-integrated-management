"""
네이버 카페 DB 추출기 서비스
비즈니스 로직과 오케스트레이션 담당
"""
from typing import List, Dict, Optional, Callable
from datetime import datetime

from src.foundation.logging import get_logger
from .models import (
    CafeInfo, BoardInfo, ExtractedUser, ExtractionTask, 
    ExtractionProgress, ExtractionStatus, ExtractionResult,
    cafe_extraction_db
)
from .adapters import NaverCafeDataAdapter
from .config import CAFE_EXTRACTION_CONFIG, NAVER_CAFE_PATTERNS, ERROR_MESSAGES, SUCCESS_MESSAGES

logger = get_logger("features.naver_cafe.service")


class NaverCafeExtractionService:
    """네이버 카페 추출 서비스"""
    
    def __init__(self):
        self.adapter = NaverCafeDataAdapter()
        # 추출 관련 변수는 worker.py에서 관리
        
    # set_callbacks 메서드 제거 - worker.py에서 직접 처리
    
    async def search_cafes(self, query: str, browser_context=None) -> List[CafeInfo]:
        """카페 검색 - 비즈니스 로직"""
        try:
            logger.info(f"카페 검색 시작: {query}")
            
            # 단순히 adapters 호출만 (URL 패턴 구분 제거)
            cafes = await self.adapter.search_cafes_by_name(query, browser_context)
            logger.info(f"카페 검색 완료: {len(cafes)}개 발견")
            return cafes
                
        except Exception as e:
            logger.error(f"카페 검색 실패: {e}")
            return []
    
    async def get_boards_for_cafe(self, cafe_info: CafeInfo, browser_context=None) -> List[BoardInfo]:
        """게시판 목록 조회 - 비즈니스 로직"""
        try:
            logger.info(f"게시판 목록 조회 시작: {cafe_info.name}")
            
            # 단순히 adapters 호출만
            boards = await self.adapter.get_cafe_boards(cafe_info, browser_context)
            logger.info(f"게시판 목록 조회 완료: {len(boards)}개 발견")
            return boards
            
        except Exception as e:
            logger.error(f"게시판 목록 조회 실패: {e}")
            return []
    
    # start_extraction 메서드 제거 - worker.py에서 직접 처리
    
    # stop_extraction 메서드 제거 - worker.py에서 직접 처리
    
    # _perform_extraction 메서드 제거 - worker.py에서 직접 처리
    
    def get_extraction_history(self) -> List[ExtractionTask]:
        """추출 기록 조회"""
        return cafe_extraction_db.get_extraction_history()
    
    def get_extracted_users(self) -> List[ExtractedUser]:
        """추출된 사용자 목록 조회"""
        return cafe_extraction_db.get_all_users()
    
    def clear_all_data(self):
        """모든 데이터 초기화"""
        cafe_extraction_db.clear_all()
        logger.info("모든 추출 데이터 초기화 완료")
    
    def export_to_excel(self, file_path: str, users: List[ExtractedUser]) -> bool:
        """엑셀로 내보내기"""
        try:
            return self.adapter.export_users_to_excel(file_path, users)
        except Exception as e:
            logger.error(f"엑셀 내보내기 실패: {e}")
            return False
    
    def export_to_meta_csv(self, file_path: str, users: List[ExtractedUser]) -> bool:
        """Meta CSV로 내보내기"""
        try:
            return self.adapter.export_users_to_meta_csv(file_path, users)
        except Exception as e:
            logger.error(f"Meta CSV 내보내기 실패: {e}")
            return False
    
    
    def get_statistics(self) -> Dict:
        """추출 통계 조회"""
        history = self.get_extraction_history()
        users = self.get_extracted_users()
        
        total_tasks = len(history)
        completed_tasks = len([task for task in history if task.status == ExtractionStatus.COMPLETED])
        failed_tasks = len([task for task in history if task.status == ExtractionStatus.FAILED])
        
        total_users = len(users)
        unique_users = len(set(user.user_id for user in users))
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_users": total_users,
            "unique_users": unique_users
        }