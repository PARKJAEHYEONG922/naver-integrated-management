"""
파워링크 광고비 분석기 서비스 레이어
오케스트레이션(검증→벤더→가공→저장/엑셀) 담당
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from src.foundation.logging import get_logger
from src.desktop.common_log import log_manager
from src.toolbox.text_utils import validate_url
from src.toolbox.text_utils import parse_keywords_from_text, process_keywords

from .adapters import PowerLinkDataAdapter, powerlink_excel_exporter
from .models import KeywordAnalysisResult, AnalysisProgress, PowerLinkRepository

logger = get_logger("features.powerlink_analyzer.service")


class KeywordDatabase:
    """키워드 분석 결과 저장소 - service 레이어에서 관리 (CLAUDE.md 준수)"""
    
    def __init__(self):
        self.keywords: Dict[str, KeywordAnalysisResult] = {}
        
    def add_keyword(self, result: KeywordAnalysisResult):
        """키워드 분석 결과 추가"""
        self.keywords[result.keyword] = result
        
    def remove_keyword(self, keyword: str):
        """키워드 제거"""
        if keyword in self.keywords:
            del self.keywords[keyword]
            
    def get_keyword(self, keyword: str) -> Optional[KeywordAnalysisResult]:
        """키워드 분석 결과 조회"""
        return self.keywords.get(keyword)
        
    def get_all_keywords(self) -> List[KeywordAnalysisResult]:
        """모든 키워드 분석 결과 조회"""
        return list(self.keywords.values())
        
    def clear(self):
        """모든 데이터 삭제"""
        self.keywords.clear()
        
    def _calculate_hybrid_rankings(self, device_type: str, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """하이브리드 방식 추천순위 계산 (통합 메서드)"""
        all_keywords = self.get_all_keywords()
        
        # 완전한 데이터가 있는 키워드들만 필터링 (분석 완료된 것들만)
        keywords = []
        for keyword in all_keywords:
            if device_type == 'pc':
                # PC 데이터가 모두 유효한 경우만 포함
                if (keyword.pc_search_volume >= 0 and 
                    keyword.pc_clicks >= 0 and 
                    keyword.pc_ctr >= 0 and
                    keyword.pc_min_exposure_bid > 0):
                    keywords.append(keyword)
            else:  # mobile
                # 모바일 데이터가 모두 유효한 경우만 포함
                if (keyword.mobile_search_volume >= 0 and 
                    keyword.mobile_clicks >= 0 and 
                    keyword.mobile_ctr >= 0 and
                    keyword.mobile_min_exposure_bid > 0):
                    keywords.append(keyword)
        
        # 유효한 키워드가 없으면 빈 리스트 반환
        if not keywords:
            return all_keywords
        
        def hybrid_efficiency_score(result: KeywordAnalysisResult) -> float:
            # device_type에 따라 필드 선택
            if device_type == 'pc':
                min_exposure_bid = result.pc_min_exposure_bid
                clicks = result.pc_clicks
                ctr = result.pc_ctr
            else:  # mobile
                min_exposure_bid = result.mobile_min_exposure_bid
                clicks = result.mobile_clicks
                ctr = result.mobile_ctr
            
            # 디바이스별 검색량 선택
            device_search_volume = result.pc_search_volume if device_type == 'pc' else result.mobile_search_volume
            
            # 예외 처리: 필수 값들이 0이거나 None인 경우
            if (min_exposure_bid == 0 or 
                clicks == 0 or 
                device_search_volume == 0 or 
                ctr == 0):
                return 0.0
                
            try:
                # 현실성 점수: 원당 예상 클릭수
                score_clicks = clicks / min_exposure_bid
                
                # 잠재력 점수: 원당 이론적 클릭 가능성 (디바이스별 검색량 사용)
                score_demand = (device_search_volume * ctr / 100.0) / min_exposure_bid
                
                # 하이브리드 최종 점수
                final_score = alpha * score_clicks + (1 - alpha) * score_demand
                
                return final_score
                
            except (ZeroDivisionError, TypeError, AttributeError):
                return 0.0
        
        # 키워드별 점수 계산하여 정렬
        keyword_scores = []
        for keyword in keywords:
            score = hybrid_efficiency_score(keyword)
            keyword_scores.append((keyword, score))
        
        # device_type에 따라 정렬 기준의 최소노출가격 필드 선택
        min_bid_field = 'pc_min_exposure_bid' if device_type == 'pc' else 'mobile_min_exposure_bid'
        
        # 디바이스별 검색량 필드 선택
        search_volume_field = 'pc_search_volume' if device_type == 'pc' else 'mobile_search_volume'
        
        # 정렬: 점수 높은 순 → 디바이스별 검색량 높은 순 → 최소노출가격 낮은 순 → 키워드명 순
        sorted_keywords = sorted(keyword_scores, key=lambda x: (
            -x[1],  # 효율성 점수 (높은 순)
            -getattr(x[0], search_volume_field),  # 디바이스별 검색량 (높은 순)
            getattr(x[0], min_bid_field),  # 최소노출가격 (낮은 순)
            x[0].keyword  # 키워드명 (사전순)
        ))
        
        # 키워드 리스트만 추출
        sorted_keywords = [keyword for keyword, score in sorted_keywords]
        
        # 먼저 모든 키워드의 순위를 -1로 초기화 (분석 대기 상태)
        for keyword in all_keywords:
            if device_type == 'pc':
                keyword.pc_recommendation_rank = -1
            else:  # mobile
                keyword.mobile_recommendation_rank = -1
        
        # 유효한 키워드들에만 순위 할당
        for i, keyword in enumerate(sorted_keywords):
            if device_type == 'pc':
                keyword.pc_recommendation_rank = i + 1
            else:  # mobile
                keyword.mobile_recommendation_rank = i + 1
            
        return all_keywords
        
    def calculate_pc_rankings(self, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """PC 추천순위 계산 및 반환 (하이브리드 방식)"""
        return self._calculate_hybrid_rankings('pc', alpha)
        
    def calculate_mobile_rankings(self, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """모바일 추천순위 계산 및 반환 (하이브리드 방식)"""
        return self._calculate_hybrid_rankings('mobile', alpha)
        
    def recalculate_all_rankings(self):
        """모든 순위 재계산"""
        self.calculate_pc_rankings()
        self.calculate_mobile_rankings()


# 전역 키워드 데이터베이스 인스턴스 - service 레이어에서 관리
keyword_database = KeywordDatabase()


class PowerLinkAnalysisService:
    """파워링크 광고비 분석 서비스"""
    
    def __init__(self):
        self.adapter = PowerLinkDataAdapter()
        self.repository = PowerLinkRepository()
        
    def validate_keywords(self, keywords_text: str) -> Tuple[bool, List[str], str]:
        """
        키워드 입력 검증
        
        Returns:
            (유효성, 정제된 키워드 리스트, 에러 메시지)
        """
        try:
            if not keywords_text or not keywords_text.strip():
                return False, [], "키워드를 입력해주세요."
            
            # 텍스트에서 키워드 파싱 (toolbox 공용 함수 사용)
            keywords = parse_keywords_from_text(keywords_text)
            
            if not keywords:
                return False, [], "유효한 키워드가 없습니다."
            
            # 키워드 수 제한 검증
            if len(keywords) > 50:
                return False, [], "키워드는 최대 50개까지 입력 가능합니다."
            
            # 키워드 정제 (toolbox 공용 함수 사용)
            processed_keywords = process_keywords(keywords)
            
            return True, processed_keywords, ""
            
        except Exception as e:
            error_msg = f"키워드 검증 실패: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
    
    def check_api_availability(self) -> Tuple[bool, str]:
        """
        API 가용성 확인
        
        Returns:
            (사용 가능 여부, 메시지)
        """
        try:
            if not self.adapter.is_api_configured():
                return False, "네이버 검색광고 API가 설정되지 않았습니다."
            
            return True, "API 사용 가능"
            
        except Exception as e:
            error_msg = f"API 상태 확인 실패: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def analyze_keywords(self, keywords: List[str], progress_callback=None) -> Dict[str, KeywordAnalysisResult]:
        """
        키워드 분석 실행 (service에서 오케스트레이션만, 실제 분석은 worker에서)
        
        Args:
            keywords: 분석할 키워드 리스트
            progress_callback: 진행률 콜백 함수
            
        Returns:
            키워드별 분석 결과 딕셔너리
        """
        try:
            if progress_callback:
                progress_callback(AnalysisProgress(
                    current_keyword="",
                    progress=0,
                    total_keywords=len(keywords),
                    status="분석 시작",
                    is_completed=False
                ))
            
            # 실제 분석은 worker에서 처리하므로, 여기서는 초기화만
            results = {}
            
            log_manager.add_log(f"파워링크 분석 시작: {len(keywords)}개 키워드", "info")
            logger.info(f"파워링크 분석 시작: {keywords}")
            
            return results
            
        except Exception as e:
            error_msg = f"키워드 분석 실행 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            raise
    
    def calculate_recommendation_ranks(self, keywords_data: Dict[str, KeywordAnalysisResult]) -> Dict[str, KeywordAnalysisResult]:
        """
        추천순위 계산 (하이브리드 방식)
        
        Args:
            keywords_data: 키워드별 분석 결과
            
        Returns:
            추천순위가 계산된 키워드 데이터
        """
        try:
            if not keywords_data:
                return keywords_data
            
            # PC 추천순위 계산
            pc_scores = []
            for keyword, result in keywords_data.items():
                if result.pc_min_exposure_bid > 0:
                    # 현실성 점수 = 월평균클릭수 ÷ 최소노출가격
                    reality_score = result.pc_clicks / result.pc_min_exposure_bid
                    
                    # 잠재력 점수 = (월검색량 × 클릭률 ÷ 100) ÷ 최소노출가격
                    potential_clicks = (result.pc_search_volume * result.pc_ctr) / 100
                    potential_score = potential_clicks / result.pc_min_exposure_bid if result.pc_min_exposure_bid > 0 else 0
                    
                    # 최종 점수 = 현실성 70% + 잠재력 30%
                    final_score = (reality_score * 0.7) + (potential_score * 0.3)
                    
                    pc_scores.append((keyword, final_score, result.pc_search_volume, result.pc_min_exposure_bid))
            
            # PC 순위 정렬 (점수 내림차순, 동점시 월검색량 내림차순, 최소노출가격 오름차순, 키워드명 오름차순)
            pc_scores.sort(key=lambda x: (-x[1], -x[2], x[3], x[0]))
            
            # PC 순위 적용
            for rank, (keyword, _, _, _) in enumerate(pc_scores, 1):
                keywords_data[keyword].pc_recommendation_rank = rank
            
            # 모바일 추천순위 계산
            mobile_scores = []
            for keyword, result in keywords_data.items():
                if result.mobile_min_exposure_bid > 0:
                    # 현실성 점수 = 월평균클릭수 ÷ 최소노출가격
                    reality_score = result.mobile_clicks / result.mobile_min_exposure_bid
                    
                    # 잠재력 점수 = (월검색량 × 클릭률 ÷ 100) ÷ 최소노출가격
                    potential_clicks = (result.mobile_search_volume * result.mobile_ctr) / 100
                    potential_score = potential_clicks / result.mobile_min_exposure_bid if result.mobile_min_exposure_bid > 0 else 0
                    
                    # 최종 점수 = 현실성 70% + 잠재력 30%
                    final_score = (reality_score * 0.7) + (potential_score * 0.3)
                    
                    mobile_scores.append((keyword, final_score, result.mobile_search_volume, result.mobile_min_exposure_bid))
            
            # 모바일 순위 정렬
            mobile_scores.sort(key=lambda x: (-x[1], -x[2], x[3], x[0]))
            
            # 모바일 순위 적용
            for rank, (keyword, _, _, _) in enumerate(mobile_scores, 1):
                keywords_data[keyword].mobile_recommendation_rank = rank
            
            log_manager.add_log("추천순위 계산 완료", "success")
            logger.info("추천순위 계산 완료")
            
            return keywords_data
            
        except Exception as e:
            error_msg = f"추천순위 계산 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return keywords_data
    
    def save_to_excel(self, keywords_data: Dict[str, KeywordAnalysisResult], file_path: str, session_name: str = "") -> bool:
        """
        분석 결과를 엑셀 파일로 저장
        
        Args:
            keywords_data: 키워드별 분석 결과
            file_path: 저장할 파일 경로
            session_name: 세션명
            
        Returns:
            저장 성공 여부
        """
        try:
            if not keywords_data:
                log_manager.add_log("저장할 분석 데이터가 없습니다.", "warning")
                return False
            
            # adapters의 엑셀 익스포터 사용
            powerlink_excel_exporter.export_to_excel(keywords_data, file_path, session_name)
            
            return True
            
        except Exception as e:
            error_msg = f"엑셀 저장 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False
    
    def save_analysis_to_database(self, keywords_data: Dict[str, KeywordAnalysisResult], session_name: str) -> bool:
        """
        분석 결과를 데이터베이스에 저장
        
        Args:
            keywords_data: 키워드별 분석 결과
            session_name: 세션명
            
        Returns:
            저장 성공 여부
        """
        try:
            if not keywords_data:
                return False
            
            # models의 keyword_database 사용
            session_id = keyword_database.save_analysis_session(session_name, keywords_data)
            
            if session_id:
                log_manager.add_log(f"분석 결과 저장 완료: {session_name}", "success")
                logger.info(f"분석 결과 DB 저장 완료: {session_name}")
                return True
            else:
                log_manager.add_log("분석 결과 저장 실패", "error")
                return False
                
        except Exception as e:
            error_msg = f"DB 저장 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False
    
    def load_analysis_from_database(self, session_id: int) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """
        데이터베이스에서 분석 결과 로드
        
        Args:
            session_id: 세션 ID
            
        Returns:
            키워드별 분석 결과 또는 None
        """
        try:
            # models의 keyword_database 사용
            keywords_data = keyword_database.load_analysis_session(session_id)
            
            if keywords_data:
                log_manager.add_log(f"분석 결과 로드 완료: {len(keywords_data)}개 키워드", "success")
                logger.info(f"분석 결과 DB 로드 완료: {session_id}")
                return keywords_data
            else:
                log_manager.add_log("분석 결과 로드 실패", "warning")
                return None
                
        except Exception as e:
            error_msg = f"DB 로드 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return None
    
    def get_analysis_history(self) -> List[Dict]:
        """
        분석 히스토리 조회
        
        Returns:
            세션 리스트
        """
        try:
            # models의 keyword_database 사용
            sessions = keyword_database.get_analysis_sessions()
            return sessions
            
        except Exception as e:
            error_msg = f"히스토리 조회 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return []
    
    def delete_analysis_sessions(self, session_ids: List[int]) -> bool:
        """
        분석 세션 삭제
        
        Args:
            session_ids: 삭제할 세션 ID 리스트
            
        Returns:
            삭제 성공 여부
        """
        try:
            # models의 keyword_database 사용
            success = keyword_database.delete_analysis_sessions(session_ids)
            
            if success:
                log_manager.add_log(f"{len(session_ids)}개 세션 삭제 완료", "success")
                logger.info(f"세션 삭제 완료: {session_ids}")
                return True
            else:
                log_manager.add_log("세션 삭제 실패", "error")
                return False
                
        except Exception as e:
            error_msg = f"세션 삭제 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False
    
    def save_current_analysis_to_db(self) -> Tuple[bool, int, str, bool]:
        """
        현재 분석 결과를 데이터베이스에 저장
        
        Returns:
            (성공 여부, 세션 ID, 세션명, 중복 여부)
        """
        try:
            # 현재 키워드 데이터 가져오기
            keywords_data = keyword_database.keywords
            
            if not keywords_data:
                log_manager.add_log("저장할 분석 결과가 없습니다.", "warning")
                return False, 0, "", False
            
            # 중복 확인
            is_duplicate = self.repository.check_duplicate_session_24h(keywords_data)
            
            session_name = f"PowerLink분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if is_duplicate:
                # 중복이면 저장하지 않고 정보만 반환
                log_manager.add_log("24시간 내 동일한 분석 결과가 존재하여 저장하지 않습니다.", "info")
                return True, 0, session_name, True
            else:
                # 중복이 아니면 DB에 저장
                session_id = self.repository.save_analysis_session(keywords_data)
                
                log_manager.add_log(f"PowerLink 분석 세션 저장 완료: {session_name} ({len(keywords_data)}개 키워드)", "success")
                logger.info(f"분석 세션 DB 저장 완료: {session_name}")
                return True, session_id, session_name, False
                
        except Exception as e:
            error_msg = f"분석 세션 저장 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False, 0, "", False
    
    def export_analysis_to_excel(self, session_ids: List[int], output_folder: str = None) -> Tuple[bool, List[str]]:
        """
        분석 세션들을 엑셀로 내보내기
        
        Args:
            session_ids: 내보낼 세션 ID 리스트
            output_folder: 출력 폴더 (None이면 파일 다이얼로그)
            
        Returns:
            (성공 여부, 저장된 파일 경로 리스트)
        """
        try:
            if not session_ids:
                return False, []
            
            import os
            
            saved_files = []
            
            for session_id in session_ids:
                try:
                    # 세션 정보 가져오기
                    session = self.repository.get_session(session_id)
                    if not session:
                        continue
                    
                    # 키워드 데이터 가져오기
                    keywords_data = self.repository.get_session_keywords(session_id)
                    if not keywords_data:
                        continue
                    
                    # 파일 경로 결정
                    if output_folder:
                        # 다중 선택: 폴더 + 자동 파일명
                        session_time = datetime.fromisoformat(session['created_at'])
                        time_str = session_time.strftime('%Y%m%d_%H%M%S')
                        filename = f"파워링크광고비분석_{time_str}.xlsx"
                        file_path = os.path.join(output_folder, filename)
                    else:
                        # 단일 선택: 사용자가 지정한 파일명 (UI에서 처리)
                        continue
                    
                    # 엑셀 내보내기
                    powerlink_excel_exporter.export_to_excel(
                        keywords_data=keywords_data,
                        file_path=file_path,
                        session_name=session['session_name']
                    )
                    
                    saved_files.append(file_path)
                    
                except Exception as e:
                    logger.error(f"세션 {session_id} 내보내기 실패: {e}")
                    continue
            
            if saved_files:
                log_manager.add_log(f"PowerLink 엑셀 내보내기 완료: {len(saved_files)}개 파일", "success")
                return True, saved_files
            else:
                log_manager.add_log("내보낼 수 있는 세션이 없습니다.", "warning")
                return False, []
                
        except Exception as e:
            error_msg = f"엑셀 내보내기 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False, []


    def load_history_session_data(self, session_id: int) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """
        히스토리에서 세션 데이터를 로드하여 KeywordAnalysisResult 객체로 변환
        
        Args:
            session_id: 로드할 세션 ID
            
        Returns:
            변환된 키워드 분석 결과 딕셔너리 또는 None
        """
        try:
            from .models import BidPosition
            
            session_keywords_data = self.repository.get_session_keywords(session_id)
            
            if not session_keywords_data:
                log_manager.add_log("키워드 데이터가 없습니다.", "warning")
                return None
            
            # 키워드 데이터를 KeywordAnalysisResult 객체로 변환
            loaded_keywords_data = {}
            
            for keyword, data in session_keywords_data.items():
                try:
                    # BidPosition 객체들 복원
                    pc_bid_positions = []
                    if data.get('pc_bid_positions'):
                        for bid_data in data['pc_bid_positions']:
                            pc_bid_positions.append(BidPosition(
                                position=bid_data['position'],
                                bid_price=bid_data['bid_price']
                            ))
                    
                    mobile_bid_positions = []
                    if data.get('mobile_bid_positions'):
                        for bid_data in data['mobile_bid_positions']:
                            mobile_bid_positions.append(BidPosition(
                                position=bid_data['position'],
                                bid_price=bid_data['bid_price']
                            ))
                    
                    # KeywordAnalysisResult 객체 복원
                    result = KeywordAnalysisResult(
                        keyword=keyword,
                        pc_search_volume=data.get('pc_search_volume', 0),
                        mobile_search_volume=data.get('mobile_search_volume', 0),
                        pc_clicks=data.get('pc_clicks', 0),
                        pc_ctr=data.get('pc_ctr', 0),
                        pc_first_page_positions=data.get('pc_first_page_positions', 0),
                        pc_first_position_bid=data.get('pc_first_position_bid', 0),
                        pc_min_exposure_bid=data.get('pc_min_exposure_bid', 0),
                        pc_bid_positions=pc_bid_positions,
                        mobile_clicks=data.get('mobile_clicks', 0),
                        mobile_ctr=data.get('mobile_ctr', 0),
                        mobile_first_page_positions=data.get('mobile_first_page_positions', 0),
                        mobile_first_position_bid=data.get('mobile_first_position_bid', 0),
                        mobile_min_exposure_bid=data.get('mobile_min_exposure_bid', 0),
                        mobile_bid_positions=mobile_bid_positions,
                        analyzed_at=datetime.fromisoformat(data.get('analyzed_at', datetime.now().isoformat()))
                    )
                    
                    loaded_keywords_data[keyword] = result
                    
                except Exception as e:
                    logger.error(f"키워드 {keyword} 복원 실패: {e}")
                    continue
            
            if loaded_keywords_data:
                log_manager.add_log(f"히스토리 세션 로드 완료: {len(loaded_keywords_data)}개 키워드", "success")
                return loaded_keywords_data
            else:
                log_manager.add_log("유효한 키워드가 없습니다.", "warning")
                return None
                
        except Exception as e:
            error_msg = f"히스토리 세션 로드 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return None
    
    def export_history_sessions(self, session_ids: List[int], single_file_path: str = None, output_folder: str = None) -> Tuple[bool, List[str]]:
        """
        히스토리 세션들을 엑셀로 내보내기
        
        Args:
            session_ids: 내보낼 세션 ID 리스트
            single_file_path: 단일 세션용 파일 경로 (None이면 다중 세션 모드)
            output_folder: 다중 세션용 출력 폴더
            
        Returns:
            (성공 여부, 저장된 파일 경로 리스트)
        """
        try:
            if not session_ids:
                return False, []
                
            import os
            
            saved_files = []
            
            # 단일 세션 처리
            if len(session_ids) == 1 and single_file_path:
                session_id = session_ids[0]
                
                # 세션 정보 가져오기
                session = self.repository.get_session(session_id)
                if not session:
                    log_manager.add_log("세션 정보를 찾을 수 없습니다.", "warning")
                    return False, []
                
                # 키워드 데이터 가져오기
                keywords_data = self.repository.get_session_keywords(session_id)
                if not keywords_data:
                    log_manager.add_log("키워드 데이터가 없습니다.", "warning")
                    return False, []
                
                # 엑셀 내보내기
                success = self.save_to_excel(keywords_data, single_file_path, session['session_name'])
                if success:
                    saved_files.append(single_file_path)
                    log_manager.add_log(f"히스토리 단일 파일 저장 완료: {session['session_name']}", "success")
                    return True, saved_files
                else:
                    return False, []
            
            # 다중 세션 처리
            elif output_folder:
                for session_id in session_ids:
                    try:
                        # 세션 정보 가져오기
                        session = self.repository.get_session(session_id)
                        if not session:
                            continue
                        
                        # 키워드 데이터 가져오기
                        keywords_data = self.repository.get_session_keywords(session_id)
                        if not keywords_data:
                            continue
                        
                        # 파일명 생성 (세션 생성 시간 사용)
                        session_time = datetime.fromisoformat(session['created_at'])
                        time_str = session_time.strftime('%Y%m%d_%H%M%S')
                        filename = f"파워링크광고비분석_{time_str}.xlsx"
                        file_path = os.path.join(output_folder, filename)
                        
                        # 엑셀 내보내기
                        success = self.save_to_excel(keywords_data, file_path, session['session_name'])
                        if success:
                            saved_files.append(file_path)
                        
                    except Exception as e:
                        logger.error(f"세션 {session_id} 내보내기 실패: {e}")
                        continue
                
                if saved_files:
                    log_manager.add_log(f"히스토리 다중 파일 저장 완료: {len(saved_files)}개 파일", "success")
                    return True, saved_files
                else:
                    log_manager.add_log("저장할 수 있는 세션이 없습니다.", "warning")
                    return False, []
            
            return False, []
            
        except Exception as e:
            error_msg = f"히스토리 엑셀 내보내기 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False, []
    
    def export_selected_history_with_dialog(self, sessions_data: list, parent_widget=None, reference_widget=None) -> bool:
        """
        선택된 히스토리 세션들을 엑셀로 내보내기 (오케스트레이션)
        
        Args:
            sessions_data: [{'id': int, 'name': str, 'created_at': str}, ...]
            parent_widget: 부모 위젯 (다이얼로그용)
            reference_widget: 참조 위젯 (성공 다이얼로그 위치용)
            
        Returns:
            성공 여부
        """
        try:
            if not sessions_data:
                log_manager.add_log("선택된 히스토리가 없습니다.", "warning")
                return False
            
            # adapters를 통한 파일 I/O 처리
            from .adapters import history_export_adapter
            
            # 단일 세션 vs 다중 세션 처리
            if len(sessions_data) == 1:
                # 단일 세션: 파일 다이얼로그
                session = sessions_data[0]
                success, result = history_export_adapter.export_single_session_with_dialog(session, parent_widget)
                
                if success:
                    # 성공 다이얼로그 표시
                    history_export_adapter.show_export_success_dialog(
                        file_path=result,
                        file_count=1,
                        parent_widget=parent_widget,
                        reference_widget=reference_widget
                    )
                    log_manager.add_log(f"PowerLink 히스토리 단일 파일 저장 완료: {session['name']}", "success")
                    return True
                else:
                    # 실패 다이얼로그 표시 (사용자 취소 제외)
                    if result != "사용자가 취소했습니다.":
                        history_export_adapter.show_export_error_dialog(result, parent_widget)
                        log_manager.add_log(f"엑셀 파일 저장 실패: {result}", "error")
                    return False
            
            else:
                # 다중 세션: 폴더 선택
                success, saved_files = history_export_adapter.export_multiple_sessions_with_dialog(sessions_data, parent_widget)
                
                if success and saved_files:
                    # 성공 다이얼로그 표시
                    history_export_adapter.show_export_success_dialog(
                        file_path=saved_files[0],  # 첫 번째 파일 경로로 폴더 열기
                        file_count=len(saved_files),
                        parent_widget=parent_widget,
                        reference_widget=reference_widget
                    )
                    log_manager.add_log(f"PowerLink 히스토리 {len(saved_files)}개 파일 저장 완료", "success")
                    return True
                else:
                    # 실패 다이얼로그 표시
                    if success:  # 폴더는 선택했지만 저장 실패
                        history_export_adapter.show_export_error_dialog("선택된 기록을 저장하는 중 오류가 발생했습니다.", parent_widget)
                    # 폴더 선택 취소는 별도 메시지 없음
                    return False
                    
        except Exception as e:
            error_msg = f"PowerLink 히스토리 내보내기 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            
            # 예외 발생 시 에러 다이얼로그 표시
            from .adapters import history_export_adapter
            history_export_adapter.show_export_error_dialog(str(e), parent_widget)
            
            return False
    
    def get_analysis_history_sessions(self) -> list:
        """분석 히스토리 세션 목록 조회 (UI 위임용)"""
        try:
            sessions = self.repository.list_sessions()
            return sessions
        except Exception as e:
            logger.error(f"히스토리 세션 목록 조회 실패: {e}")
            return []
    
    def delete_analysis_history_sessions(self, session_ids: list) -> bool:
        """분석 히스토리 세션 삭제 (UI 위임용)"""
        try:
            success = self.repository.delete_sessions(session_ids)
            
            if success:
                log_manager.add_log(f"PowerLink 히스토리 {len(session_ids)}개 세션 삭제 완료", "success")
                logger.info(f"히스토리 세션 삭제 완료: {session_ids}")
            else:
                log_manager.add_log("히스토리 세션 삭제 실패", "error")
                
            return success
        except Exception as e:
            logger.error(f"히스토리 세션 삭제 실패: {e}")
            log_manager.add_log(f"히스토리 세션 삭제 실패: {e}", "error")
            return False
    
    def export_current_analysis_with_dialog(self, keywords_data: dict, session_name: str = "", parent_widget=None) -> bool:
        """
        현재 분석 결과를 엑셀로 내보내기 (오케스트레이션)
        
        Args:
            keywords_data: 키워드 분석 결과 딕셔너리
            session_name: 세션명
            parent_widget: 부모 위젯 (다이얼로그용)
            
        Returns:
            성공 여부
        """
        try:
            if not keywords_data:
                log_manager.add_log("내보낼 분석 결과가 없습니다.", "warning")
                return False
            
            # adapters를 통한 파일 I/O 처리
            from .adapters import current_analysis_export_adapter
            
            success = current_analysis_export_adapter.export_current_analysis_with_dialog(
                keywords_data=keywords_data,
                session_name=session_name,
                parent_widget=parent_widget
            )
            
            if success:
                log_manager.add_log("PowerLink 분석 결과 엑셀 저장 완료", "success")
            
            return success
            
        except Exception as e:
            error_msg = f"PowerLink 분석 결과 내보내기 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            
            # 예외 발생 시 에러 다이얼로그 표시
            from .adapters import current_analysis_export_adapter
            current_analysis_export_adapter.show_current_export_error_dialog(str(e), parent_widget)
            
            return False


# 전역 서비스 인스턴스
powerlink_service = PowerLinkAnalysisService()