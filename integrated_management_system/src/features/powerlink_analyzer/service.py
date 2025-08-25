"""
파워링크 광고비 분석기 서비스 레이어
오케스트레이션(검증→벤더→가공→저장/엑셀) 담당
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from src.foundation.logging import get_logger
from src.desktop.common_log import log_manager
from src.toolbox.text_utils import parse_keywords_from_text, process_keywords

from .adapters import PowerLinkDataAdapter, powerlink_excel_exporter
from .models import KeywordAnalysisResult, AnalysisProgress, PowerLinkRepository, is_completed
from .engine_local import calculate_all_rankings, rank_pc_keywords, rank_mobile_keywords

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

    def remove_keywords(self, keywords_to_remove: List[str]):
        """여러 키워드 제거"""
        for keyword in keywords_to_remove:
            if keyword in self.keywords:
                del self.keywords[keyword]

    def get_keyword_count(self) -> int:
        """현재 저장된 키워드 개수"""
        return len(self.keywords)

    def _calculate_hybrid_rankings(self, device_type: str, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """하이브리드 방식 추천순위 계산 (engine_local 위임)"""
        all_keywords = self.get_all_keywords()
        if device_type == 'pc':
            rank_pc_keywords(all_keywords, alpha)
        else:  # mobile
            rank_mobile_keywords(all_keywords, alpha)
        return all_keywords

    def calculate_pc_rankings(self, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """PC 추천순위 계산 및 반환 (하이브리드 방식)"""
        return self._calculate_hybrid_rankings('pc', alpha)

    def calculate_mobile_rankings(self, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """모바일 추천순위 계산 및 반환 (하이브리드 방식)"""
        return self._calculate_hybrid_rankings('mobile', alpha)

    def recalculate_all_rankings(self):
        """모든 순위 재계산 (engine_local 위임)"""
        all_keywords = self.get_all_keywords()
        calculate_all_rankings(all_keywords, alpha=0.7)

    def get_saved_sessions(self) -> List[Dict]:
        """저장된 세션 목록 조회 (UI 호환성)"""
        try:
            repository = PowerLinkRepository()
            # get_analysis_sessions()를 사용하여 'id' 키가 포함된 데이터 반환
            return repository.get_analysis_sessions()
        except Exception as e:
            logger.error(f"세션 목록 조회 실패: {e}")
            return []

    def load_session(self, session_name: str) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """세션명으로 세션 데이터 로드 (UI 호환성)"""
        try:
            repository = PowerLinkRepository()
            # get_analysis_sessions()를 사용하여 'id' 키가 포함된 데이터 사용
            sessions = repository.get_analysis_sessions()
            target_session = None
            for session in sessions:
                if session.get('name') == session_name or session.get('session_name') == session_name:
                    target_session = session
                    break

            if not target_session:
                logger.warning(f"세션을 찾을 수 없음: {session_name}")
                return None

            session_id = target_session.get('id')
            if session_id:
                return repository.get_session_keywords(session_id)
            return None
        except Exception as e:
            logger.error(f"세션 로드 실패: {e}")
            return None


class PowerLinkAnalysisService:
    """파워링크 광고비 분석 서비스"""

    def __init__(self):
        self.adapter = PowerLinkDataAdapter()
        self.repository = PowerLinkRepository()

    # ---------------- 입력 검증/상태 ----------------

    def validate_keywords(self, keywords_text: str) -> Tuple[bool, List[str], str]:
        """키워드 입력 검증"""
        try:
            if not keywords_text or not keywords_text.strip():
                return False, [], "키워드를 입력해주세요."
            keywords = parse_keywords_from_text(keywords_text)
            if not keywords:
                return False, [], "유효한 키워드가 없습니다."
            if len(keywords) > 50:
                return False, [], "키워드는 최대 50개까지 입력 가능합니다."
            processed_keywords = process_keywords(keywords)
            return True, processed_keywords, ""
        except Exception as e:
            error_msg = f"키워드 검증 실패: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg

    def check_api_availability(self) -> Tuple[bool, str]:
        """API 가용성 확인"""
        try:
            if not self.adapter.is_api_configured():
                return False, "네이버 검색광고 API가 설정되지 않았습니다."
            return True, "API 사용 가능"
        except Exception as e:
            error_msg = f"API 상태 확인 실패: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    # ---------------- 분석/계산 ----------------

    def analyze_keywords(self, keywords: List[str], progress_callback=None) -> Dict[str, KeywordAnalysisResult]:
        """
        키워드 분석 실행 (service에서 오케스트레이션만, 실제 분석은 worker에서)
        """
        try:
            if progress_callback:
                progress_callback(AnalysisProgress(
                    current=0, total=len(keywords), current_keyword="",
                    status="분석 시작", current_step="준비", step_detail=f"{len(keywords)}개 키워드"
                ))
            results: Dict[str, KeywordAnalysisResult] = {}
            log_manager.add_log(f"파워링크 분석 시작: {len(keywords)}개 키워드", "info")
            logger.info(f"파워링크 분석 시작: {keywords}")
            return results
        except Exception as e:
            error_msg = f"키워드 분석 실행 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            raise

    def calculate_recommendation_ranks(self, keywords_data: Dict[str, KeywordAnalysisResult]) -> Dict[str, KeywordAnalysisResult]:
        """추천순위 계산 (engine_local 위임)"""
        try:
            if not keywords_data:
                return keywords_data
            keywords_list = list(keywords_data.values())
            calculate_all_rankings(keywords_list, alpha=0.7)
            log_manager.add_log("추천순위 계산 완료", "success")
            logger.info("추천순위 계산 완료")
            return keywords_data
        except Exception as e:
            error_msg = f"추천순위 계산 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return keywords_data

    # ---------------- 저장/불러오기 (엑셀·DB) ----------------

    def save_to_excel(self, keywords_data: Dict[str, KeywordAnalysisResult], file_path: str, session_name: str = "") -> bool:
        """분석 결과를 엑셀 파일로 저장"""
        try:
            if not keywords_data:
                log_manager.add_log("저장할 분석 데이터가 없습니다.", "warning")
                return False
            powerlink_excel_exporter.export_to_excel(keywords_data, file_path, session_name)
            return True
        except Exception as e:
            error_msg = f"엑셀 저장 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False

    def save_analysis_to_database(self, keywords_data: Dict[str, KeywordAnalysisResult], session_name: str) -> bool:
        """분석 결과를 데이터베이스에 저장"""
        try:
            if not keywords_data:
                return False
            session_id = self.repository.save_analysis_session(keywords_data)
            if session_id:
                log_manager.add_log(f"분석 결과 저장 완료: {session_name}", "success")
                logger.info(f"분석 결과 DB 저장 완료: {session_name}")
                return True
            log_manager.add_log("분석 결과 저장 실패", "error")
            return False
        except Exception as e:
            error_msg = f"DB 저장 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False

    def load_analysis_from_database(self, session_id: int) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """데이터베이스에서 분석 결과 로드 (dict 그대로 반환)"""
        try:
            keywords_data = self.repository.get_session_keywords(session_id)
            if keywords_data:
                log_manager.add_log(f"분석 결과 로드 완료: {len(keywords_data)}개 키워드", "success")
                logger.info(f"분석 결과 DB 로드 완료: {session_id}")
                return keywords_data
            log_manager.add_log("분석 결과 로드 실패", "warning")
            return None
        except Exception as e:
            error_msg = f"DB 로드 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return None

    def get_analysis_history(self) -> List[Dict]:
        """분석 히스토리 조회"""
        try:
            return self.repository.list_sessions()
        except Exception as e:
            error_msg = f"히스토리 조회 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return []

    def delete_analysis_sessions(self, session_ids: List[int]) -> bool:
        """분석 세션 삭제"""
        try:
            success = self.repository.delete_sessions(session_ids)
            if success:
                log_manager.add_log(f"{len(session_ids)}개 세션 삭제 완료", "success")
                logger.info(f"세션 삭제 완료: {session_ids}")
                return True
            log_manager.add_log("세션 삭제 실패", "error")
            return False
        except Exception as e:
            error_msg = f"세션 삭제 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False

    # ---------------- 현재 분석 키워드 관리 ----------------

    def clear_current_analysis(self) -> bool:
        """현재 분석 결과 전체 삭제"""
        try:
            keyword_database.clear()
            log_manager.add_log("현재 분석 결과 전체 삭제 완료", "success")
            logger.info("현재 분석 결과 전체 삭제 완료")
            return True
        except Exception as e:
            error_msg = f"분석 결과 삭제 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False

    # ---------------- 현재 분석 저장/내보내기 ----------------

    def save_current_analysis_to_db(self) -> Tuple[bool, int, str, bool]:
        """
        현재 분석 결과를 DB에 저장.
        Returns: (성공 여부, 세션 ID, 세션명, 중복 여부)
        """
        try:
            if not keyword_database.keywords:
                log_manager.add_log("저장할 분석 결과가 없습니다.", "warning")
                return False, 0, "", False

            is_duplicate = self.repository.check_duplicate_session_24h(keyword_database.keywords)
            
            # 추천순위 1위 키워드 기반으로 세션명 생성
            keywords_list = list(keyword_database.keywords.values())
            
            if keywords_list:
                try:
                    # 모바일 기준으로 가장 높은 순위를 가진 키워드를 찾기
                    def get_best_rank(result):
                        """모바일 순위 반환 (작을수록 좋음, -1은 순위 없음으로 최악)"""
                        return result.mobile_recommendation_rank if result.mobile_recommendation_rank > 0 else 999
                    
                    # 모바일 추천순위가 가장 좋은 키워드를 대표로 선택
                    best_keyword_result = min(keywords_list, key=get_best_rank)
                    representative_keyword = best_keyword_result.keyword
                    
                    if len(keywords_list) == 1:
                        session_name = representative_keyword
                    else:
                        remaining_count = len(keywords_list) - 1
                        session_name = f"{representative_keyword} 외 {remaining_count}개"
                    
                except Exception as e:
                    # 오류 시 첫 번째 키워드로 폴백
                    first_keyword = keywords_list[0].keyword if keywords_list else "알수없음"
                    session_name = f"{first_keyword} 외 {len(keywords_list)-1}개" if len(keywords_list) > 1 else first_keyword
            else:
                session_name = f"PowerLink분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if is_duplicate:
                log_manager.add_log("24시간 내 동일한 분석 결과가 존재하여 저장하지 않습니다.", "info")
                return True, 0, session_name, True

            session_id = self.repository.save_analysis_session(keyword_database.keywords, session_name)
            log_manager.add_log(f"PowerLink 분석 세션 저장 완료: {session_name} ({len(keyword_database.keywords)}개 키워드)", "success")
            logger.info(f"분석 세션 DB 저장 완료: {session_name}")
            return True, session_id, session_name, False
        except Exception as e:
            error_msg = f"분석 세션 저장 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False, 0, "", False

    def export_results_to_excel(self, results: List[KeywordAnalysisResult], device_type: str) -> bool:
        """UI에서 호출하는 엑셀 내보내기(현재 결과)"""
        try:
            if not results:
                return False
            keywords_data = {result.keyword: result for result in results}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"파워링크분석_{device_type}_{timestamp}.xlsx"
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(None, f"{device_type.upper()} 분석 결과 저장", default_name, "Excel Files (*.xlsx)")
            if not file_path:
                return False
            success = self.save_to_excel(keywords_data, file_path, f"{device_type.upper()} 분석")
            if success:
                log_manager.add_log(f"{device_type.upper()} 분석 결과를 엑셀로 저장했습니다: {file_path}", "success")
            return success
        except Exception as e:
            logger.error(f"엑셀 내보내기 실패: {e}")
            log_manager.add_log(f"엑셀 내보내기 실패: {str(e)}", "error")
            return False

    # ---------------- 히스토리: 내보내기/보기 ----------------

    def export_history_sessions(self, session_ids: List[int], single_file_path: str = None, output_folder: str = None) -> Tuple[bool, List[str]]:
        """
        히스토리 세션들을 엑셀로 내보내기
        - 단일: single_file_path 지정
        - 다중: output_folder 지정
        """
        try:
            if not session_ids:
                return False, []

            import os
            saved_files: List[str] = []

            # 단일 저장
            if len(session_ids) == 1 and single_file_path:
                session_id = session_ids[0]
                session = self.repository.get_session(session_id)
                if not session:
                    log_manager.add_log("세션 정보를 찾을 수 없습니다.", "warning")
                    return False, []
                keywords_data = self.repository.get_session_keywords(session_id)
                if not keywords_data:
                    log_manager.add_log("키워드 데이터가 없습니다.", "warning")
                    return False, []
                success = self.save_to_excel(keywords_data, single_file_path, session['session_name'])
                if success:
                    saved_files.append(single_file_path)
                    log_manager.add_log(f"히스토리 단일 파일 저장 완료: {session['session_name']}", "success")
                    return True, saved_files
                return False, []

            # 다중 저장
            if output_folder:
                for session_id in session_ids:
                    try:
                        session = self.repository.get_session(session_id)
                        if not session:
                            continue
                        keywords_data = self.repository.get_session_keywords(session_id)
                        if not keywords_data:
                            continue
                        session_time = datetime.fromisoformat(session['created_at'])
                        time_str = session_time.strftime('%Y%m%d_%H%M%S')
                        filename = f"파워링크광고비분석_{time_str}.xlsx"
                        file_path = os.path.join(output_folder, filename)
                        if self.save_to_excel(keywords_data, file_path, session['session_name']):
                            saved_files.append(file_path)
                    except Exception as e:
                        logger.error(f"세션 {session_id} 내보내기 실패: {e}")
                        continue

                if saved_files:
                    log_manager.add_log(f"히스토리 다중 파일 저장 완료: {len(saved_files)}개 파일", "success")
                    return True, saved_files
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
        선택된 히스토리를 엑셀로 내보내기 (오케스트레이션)
        - 1개: 파일 경로 선택 → export_history_sessions(single_file_path=..)
        - N개: 폴더 선택 → export_history_sessions(output_folder=..)
        """
        try:
            if not sessions_data:
                log_manager.add_log("선택된 히스토리가 없습니다.", "warning")
                return False

            from .adapters import history_export_adapter

            # 단일 세션
            if len(sessions_data) == 1:
                session = sessions_data[0]
                ok, file_path = history_export_adapter.choose_single_file_path(session, parent_widget)
                if not ok:
                    return False
                ok, saved = self.export_history_sessions([session['id']], single_file_path=file_path)
                if ok and saved:
                    history_export_adapter.show_export_success_dialog(saved[0], 1, parent_widget, reference_widget)
                elif ok:
                    history_export_adapter.show_export_error_dialog("저장할 데이터가 없습니다.", parent_widget)
                return ok

            # 다중 세션
            ok, folder = history_export_adapter.choose_output_folder(parent_widget)
            if not ok:
                return False
            session_ids = [s['id'] for s in sessions_data]
            ok, saved_files = self.export_history_sessions(session_ids, output_folder=folder)
            if ok and saved_files:
                history_export_adapter.show_export_success_dialog(saved_files[0], len(saved_files), parent_widget, reference_widget)
            elif ok:
                history_export_adapter.show_export_error_dialog("선택된 기록을 저장하는 중 오류가 발생했습니다.", parent_widget)
            return ok

        except Exception as e:
            error_msg = f"PowerLink 히스토리 내보내기 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            from .adapters import history_export_adapter
            history_export_adapter.show_export_error_dialog(str(e), parent_widget)
            return False

    def load_history_session_data(self, session_id: int) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """
        히스토리에서 세션 데이터를 로드하여 KeywordAnalysisResult 객체로 변환
        (UI '보기'에서 바로 테이블에 넣을 수 있도록 객체로 복원)
        """
        try:
            from .models import BidPosition  # 지연 임포트(순환 방지)

            session_keywords_data = self.repository.get_session_keywords(session_id)
            if not session_keywords_data:
                log_manager.add_log("키워드 데이터가 없습니다.", "warning")
                return None

            loaded_keywords_data: Dict[str, KeywordAnalysisResult] = {}

            for keyword, data in session_keywords_data.items():
                try:
                    pc_bid_positions = []
                    if data.get('pc_bid_positions'):
                        for bid_data in data['pc_bid_positions']:
                            pc_bid_positions.append(BidPosition(position=bid_data['position'], bid_price=bid_data['bid_price']))

                    mobile_bid_positions = []
                    if data.get('mobile_bid_positions'):
                        for bid_data in data['mobile_bid_positions']:
                            mobile_bid_positions.append(BidPosition(position=bid_data['position'], bid_price=bid_data['bid_price']))

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

            log_manager.add_log("유효한 키워드가 없습니다.", "warning")
            return None

        except Exception as e:
            error_msg = f"히스토리 세션 로드 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return None

    # ---------------- UI 호환(래핑) ----------------

    def get_analysis_history_sessions(self) -> list:
        """분석 히스토리 세션 목록 조회 (UI 위임용)"""
        try:
            return self.repository.list_sessions()
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
        """현재 분석 결과를 엑셀로 내보내기 (adapters 위임)"""
        try:
            if not keywords_data:
                log_manager.add_log("내보낼 분석 결과가 없습니다.", "warning")
                return False
            from .adapters import current_analysis_export_adapter
            success = current_analysis_export_adapter.export_current_analysis_with_dialog(
                keywords_data=keywords_data, session_name=session_name, parent_widget=parent_widget
            )
            if success:
                log_manager.add_log("PowerLink 분석 결과 엑셀 저장 완료", "success")
            return success
        except Exception as e:
            error_msg = f"PowerLink 분석 결과 내보내기 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            from .adapters import current_analysis_export_adapter
            current_analysis_export_adapter.show_current_export_error_dialog(str(e), parent_widget)
            return False


    def get_analysis_sessions(self) -> List[Dict]:
        """저장된 분석 세션 목록 조회 (UI에서 사용)"""
        try:
            repo = PowerLinkRepository()
            return repo.get_analysis_sessions()
        except Exception as e:
            logger.error(f"분석 세션 목록 조회 실패: {e}")
            return []

    def load_analysis_session(self, session_id: int) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """저장된 분석 세션 로드"""
        try:
            return self.load_analysis_from_database(session_id)
        except Exception as e:
            logger.error(f"분석 세션 로드 실패: {e}")
            return None

    def export_analysis_session_with_dialog(self, session_id: int, session_name: str, parent_widget=None) -> bool:
        """저장된 분석 세션을 엑셀로 내보내기 (다이얼로그 포함)"""
        try:
            keywords_data = self.load_analysis_session(session_id)
            if not keywords_data:
                from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
                ModernInfoDialog.warning(parent_widget, "오류", "분석 기록을 불러올 수 없습니다.")
                return False
            return self.export_current_analysis_with_dialog(
                keywords_data=keywords_data, session_name=session_name, parent_widget=parent_widget
            )
        except Exception as e:
            logger.error(f"분석 세션 내보내기 실패: {e}")
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.error(parent_widget, "오류", f"내보내기 실패: {str(e)}")
            return False

    def load_session_by_name(self, session_name: str) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """세션명으로 세션 데이터 로드"""
        return keyword_database.load_session(session_name)
    
    def load_and_set_session_data(self, session_id: int) -> bool:
        """세션 데이터를 로드하고 전역 keyword_database에 설정 (CLAUDE.md 준수)"""
        try:
            # 히스토리 세션 데이터 로드
            loaded_keywords_data = self.load_history_session_data(session_id)
            if not loaded_keywords_data:
                log_manager.add_log("히스토리 세션 데이터 로드 실패", "error")
                return False
            
            # 기존 데이터 초기화 및 새 데이터 설정
            keyword_database.clear()
            for keyword, result in loaded_keywords_data.items():
                keyword_database.add_keyword(result)
            
            # 순위 재계산
            keyword_database.recalculate_all_rankings()
            
            log_manager.add_log(f"히스토리 세션 데이터 설정 완료: {len(loaded_keywords_data)}개 키워드", "success")
            return True
            
        except Exception as e:
            error_msg = f"히스토리 세션 데이터 설정 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False
    
    
    def set_keywords_data(self, keywords_data: Dict[str, KeywordAnalysisResult]) -> bool:
        """키워드 데이터를 전역 keyword_database에 설정 (CLAUDE.md 준수) - 덮어쓰기 방식"""
        try:
            # 기존 데이터 클리어 후 새 데이터 설정 (히스토리 로드용)
            keyword_database.clear()
            for keyword, result in keywords_data.items():
                keyword_database.add_keyword(result)
            
            # 순위 재계산
            keyword_database.recalculate_all_rankings()
            
            log_manager.add_log(f"키워드 데이터 설정 완료: {len(keywords_data)}개", "success")
            return True
            
        except Exception as e:
            error_msg = f"키워드 데이터 설정 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False
    
    def add_keywords_data(self, keywords_data: Dict[str, KeywordAnalysisResult]) -> bool:
        """키워드 데이터를 전역 keyword_database에 추가 (CLAUDE.md 준수) - 누적 방식"""
        try:
            # 기존 데이터에 새 데이터 추가 (누적)
            for keyword, result in keywords_data.items():
                keyword_database.add_keyword(result)  # add_keyword는 덮어쓰기 동작
            
            # 순위 재계산
            keyword_database.recalculate_all_rankings()
            
            log_manager.add_log(f"키워드 데이터 추가 완료: {len(keywords_data)}개 (전체: {len(keyword_database.keywords)}개)", "success")
            return True
            
        except Exception as e:
            error_msg = f"키워드 데이터 추가 실패: {str(e)}"
            logger.error(error_msg)
            log_manager.add_log(error_msg, "error")
            return False

    # ---------------- UI 지원 메서드들 (Repository 패턴) ----------------
    
    def get_all_keywords(self) -> Dict[str, KeywordAnalysisResult]:
        """모든 키워드 데이터 반환"""
        return keyword_database.keywords.copy()
    
    def get_keyword_count(self) -> int:
        """키워드 개수 반환"""
        return len(keyword_database.keywords)
    
    def has_keywords(self) -> bool:
        """키워드 데이터 존재 여부"""
        return len(keyword_database.keywords) > 0
    
    def clear_all_keywords(self) -> bool:
        """모든 키워드 데이터 삭제"""
        try:
            keyword_database.clear()
            log_manager.add_log("모든 키워드 데이터 삭제 완료", "info")
            return True
        except Exception as e:
            logger.error(f"키워드 데이터 삭제 실패: {e}")
            return False
    
    def remove_keywords(self, keywords: List[str]) -> bool:
        """여러 키워드 삭제"""
        try:
            removed_count = 0
            for keyword in keywords:
                if keyword in keyword_database.keywords:
                    keyword_database.remove_keyword(keyword)
                    removed_count += 1
            keyword_database.recalculate_all_rankings()
            log_manager.add_log(f"{removed_count}개 키워드 삭제 완료", "info")
            return True
        except Exception as e:
            logger.error(f"키워드 삭제 실패: {e}")
            return False
    
    def add_keyword_result(self, result: KeywordAnalysisResult) -> bool:
        """키워드 결과 추가"""
        try:
            keyword_database.add_keyword(result)
            keyword_database.recalculate_all_rankings()
            return True
        except Exception as e:
            logger.error(f"키워드 추가 실패: {e}")
            return False
    
    def get_keyword_result(self, keyword: str) -> Optional[KeywordAnalysisResult]:
        """특정 키워드 결과 반환"""
        return keyword_database.get_keyword(keyword)
    
    def get_mobile_rankings(self) -> List[KeywordAnalysisResult]:
        """모바일 순위 계산 결과 반환"""
        return keyword_database.calculate_mobile_rankings()
    
    def get_pc_rankings(self) -> List[KeywordAnalysisResult]:
        """PC 순위 계산 결과 반환"""
        return keyword_database.calculate_pc_rankings()
    
    def load_and_set_session_data(self, session_id: int) -> Optional[Dict[str, KeywordAnalysisResult]]:
        """세션 데이터를 로드하여 keyword_database에 설정"""
        try:
            # 세션 데이터 로드
            loaded_data = self.load_history_session_data(session_id)
            if not loaded_data:
                return None
            
            # keyword_database에 설정
            if self.set_keywords_data(loaded_data):
                return loaded_data
            return None
            
        except Exception as e:
            logger.error(f"세션 로드 및 설정 실패: {e}")
            return None
    
    def recalculate_rankings(self) -> bool:
        """순위 재계산 (UI → Service → Engine 위임)"""
        try:
            keyword_database.recalculate_all_rankings()
            log_manager.add_log("순위 재계산 완료", "info")
            return True
        except Exception as e:
            logger.error(f"순위 재계산 실패: {e}")
            return False
    
    def remove_incomplete_keywords(self) -> Dict[str, int]:
        """불완전한 키워드 제거 (분석 중단 시 사용) - 공통 헬퍼 사용"""
        try:
            completed, removed = [], []
            all_keywords = keyword_database.get_all_keywords()  # List[KeywordAnalysisResult]
            
            for result in all_keywords:
                if is_completed(result):
                    completed.append(result.keyword)
                else:
                    keyword_database.remove_keyword(result.keyword)
                    removed.append(result.keyword)
            
            # 순위 재계산
            keyword_database.recalculate_all_rankings()
            
            if removed:
                log_manager.add_log(f"불완전한 키워드 {len(removed)}개 제거 완료", "info")
            
            result_stats = {
                'completed': len(completed),
                'removed': len(removed)
            }
            
            return result_stats
            
        except Exception as e:
            logger.error(f"불완전한 키워드 제거 실패: {e}")
            return {'completed': 0, 'removed': 0}
    
    def get_keyword_count_info(self) -> Dict[str, any]:
        """키워드 개수 및 목록 정보 반환 (디버그용)"""
        try:
            keywords = keyword_database.keywords
            return {
                'count': len(keywords),
                'keywords': list(keywords.keys())
            }
        except Exception as e:
            logger.error(f"키워드 정보 조회 실패: {e}")
            return {'count': 0, 'keywords': []}


# 전역 인스턴스 (UI에서 import)
keyword_database = KeywordDatabase()
powerlink_service = PowerLinkAnalysisService()
