"""
순위 추적 ViewModel - UI와 Service 사이의 중간 레이어
UI에서 직접 서비스를 호출하는 대신 ViewModel을 통해 간접 호출
복잡한 UI 로직과 데이터 변환도 여기서 처리
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .service import rank_tracking_service
from .models import TrackingProject, TrackingKeyword
from .adapters import format_date, format_date_with_time
from src.foundation.logging import get_logger

logger = get_logger("features.rank_tracking.view_model")


class RankingTableViewModel:
    """순위 테이블 ViewModel - UI와 Service 사이의 비즈니스 로직 처리"""
    
    def __init__(self):
        self.service = rank_tracking_service
        self.current_project_id: Optional[int] = None
        self.current_project: Optional[TrackingProject] = None
    
    def set_current_project(self, project_id: int) -> bool:
        """현재 프로젝트 설정"""
        try:
            project = self.service.get_project_by_id(project_id)
            if project:
                self.current_project_id = project_id
                self.current_project = project
                return True
            return False
        except Exception as e:
            logger.error(f"프로젝트 설정 실패: {e}")
            return False
    
    def get_current_project(self) -> Optional[TrackingProject]:
        """현재 프로젝트 반환"""
        return self.current_project
    
    def get_project_overview(self, project_id: int) -> Optional[Dict]:
        """프로젝트 개요 조회"""
        try:
            return self.service.get_project_overview(project_id)
        except Exception as e:
            logger.error(f"프로젝트 개요 조회 실패: {e}")
            return None
    
    def get_project_keywords(self, project_id: int) -> List[TrackingKeyword]:
        """프로젝트 키워드 목록 조회"""
        try:
            return self.service.get_project_keywords(project_id)
        except Exception as e:
            logger.error(f"프로젝트 키워드 조회 실패: {e}")
            return []
    
    def delete_ranking_data_by_date(self, project_id: int, date: str) -> bool:
        """날짜별 순위 데이터 삭제"""
        try:
            return self.service.delete_ranking_data_by_date(project_id, date)
        except Exception as e:
            logger.error(f"순위 데이터 삭제 실패: {e}")
            return False
    
    def delete_keyword(self, project_id: int, keyword: str) -> bool:
        """키워드 삭제"""
        try:
            return self.service.delete_keyword(project_id, keyword)
        except Exception as e:
            logger.error(f"키워드 삭제 실패: {e}")
            return False
    
    def analyze_and_add_keyword(self, project_id: int, keyword: str) -> Tuple[bool, str]:
        """키워드 분석 후 추가"""
        try:
            # 키워드 분석
            analysis = self.service.analyze_keyword_for_tracking(keyword)
            if not analysis:
                return False, "키워드 분석에 실패했습니다."
            
            # 키워드 정보 업데이트
            success = self.service.update_keyword_info(
                project_id, keyword, 
                analysis.get('category', ''), 
                analysis.get('monthly_volume', -1)
            )
            
            if success:
                return True, f"키워드 '{keyword}' 추가 완료"
            else:
                return False, "키워드 추가에 실패했습니다."
                
        except Exception as e:
            logger.error(f"키워드 분석/추가 실패: {e}")
            return False, f"오류 발생: {e}"
    
    def add_keyword(self, project_id: int, keyword: str) -> Optional[TrackingKeyword]:
        """키워드 추가"""
        try:
            return self.service.add_keyword(project_id, keyword)
        except Exception as e:
            logger.error(f"키워드 추가 실패: {e}")
            return None
    
    def refresh_project_info(self, project_id: int) -> Tuple[bool, str]:
        """프로젝트 정보 새로고침"""
        try:
            result = self.service.refresh_project_info(project_id)
            if result.get('success', False):
                return True, result.get('message', '새로고침 완료')
            else:
                return False, result.get('message', '새로고침 실패')
        except Exception as e:
            logger.error(f"프로젝트 정보 새로고침 실패: {e}")
            return False, f"오류 발생: {e}"
    
    def prepare_table_data(self, project_id: int) -> Dict[str, Any]:
        """테이블 표시용 데이터 준비 - UI 로직을 여기서 처리"""
        try:
            # 기본 데이터 수집
            project = self.service.get_project_by_id(project_id)
            if not project:
                return {"success": False, "message": "프로젝트를 찾을 수 없습니다."}
            
            overview = self.service.get_project_overview(project_id)
            keywords = self.service.get_project_keywords(project_id)
            
            # 날짜 목록 정리 및 헤더 생성
            dates = overview.get('dates', []) if overview else []
            all_dates = dates[:10] if dates else []  # 최대 10개
            
            # 헤더 구성
            headers = ["", "키워드", "카테고리", "월검색량"]
            for date in all_dates:
                headers.append(format_date(date))
            
            # 마지막 확인 시간
            last_check_time = ""
            if dates:
                last_check_time = f"마지막 확인: {format_date_with_time(dates[0])}"
            else:
                last_check_time = "마지막 확인: -"
            
            # 프로젝트 카테고리 기본 형태 (색상 매칭용)
            project_category_base = ""
            if hasattr(project, 'category') and project.category:
                project_category_base = project.category.split(' > ')[-1] if ' > ' in project.category else project.category
            
            return {
                "success": True,
                "project": project,
                "keywords": keywords,
                "headers": headers,
                "dates": all_dates,
                "last_check_time": last_check_time,
                "project_category_base": project_category_base,
                "overview": overview
            }
            
        except Exception as e:
            logger.error(f"테이블 데이터 준비 실패: {e}")
            return {"success": False, "message": f"오류 발생: {e}"}
    
    def get_current_project_keywords_for_analysis(self, project_id: int) -> Tuple[bool, List[str]]:
        """키워드 분석을 위한 현재 프로젝트 키워드 목록 조회"""
        try:
            keywords = self.service.get_project_keywords(project_id)
            keyword_texts = [kw.keyword for kw in keywords if hasattr(kw, 'keyword')]
            return True, keyword_texts
        except Exception as e:
            logger.error(f"키워드 목록 조회 실패: {e}")
            return False, []


# 전역 ViewModel 인스턴스
ranking_table_view_model = RankingTableViewModel()