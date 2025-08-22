"""
순위 추적 비즈니스 서비스 (단순화됨)
SQLite3 직접 사용으로 단순화된 깔끔한 코드
"""
from typing import List, Optional, Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal

from src.features.rank_tracking.models import TrackingProject, TrackingKeyword, RankingResult, rank_tracking_repository
from src.features.rank_tracking.adapters import RankTrackingAdapter, smart_product_search, rank_tracking_adapter
from src.features.rank_tracking.engine_local import rank_tracking_engine
from src.foundation.exceptions import RankTrackingError
from src.foundation.logging import get_logger

logger = get_logger("features.rank_tracking.service")


def _dict_to_tracking_project(p_dict: Dict[str, Any]) -> TrackingProject:
    """Dict을 TrackingProject 객체로 변환하는 유틸리티"""
    return TrackingProject(
        id=p_dict['id'],
        product_id=p_dict['product_id'],
        current_name=p_dict['current_name'],
        product_url=p_dict['product_url'],
        is_active=bool(p_dict['is_active']),
        category=p_dict.get('category', ''),
        price=p_dict.get('price', 0),
        store_name=p_dict.get('store_name', ''),
        description=p_dict.get('description', ''),
        image_url=p_dict.get('image_url', ''),
        created_at=p_dict.get('created_at')
    )


def _dict_to_tracking_keyword(k_dict: Dict[str, Any]) -> TrackingKeyword:
    """Dict을 TrackingKeyword 객체로 변환하는 유틸리티"""
    return TrackingKeyword(
        id=k_dict['id'],
        project_id=k_dict['project_id'],
        keyword=k_dict['keyword'],
        is_active=bool(k_dict['is_active']),
        monthly_volume=k_dict.get('monthly_volume', -1),
        category=k_dict.get('category', ''),
        created_at=k_dict.get('created_at')
    )



def _dto_to_ranking_result(dto: Dict[str, Any]) -> RankingResult:
    """DTO를 RankingResult 모델로 변환하는 헬퍼"""
    rank = dto.get('rank', 999)
    return RankingResult(
        keyword=dto['keyword'],
        product_id=dto['product_id'],
        rank=rank if isinstance(rank, int) else 999,
        total_results=dto.get('total_results', 0),
        success=dto['success'],
        error_message=dto.get('error', dto.get('error_message'))
    )


class RankTrackingService(QObject):
    """순위 추적 서비스 (단순화됨)"""
    
    # 실시간 업데이트용 시그널들
    progress_updated = Signal(int, int, str)    # (현재, 전체, 메시지)
    project_created = Signal(object)            # TrackingProject
    keyword_added = Signal(object)              # TrackingKeyword  
    ranking_updated = Signal(int, str, int, int) # (keyword_id, keyword, rank, volume)
    processing_finished = Signal(bool, str, list) # (success, message, results)
    error_occurred = Signal(str)                # 오류 발생
    
    def __init__(self):
        """순위 추적 서비스 초기화"""
        super().__init__()
        self.is_running = False
        self.max_workers = 3  # 병렬 처리 스레드 수
    
    
    def create_project(self, project_url: str, product_name: str) -> TrackingProject:
        """URL과 상품명으로부터 새 추적 프로젝트 생성"""
        try:
            # 1. URL에서 상품 ID 추출
            adapter = RankTrackingAdapter()
            product_id = adapter.extract_product_id_from_url(project_url)
            logger.info(f"상품 ID 추출 완료: {product_id}")
            
            # 1.1. 중복 프로젝트 체크
            logger.info(f"상품 ID 중복 체크 시작: {product_id}")
            try:
                existing_project = self.get_project_by_product_id(product_id)
                if existing_project:
                    # 이미 존재하는 프로젝트가 있음
                    logger.warning(f"이미 존재하는 상품 ID: {product_id}, 기존 상품명: {existing_project.current_name}")
                    raise RankTrackingError(f"이미 존재하는 상품입니다.\n\n상품명: {existing_project.current_name}\n상품 ID: {product_id}\n\n프로젝트 목록에서 확인해주세요.")
                
                logger.info(f"상품 ID 중복 체크 통과: {product_id}")
                
            except RankTrackingError:
                # RankTrackingError는 다시 발생시켜서 호출자에게 전달
                raise
            except Exception as e:
                logger.error(f"중복 체크 중 오류 발생: {e}")
                # 중복 체크 실패 시에도 계속 진행하되 경고 로그 남김
                logger.warning("중복 체크 실패로 인해 프로젝트 생성을 계속 진행합니다")
            
            # 2. 스마트 상품 검색으로 상품 정보 조회
            logger.info("스마트 검색으로 상품 정보 조회 중...")
            api_product_info = smart_product_search(product_name, product_id)
                
            # 3. 프로젝트 생성
            if api_product_info:
                # API에서 가져온 실제 상품명 사용
                final_name = api_product_info.get('name', product_name)
                store_name = api_product_info.get('store_name', '')
                price = api_product_info.get('price', 0)
                category = api_product_info.get('category', '')
                image_url = api_product_info.get('image_url', '')
                
                logger.info("API 상품 정보 조회 성공:")
                logger.info(f"  실제 상품명: {final_name}")
                logger.info(f"  카테고리: {category}")
                logger.info(f"  스토어명: {store_name}")
                logger.info(f"  가격: {price}원")
            else:
                # API 실패 시 사용자 입력 정보 사용
                final_name = product_name
                store_name = ''
                price = 0
                category = ''
                image_url = ''
                logger.warning("API 상품 정보 조회 실패, 기본 정보로 생성")
            
            # 프로젝트 객체 생성
            project = TrackingProject(
                product_id=product_id,
                current_name=final_name,
                product_url=project_url,
                category=category,
                price=price,
                store_name=store_name,
                image_url=image_url
            )
            
            # repository를 통한 DB 저장
            project_id = rank_tracking_repository.insert_project(project)
            project.id = project_id
            
            logger.info(f"프로젝트 생성 완료: {final_name} (ID: {project_id})")
            
            # 시그널 발출
            self.project_created.emit(project)
            
            return project
            
        except Exception as e:
            logger.error(f"프로젝트 생성 실패: {e}")
            raise RankTrackingError(f"프로젝트 생성 중 오류 발생: {e}")
    
    def get_all_projects(self, active_only: bool = True) -> List[TrackingProject]:
        """모든 프로젝트 조회"""
        try:
            # repository 패턴 사용
            is_active_filter = True if active_only else None
            project_dicts = rank_tracking_repository.get_all_projects(is_active_filter)
            
            # Dict을 TrackingProject 객체로 변환
            projects = [_dict_to_tracking_project(p_dict) for p_dict in project_dicts]
            
            return projects
        except Exception as e:
            logger.error(f"프로젝트 목록 조회 실패: {e}")
            raise RankTrackingError(f"프로젝트 목록 조회 실패: {e}")
    
    def get_project_by_id(self, project_id: int) -> Optional[TrackingProject]:
        """ID로 프로젝트 조회"""
        try:
            p_dict = rank_tracking_repository.get_project_by_id(project_id)
            return _dict_to_tracking_project(p_dict) if p_dict else None
        except Exception as e:
            logger.error(f"프로젝트 조회 실패 (ID: {project_id}): {e}")
            return None
    
    def get_project_by_product_id(self, product_id: str) -> Optional[TrackingProject]:
        """상품 ID로 프로젝트 조회 (중복 확인용)"""
        try:
            p_dict = rank_tracking_repository.get_project_by_product_id(product_id)
            return _dict_to_tracking_project(p_dict) if p_dict else None
        except Exception as e:
            logger.error(f"프로젝트 조회 실패 (상품 ID: {product_id}): {e}")
            return None
    
    def add_keyword(self, project_id: int, keyword: str) -> TrackingKeyword:
        """키워드 추가 (engine_local에서 분석 후 DB에 저장)"""
        try:
            logger.info(f"키워드 추가 시작: '{keyword}' (프로젝트 {project_id})")
            
            # adapter에서 키워드 분석 수행
            analysis_result = rank_tracking_adapter.analyze_and_add_keyword(keyword)
            
            # DB에 키워드 추가
            keyword_id = rank_tracking_repository.add_keyword(project_id, keyword)
            
            if keyword_id == 0:
                # 이미 활성 상태인 키워드
                logger.warning(f"키워드 중복: {keyword} (프로젝트 {project_id})")
                raise RankTrackingError(f"키워드 '{keyword}'는 이미 등록되어 있습니다.")
            
            logger.info(f"키워드 추가 성공: {keyword} (ID: {keyword_id})")
            
            # 분석 결과가 성공적이면 키워드 정보 업데이트
            if analysis_result['success'] and analysis_result['ready_for_db']:
                self.update_keyword_info(
                    project_id=project_id,
                    keyword=keyword,
                    category=analysis_result['category'],
                    monthly_volume=analysis_result['monthly_volume']
                )
            
            # 키워드 관리 이력 기록
            if keyword_id > 0:
                rank_tracking_repository.add_keyword_management_history(project_id, keyword, 'add')
            
            # TrackingKeyword 객체 생성
            tracking_keyword = TrackingKeyword(
                id=keyword_id,
                project_id=project_id,
                keyword=keyword,
                is_active=True,
                category=analysis_result.get('category', '-'),
                monthly_volume=analysis_result.get('monthly_volume', -1)
            )
            
            return tracking_keyword
            
        except Exception as e:
            logger.error(f"키워드 추가 실패: {keyword}: {e}")
            raise RankTrackingError(f"키워드 추가 실패: {e}")
    
    def get_project_keywords(self, project_id: int) -> List[TrackingKeyword]:
        """프로젝트의 키워드 목록 조회"""
        try:
            keyword_dicts = rank_tracking_repository.get_project_keywords(project_id)
            return [_dict_to_tracking_keyword(k_dict) for k_dict in keyword_dicts]
        except Exception as e:
            logger.error(f"키워드 목록 조회 실패 (프로젝트 ID: {project_id}): {e}")
            return []
    
    def update_keyword_info(self, project_id: int, keyword: str, category: str, monthly_volume: int) -> bool:
        """키워드 정보 업데이트 (백그라운드 워커에서 사용)"""
        try:
            result = rank_tracking_repository.update_keyword_volume_and_category(project_id, keyword, monthly_volume, category)
            
            if result:
                logger.info(f"키워드 정보 업데이트: {keyword} -> 볼륨: {monthly_volume}, 카테고리: {category}")
                # UI 업데이트를 위한 시그널 발출
                keywords = self.get_project_keywords(project_id)
                for kw in keywords:
                    if kw.keyword == keyword:
                        self.ranking_updated.emit(kw.id or 0, keyword, 0, monthly_volume)  # rank는 0으로 설정
                        break
            
            return result
        except Exception as e:
            logger.error(f"키워드 정보 업데이트 실패: {keyword}: {e}")
            return False
    
    def _update_keyword_info_realtime(self, project_id: int, keyword: str) -> bool:
        """개별 키워드의 월검색량과 카테고리를 실시간으로 업데이트"""
        try:
            # 키워드 분석 수행
            analysis = self.analyze_keyword_for_tracking(keyword)
            
            if analysis['success']:
                # DB 업데이트
                return self.update_keyword_info(
                    project_id=project_id,
                    keyword=keyword,
                    category=analysis['category'],
                    monthly_volume=analysis['monthly_volume']
                )
            else:
                logger.warning(f"키워드 '{keyword}' 분석 실패: {analysis.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 실시간 정보 업데이트 실패: {e}")
            return False
    
    def delete_keyword(self, project_id: int, keyword_text: str) -> bool:
        """키워드 삭제"""
        try:
            success = rank_tracking_repository.delete_keyword_by_text(project_id, keyword_text)
            
            # 삭제 성공 시 이력 기록
            if success:
                rank_tracking_repository.add_keyword_management_history(project_id, keyword_text, 'delete')
            
            return success
        except Exception as e:
            logger.error(f"키워드 삭제 실패: {keyword_text}: {e}")
            return False
    
    def get_ranking_overview(self, project_id: int) -> dict:
        """순위 현황 조회"""
        try:
            return rank_tracking_repository.get_project_ranking_overview(project_id)
        except Exception as e:
            logger.error(f"순위 현황 조회 실패 (프로젝트 ID: {project_id}): {e}")
            return {'dates': [], 'keywords': {}}
    
    def get_keyword_management_history(self, project_id: int) -> List[Dict[str, Any]]:
        """키워드 관리 이력 조회"""
        try:
            return rank_tracking_repository.get_keyword_management_history(project_id)
        except Exception as e:
            logger.error(f"키워드 관리 이력 조회 실패 (프로젝트 ID: {project_id}): {e}")
            return []
    
    def get_basic_info_change_history(self, project_id: int) -> List[Dict[str, Any]]:
        """기본정보 변경 이력 조회"""
        try:
            return rank_tracking_repository.get_basic_info_change_history(project_id)
        except Exception as e:
            logger.error(f"기본정보 변경 이력 조회 실패 (프로젝트 ID: {project_id}): {e}")
            return []
    
    def get_ranking_history_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        """프로젝트의 순위 이력 조회"""
        try:
            return rank_tracking_repository.get_ranking_history_for_project(project_id)
        except Exception as e:
            logger.error(f"프로젝트 순위 이력 조회 실패 (프로젝트 ID: {project_id}): {e}")
            return []
    
    def delete_project(self, project_id: int) -> bool:
        """프로젝트 삭제 (키워드, 순위 이력 모두 포함)"""
        try:
            # Repository의 delete_project 메서드를 호출
            # 이 메서드는 프로젝트와 관련된 모든 데이터(키워드, 순위 이력)를 함께 삭제해야 함
            success = rank_tracking_repository.delete_project(project_id)
            
            if success:
                logger.info(f"프로젝트 삭제 완료 (ID: {project_id})")
                return True
            else:
                logger.warning(f"프로젝트 삭제 실패 (ID: {project_id})")
                return False
                
        except Exception as e:
            logger.error(f"프로젝트 삭제 오류 (ID: {project_id}): {e}")
            return False
    
    def add_keywords_to_project(self, project_id: int, keywords: List[str]) -> int:
        """프로젝트에 키워드 추가 (engine_local에서 키워드 생성)"""
        try:
            # 프로젝트 정보 조회
            project = self.get_project_by_id(project_id)
            if not project:
                logger.error(f"프로젝트를 찾을 수 없습니다: {project_id}")
                return 0
            
            # engine_local에서 상품명으로부터 키워드 생성
            if len(keywords) == 1 and keywords[0] == project.current_name:
                # 상품명 하나만 전달된 경우 - 키워드 생성
                generated_keywords = rank_tracking_engine.generate_keywords_from_product(project.current_name)
                keywords = generated_keywords
            
            # 키워드 배치 추가
            result = self.add_keywords_batch(project_id, keywords)
            return result['added_count']
            
        except Exception as e:
            logger.error(f"키워드 추가 프로세스 실패: {e}")
            return 0
    
    def add_keywords_batch(self, project_id: int, keywords: List[str]) -> dict:
        """UI용 키워드 배치 추가 (engine_local 사용)"""
        try:
            # 기존 키워드 목록 조회
            existing_keywords = rank_tracking_repository.get_project_keywords(project_id)
            existing_keyword_texts = {kw['keyword'].lower().strip() for kw in existing_keywords}
            
            # engine_local에서 배치 결과 계산
            batch_result = rank_tracking_engine.calculate_keyword_batch_results(keywords, existing_keyword_texts)
            
            new_keywords = batch_result['new_keywords']
            duplicate_keywords = batch_result['duplicate_keywords']
            successfully_added_keywords = []
            failed_keywords = []
            
            # 새 키워드 추가
            duplicate_keyword_set = {k.lower().strip() for k in duplicate_keywords}
            
            for keyword in new_keywords:
                try:
                    keyword_id = rank_tracking_repository.add_keyword(project_id, keyword)
                    if keyword_id and keyword_id > 0:
                        successfully_added_keywords.append(keyword)
                        logger.info(f"키워드 추가 성공: {keyword} (ID: {keyword_id})")
                    elif keyword.lower().strip() in duplicate_keyword_set:
                        # 엔진이 중복으로 판단한 케이스는 이미 duplicate_keywords에 있음
                        pass
                    else:
                        failed_keywords.append(keyword)
                        logger.warning(f"키워드 추가 실패: {keyword} (ID: {keyword_id})")
                except Exception as e:
                    failed_keywords.append(keyword)
                    logger.error(f"키워드 '{keyword}' 추가 중 오류: {e}")
            
            return {
                'success': len(successfully_added_keywords) > 0,
                'added_count': len(successfully_added_keywords),
                'successfully_added_keywords': successfully_added_keywords,
                'duplicate_keywords': duplicate_keywords,
                'failed_keywords': failed_keywords,
                'new_keywords': new_keywords
            }
            
        except Exception as e:
            logger.error(f"키워드 배치 추가 실패: {e}")
            return {
                'success': False,
                'added_count': 0,
                'successfully_added_keywords': [],
                'duplicate_keywords': [],
                'failed_keywords': keywords,
                'new_keywords': [],
                'error': str(e)
            }
    
    def update_keyword_category_only(self, project_id: int, keyword: str, category: str) -> bool:
        """카테고리만 업데이트 (병렬 처리용)"""
        try:
            return rank_tracking_repository.update_keyword_by_text(project_id, keyword, category=category)
        except Exception as e:
            logger.error(f"카테고리 업데이트 실패: {keyword}: {e}")
            return False
    
    def update_keyword_volume_only(self, project_id: int, keyword: str, monthly_volume: int) -> bool:
        """월검색량만 업데이트 (병렬 처리용)"""
        try:
            return rank_tracking_repository.update_keyword_by_text(project_id, keyword, monthly_volume=monthly_volume)
        except Exception as e:
            logger.error(f"월검색량 업데이트 실패: {keyword}: {e}")
            return False
    
    def analyze_keyword_for_tracking(self, keyword: str) -> dict:
        """키워드 분석 (어댑터 레이어 위임)"""
        try:
            return rank_tracking_adapter.analyze_keyword_for_tracking(keyword)
        except Exception as e:
            logger.error(f"키워드 분석 실패: {keyword}: {e}")
            return {
                'success': False,
                'keyword': keyword,
                'category': '-',
                'monthly_volume': -1,
                'error': str(e)
            }
    
    def batch_update_keywords_volume(self, project_id: int, keywords: List[str]) -> dict:
        """키워드 배치 월검색량 업데이트 (engine_local 사용)"""
        try:
            # adapter에서 분석 수행
            analysis_result = rank_tracking_adapter.analyze_keywords_batch(keywords)
            
            # DB 업데이트 수행
            updated_count = 0
            failed_count = 0
            
            for result in analysis_result['results']:
                try:
                    if result['success']:
                        # DB 업데이트
                        success = self.update_keyword_info(
                            project_id=project_id,
                            keyword=result['keyword'],
                            category=result['category'],
                            monthly_volume=result['monthly_volume']
                        )
                        
                        if success:
                            updated_count += 1
                        else:
                            failed_count += 1
                            result['error'] = 'DB 업데이트 실패'
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    result['error'] = str(e)
                    logger.error(f"키워드 '{result['keyword']}' DB 업데이트 실패: {e}")
            
            # 결과 반환
            return {
                'success': updated_count > 0,
                'updated_count': updated_count,
                'failed_count': failed_count,
                'total_count': len(keywords),
                'results': analysis_result['results']
            }
            
        except Exception as e:
            logger.error(f"키워드 배치 월검색량 업데이트 실패: {e}")
            return {
                'success': False,
                'updated_count': 0,
                'failed_count': len(keywords),
                'total_count': len(keywords),
                'results': [],
                'error': str(e)
            }
    
    
    def get_keyword_search_volume(self, keyword: str) -> tuple[bool, int]:
        """키워드 검색량 조회"""
        try:
            from src.vendors.naver.client_factory import get_keyword_tool_client
            
            keyword_client = get_keyword_tool_client()
            if not keyword_client:
                return False, -1
            
            # 검색량 조회
            result = keyword_client.get_search_volume([keyword])
            if result and keyword in result:
                return True, result[keyword].get('monthly_volume', -1)
            
            return False, -1
            
        except Exception as e:
            logger.error(f"키워드 검색량 조회 실패: {keyword}: {e}")
            return False, -1
    
    def update_keywords_search_volume(self, project_id: int) -> tuple[bool, str]:
        """프로젝트 키워드들의 검색량 업데이트"""
        try:
            from src.vendors.naver.client_factory import get_keyword_tool_client
            
            keyword_client = get_keyword_tool_client()
            if not keyword_client:
                return False, "네이버 검색광고 API 설정이 필요합니다."
            
            keywords = self.get_project_keywords(project_id)
            if not keywords:
                return True, "업데이트할 키워드가 없습니다."
            
            # 키워드 텍스트만 추출
            keyword_texts = [kw.keyword for kw in keywords]
            
            # 검색량 조회
            volume_results = keyword_client.get_search_volume(keyword_texts)
            
            updated_count = 0
            
            for keyword in keywords:
                if keyword.keyword in volume_results:
                    volume_data = volume_results[keyword.keyword]
                    monthly_volume = volume_data.get('monthly_volume', -1)
                    category = volume_data.get('category', '')
                    
                    # DB 업데이트
                    success = rank_tracking_repository.update_keyword_by_text(
                        project_id, 
                        keyword.keyword, 
                        category=category, 
                        monthly_volume=monthly_volume
                    )
                    if success:
                        updated_count += 1
            
            message = f"{updated_count}/{len(keywords)}개 키워드 검색량이 업데이트되었습니다."
            return True, message
            
        except Exception as e:
            logger.error(f"키워드 검색량 업데이트 실패: {e}")
            return False, f"검색량 업데이트 중 오류 발생: {str(e)}"
    
    
    def get_project_with_keywords(self, project_id: int) -> tuple[Optional[TrackingProject], List[TrackingKeyword]]:
        """프로젝트와 키워드를 함께 조회"""
        project = self.get_project_by_id(project_id)
        keywords = self.get_project_keywords(project_id)
        return project, keywords
    
    def get_ranking_history(self, keyword_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """키워드의 순위 변화 이력"""
        try:
            return rank_tracking_repository.get_ranking_history(keyword_id, limit)
        except Exception as e:
            logger.error(f"순위 이력 조회 실패 (키워드 ID: {keyword_id}): {e}")
            return []
    
    def prepare_table_data(self, project_id: int) -> Dict[str, Any]:
        """테이블 데이터 준비 (engine_local 사용)"""
        try:
            # 기본 데이터 조회 (service 담당)
            project = self.get_project_by_id(project_id)
            if not project:
                return {"success": False, "message": "프로젝트를 찾을 수 없습니다."}
            
            keywords = self.get_project_keywords(project_id)
            overview = self.get_project_overview(project_id)
            
            # engine_local에서 분석 수행
            return rank_tracking_engine.prepare_table_data_analysis(project, keywords, overview)
            
        except Exception as e:
            logger.error(f"테이블 데이터 준비 실패: {e}")
            return {"success": False, "message": f"오류 발생: {e}"}
    
    def prepare_table_row_data(self, project_id: int, keyword_data: dict, all_dates: list, project_category_base: str) -> list:
        """테이블 행 데이터 준비 (engine_local 사용)"""
        try:
            # 워커 매니저에서 현재 순위 데이터 가져오기 (service 담당)
            from .worker import ranking_worker_manager
            current_time = ranking_worker_manager.get_current_time(project_id)
            current_rankings = ranking_worker_manager.get_current_rankings(project_id)
            
            # engine_local에서 분석 수행
            return rank_tracking_engine.prepare_table_row_data_analysis(
                keyword_data, all_dates, current_rankings, current_time
            )
            
        except Exception as e:
            logger.error(f"테이블 행 데이터 준비 실패: {e}")
            return [keyword_data.get('keyword', ''), '-', '-'] + ['-'] * len(all_dates)
    
    def should_show_date_columns(self, project_id: int) -> bool:
        """날짜 컬럼을 표시해야 하는지 판단 (키워드가 있을 때만)"""
        try:
            keywords = self.get_project_keywords(project_id)
            overview = self.get_project_overview(project_id)
            keywords_data = overview.get("keywords", {}) if overview else {}
            
            total_keywords = len(keywords_data) + len(keywords)
            return total_keywords > 0
        except Exception as e:
            logger.error(f"날짜 컬럼 표시 판단 실패: {e}")
            return False
    
    def delete_selected_keywords_by_ids(self, project_id: int, keyword_ids: List[int], keyword_names: List[str]) -> Tuple[bool, str]:
        """선택된 키워드들 삭제 (UI에서 비즈니스 로직 분리)"""
        try:
            if not keyword_ids:
                return False, "삭제할 키워드가 선택되지 않았습니다."
            
            success_count = 0
            for i, keyword_id in enumerate(keyword_ids):
                keyword_name = keyword_names[i] if i < len(keyword_names) else f"키워드 ID {keyword_id}"
                try:
                    if self.delete_keyword_by_id(keyword_id):
                        success_count += 1
                        logger.info(f"키워드 삭제 성공: {keyword_name} (ID: {keyword_id})")
                        # 키워드 삭제 이력 기록
                        rank_tracking_repository.add_keyword_management_history(project_id, keyword_name, 'delete')
                    else:
                        logger.warning(f"키워드 삭제 실패: {keyword_name} (ID: {keyword_id})")
                except Exception as e:
                    logger.error(f"키워드 삭제 중 오류: {keyword_name} (ID: {keyword_id}): {e}")
            
            if success_count > 0:
                return True, f"✅ {success_count}개 키워드가 삭제되었습니다."
            else:
                return False, "❌ 키워드 삭제에 실패했습니다."
                
        except Exception as e:
            logger.error(f"키워드 일괄 삭제 실패: {e}")
            return False, f"❌ 키워드 삭제 중 오류가 발생했습니다: {str(e)}"
    
    def delete_keyword_by_id(self, keyword_id: int) -> bool:
        """키워드 ID로 삭제"""
        try:
            return rank_tracking_repository.delete_keyword_by_id(keyword_id)
        except Exception as e:
            logger.error(f"키워드 ID {keyword_id} 삭제 실패: {e}")
            return False
    
    def process_ranking_check_for_project(self, project_id: int) -> Dict[str, Any]:
        """프로젝트 순위 확인 처리 (worker에서 비즈니스 로직 분리)"""
        try:
            # 프로젝트 정보 조회
            project = self.get_project_by_id(project_id)
            if not project:
                return {
                    'success': False,
                    'message': '프로젝트를 찾을 수 없습니다.',
                    'data': None
                }
            
            # 키워드 조회
            keywords = self.get_project_keywords(project_id)
            if not keywords:
                return {
                    'success': False,
                    'message': '추적할 키워드가 없습니다.',
                    'data': None
                }
            
            return {
                'success': True,
                'message': f"프로젝트 '{project.current_name}' 순위 확인 준비 완료",
                'data': {
                    'project': project,
                    'keywords': keywords
                }
            }
            
        except Exception as e:
            logger.error(f"순위 확인 준비 실패 (프로젝트 {project_id}): {e}")
            return {
                'success': False,
                'message': f'순위 확인 준비 실패: {str(e)}',
                'data': None
            }
    
    def process_single_keyword_ranking(self, keyword_obj, product_id: str) -> Tuple[Dict[str, Any], bool]:
        """단일 키워드 순위 확인 처리 (adapter 사용) - RankingCheckDTO 반환"""
        return rank_tracking_adapter.process_single_keyword_ranking(keyword_obj, product_id)
    
    def create_failed_ranking_result(self, keyword: str, error_message: str) -> RankingResult:
        """실패한 순위 결과 생성 (worker에서 models import 방지)"""
        return RankingResult(
            keyword=keyword,
            success=False,
            rank=999,
            error_message=error_message
        )
    
    def save_ranking_results_for_project(self, project_id: int, results: list) -> bool:
        """프로젝트 순위 결과 저장 (worker에서 비즈니스 로직 분리)"""
        try:
            if results:
                return self.save_ranking_results(project_id, results)
            return True
        except Exception as e:
            logger.error(f"순위 결과 저장 실패 (프로젝트 {project_id}): {e}")
            return False
    
    
    
    
    
    
    def get_keyword_category_from_vendor(self, keyword: str) -> str:
        """키워드 카테고리 조회 - adapters로 위임"""
        try:
            adapter = RankTrackingAdapter()
            return adapter.get_keyword_category(keyword) or "-"
        except Exception as e:
            logger.warning(f"카테고리 조회 실패: {keyword}: {e}")
            return "-"
    
    def get_keyword_volume_from_vendor(self, keyword: str) -> int:
        """키워드 월검색량 조회 - adapters로 위임"""
        try:
            adapter = RankTrackingAdapter()
            vol = adapter.get_keyword_monthly_volume(keyword)
            return vol if isinstance(vol, int) else -1
        except Exception as e:
            logger.warning(f"월검색량 조회 실패: {keyword}: {e}")
            return -1
    
    def process_keyword_info_update(self, project_id: int, keyword: str) -> Dict[str, Any]:
        """키워드 정보 업데이트 처리 (engine_local 사용)"""
        try:
            # adapter에서 분석 수행
            analysis_result = rank_tracking_adapter.process_keyword_info_analysis(keyword)
            
            # DB 업데이트
            success_count = 0
            category = analysis_result['category']
            monthly_volume = analysis_result['monthly_volume']
            
            # 카테고리 업데이트
            if category != "-":
                try:
                    if self.update_keyword_category_only(project_id, keyword, category):
                        success_count += 1
                except Exception as e:
                    logger.error(f"카테고리 DB 업데이트 실패: {keyword}: {e}")
            
            # 월검색량 업데이트
            if monthly_volume >= 0:
                try:
                    if self.update_keyword_volume_only(project_id, keyword, monthly_volume):
                        success_count += 1
                except Exception as e:
                    logger.error(f"월검색량 DB 업데이트 실패: {keyword}: {e}")
            
            return {
                'success': success_count > 0,
                'category': category,
                'monthly_volume': monthly_volume
            }
            
        except Exception as e:
            logger.error(f"키워드 정보 업데이트 실패: {keyword}: {e}")
            return {
                'success': False,
                'category': '-',
                'monthly_volume': -1
            }
    
    def analyze_and_add_keyword(self, project_id: int, keyword: str) -> Tuple[bool, str]:
        """키워드 분석 후 추가 (engine_local 사용)"""
        try:
            # engine_local에서 분석 수행
            analysis_result = rank_tracking_adapter.analyze_and_add_keyword(keyword)
            
            if not analysis_result['success']:
                return False, analysis_result.get('error', '키워드 분석에 실패했습니다.')
            
            if analysis_result['ready_for_db']:
                # 키워드 정보 DB 업데이트
                success = self.update_keyword_info(
                    project_id, keyword, 
                    analysis_result.get('category', ''), 
                    analysis_result.get('monthly_volume', -1)
                )
                
                if success:
                    return True, f"키워드 '{keyword}' 추가 완료"
                else:
                    return False, "키워드 추가에 실패했습니다."
            else:
                return False, "키워드 분석 결과가 DB 저장에 적합하지 않습니다."
                
        except Exception as e:
            logger.error(f"키워드 분석/추가 실패: {e}")
            return False, f"오류 발생: {e}"
    
    def get_current_project_keywords_for_analysis(self, project_id: int) -> Tuple[bool, List[str]]:
        """키워드 분석을 위한 현재 프로젝트 키워드 목록 조회"""
        try:
            keywords = self.get_project_keywords(project_id)
            keyword_texts = [kw.keyword for kw in keywords if hasattr(kw, 'keyword')]
            return True, keyword_texts
        except Exception as e:
            logger.error(f"키워드 목록 조회 실패: {e}")
            return False, []
    
    def get_keyword_ranking_history(self, project_id: int, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """키워드 텍스트로 순위 이력 조회"""
        try:
            # 먼저 키워드 존재 여부 확인
            keywords = self.get_project_keywords(project_id)
            keyword_obj = None
            for kw in keywords:
                if kw.keyword == keyword:
                    keyword_obj = kw
                    break
            
            if not keyword_obj:
                logger.warning(f"키워드 '{keyword}'를 프로젝트 {project_id}에서 찾을 수 없음")
                return []
            
            # 순위 이력 조회 (repository 사용)
            return rank_tracking_repository.get_keyword_ranking_history(project_id, keyword, limit)
            
        except Exception as e:
            logger.error(f"키워드 순위 이력 조회 실패 (프로젝트: {project_id}, 키워드: {keyword}): {e}")
            return []
    
    def save_ranking_result(self, ranking_result) -> int:
        """순위 결과 저장"""
        try:
            return rank_tracking_repository.save_ranking_result(
                ranking_result.keyword_id,
                ranking_result.rank_position,
                ranking_result.page_number,
                ranking_result.total_results,
                ranking_result.competitor_data
            )
        except Exception as e:
            logger.error(f"순위 결과 저장 실패: {e}")
            return 0
    
    def get_project_overview(self, project_id: int, limit: int = 10) -> dict:
        """프로젝트 개요 정보"""
        try:
            return rank_tracking_repository.get_project_ranking_overview(project_id)
        except Exception as e:
            logger.error(f"프로젝트 개요 조회 실패: {e}")
            return {'dates': [], 'keywords': {}}
    
    
    def get_product_category(self, product_id: str) -> tuple[bool, str]:
        """상품 카테고리 조회 (engine_local 사용)"""
        try:
            # adapter에서 분석 수행
            analysis_result = rank_tracking_adapter.get_product_category_analysis(product_id)
            
            return analysis_result['success'], analysis_result['category']
            
        except Exception as e:
            logger.error(f"상품 카테고리 조회 실패: {e}")
            return False, ""
    
    def check_keyword_ranking(self, keyword: str, product_id: str) -> RankingResult:
        """키워드 순위 확인 (adapter 사용 + DTO → Model 변환)"""
        dto = rank_tracking_adapter.check_keyword_ranking(keyword, product_id)
        return _dto_to_ranking_result(dto)
    
    def save_ranking_results(self, project_id: int, results: List[RankingResult]) -> bool:
        """순위 확인 결과 저장"""
        try:
            saved_count = 0
            
            # 워커 매니저에서 설정한 현재 시간 가져오기
            from .worker import ranking_worker_manager
            current_time = ranking_worker_manager.get_current_time(project_id)
            
            # 프로젝트의 모든 키워드 가져오기
            keywords = rank_tracking_repository.get_keywords(project_id)
            keyword_map = {kw['keyword']: kw['id'] for kw in keywords}
            
            logger.info(f"순위 결과 저장 시작: 프로젝트={project_id}, 시간={current_time}, 결과수={len(results)}")
            
            for result in results:
                try:
                    keyword_id = keyword_map.get(result.keyword)
                    if not keyword_id:
                        logger.warning(f"키워드 ID를 찾을 수 없음: {result.keyword}")
                        continue
                    
                    logger.info(f"순위 저장 시도: 키워드={result.keyword}, 키워드ID={keyword_id}, 순위={result.rank}, 시간={current_time}")
                    
                    ranking_id = rank_tracking_repository.save_ranking_result(
                        keyword_id=keyword_id,
                        rank_position=result.rank,
                        page_number=1,
                        total_results=result.total_results or 0,
                        competitor_data={},
                        search_date=current_time  # 워커에서 설정한 시간 사용
                    )
                    if ranking_id:
                        saved_count += 1
                        logger.info(f"순위 저장 성공: ranking_id={ranking_id}")
                except Exception as e:
                    logger.error(f"순위 결과 저장 실패: {result.keyword}: {e}")
                    continue
            
            logger.info(f"순위 결과 저장 완료: {saved_count}/{len(results)}")
            return saved_count > 0
            
        except Exception as e:
            logger.error(f"순위 결과 배치 저장 실패: {e}")
            return False
    
    def check_project_rankings(self, project_id: int) -> dict:
        """프로젝트 전체 키워드 순위 확인 (워커용)"""
        try:
            # 프로젝트 정보 조회
            project = self.get_project_by_id(project_id)
            if not project:
                return {
                    'success': False,
                    'message': '프로젝트를 찾을 수 없습니다.',
                    'results': []
                }
            
            # 키워드 조회
            keywords = self.get_project_keywords(project_id)
            if not keywords:
                return {
                    'success': False,
                    'message': '추적할 키워드가 없습니다.',
                    'results': []
                }
            
            # 순위 확인 결과
            results = []
            success_count = 0
            
            for keyword_obj in keywords:
                result = self.check_keyword_ranking(keyword_obj.keyword, project.product_id)
                results.append(result)
                if result.success:
                    success_count += 1
            
            # 결과 저장
            if results:
                self.save_ranking_results(project_id, results)
            
            return {
                'success': success_count > 0,
                'message': f"순위 확인 완료: {success_count}/{len(keywords)} 키워드",
                'results': results
            }
            
        except Exception as e:
            logger.error(f"프로젝트 순위 확인 실패: {e}")
            return {
                'success': False,
                'message': f"순위 확인 중 오류 발생: {e}",
                'results': []
            }
    
    def delete_ranking_data_by_date(self, project_id: int, date_str: str) -> bool:
        """특정 날짜의 순위 데이터 삭제"""
        try:
            success = rank_tracking_repository.delete_ranking_results_by_date(project_id, date_str)
            
            if success:
                logger.info(f"날짜별 순위 데이터 삭제 성공: 프로젝트 {project_id}, 날짜 {date_str}")
            else:
                logger.warning(f"날짜별 순위 데이터 삭제 실패: 프로젝트 {project_id}, 날짜 {date_str}")
            
            return success
            
        except Exception as e:
            logger.error(f"날짜별 순위 데이터 삭제 오류: {e}")
            return False
    
    # 프로세싱 중지용 플래그
    _stop_processing = False
    
    def stop_processing(self):
        """처리 중지 플래그 설정"""
        self._stop_processing = True
        
    def reset_processing(self):
        """처리 중지 플래그 리셋"""
        self._stop_processing = False
    
    def refresh_project_info(self, project_id: int) -> Dict[str, Any]:
        """프로젝트 상품 정보 새로고침 (engine_local 사용)"""
        try:
            # 1. 프로젝트 조회
            project = self.get_project_by_id(project_id)
            if not project:
                return {
                    'success': False,
                    'message': '프로젝트를 찾을 수 없습니다.'
                }
            
            # 2. adapter에서 분석
            analysis_result = rank_tracking_adapter.refresh_product_info_analysis(project)
            
            if not analysis_result['success']:
                return analysis_result
            
            # 3. DB 업데이트 (service의 책임)
            changes_detected = analysis_result['changes']
            if changes_detected:
                # 변경 기록 저장
                for change in changes_detected:
                    rank_tracking_repository.add_basic_info_change_record(
                        project_id=project_id,
                        field_name=change['field_name'],
                        old_value=change['old_value'],
                        new_value=change['new_value'],
                        is_auto=True
                    )
                
                # 프로젝트 정보 업데이트
                self.update_project(project_id, analysis_result['new_info'])
                logger.info(f"프로젝트 정보 업데이트 완료: {len(changes_detected)}개 변경사항")
            
            # 4. 결과 메시지 생성
            if changes_detected:
                change_messages = []
                for change in changes_detected:
                    change_messages.append(f"• {change['field']}: {change['old']} → {change['new']}")
                
                message = f"✅ {project.current_name} 상품 정보가 업데이트되었습니다.\n\n변경사항:\n" + "\n".join(change_messages)
            else:
                message = f"ℹ️ {project.current_name} 상품 정보에 변경사항이 없습니다."
            
            return {
                'success': True,
                'message': message,
                'product_info': analysis_result['product_info'],
                'changes_count': len(changes_detected)
            }
            
        except Exception as e:
            logger.error(f"프로젝트 정보 새로고침 실패: {e}")
            return {
                'success': False,
                'message': f'상품 정보 새로고침 중 오류가 발생했습니다: {str(e)}'
            }
    
    def update_project(self, project_id: int, new_info: Dict[str, Any]) -> bool:
        """프로젝트 기본정보 일부 필드만 안전하게 갱신"""
        try:
            # repository의 update_project_info 메서드 사용
            success = rank_tracking_repository.update_project_info(project_id, new_info)
            
            if success:
                logger.info(f"프로젝트 업데이트 완료: ID={project_id}")
            else:
                logger.error(f"프로젝트 업데이트 실패: ID={project_id}")
            
            return success
        except Exception as e:
            logger.error(f"프로젝트 업데이트 실패(ID={project_id}): {e}")
            return False
    
    def get_project_changes_history(self, project_id: int) -> Dict[str, Any]:
        """프로젝트 변경사항 이력 조회 (기존 통합관리프로그램과 동일)"""
        try:
            # 현재는 간단한 구현 - 추후 실제 변경사항 로그 시스템 구현 시 확장
            project = self.get_project_by_id(project_id)
            if not project:
                return {
                    'success': False,
                    'changes': [],
                    'message': '프로젝트를 찾을 수 없습니다.'
                }
            
            # 임시로 기본 메시지 반환 (실제로는 DB에서 변경사항 조회)
            return {
                'success': True,
                'changes': [],  # 실제 변경사항 데이터는 추후 구현
                'message': '변경사항 조회 완료'
            }
            
        except Exception as e:
            logger.error(f"프로젝트 변경사항 조회 실패: {e}")
            return {
                'success': False,
                'changes': [],
                'message': f'변경사항 조회 중 오류가 발생했습니다: {str(e)}'
            }






    
    # ================ Excel 내보내기 메서드들 ================
    # Note: 다이얼로그는 ui_table.py로 이동됨. 필요시 adapters를 직접 사용.
    
    # ================ 순위 확인 관련 메서드들 ================
    
    def start_ranking_check(self, project_id: int) -> bool:
        """순위 확인 시작 (비즈니스 로직)"""
        try:
            # 프로젝트 존재 여부 확인
            project = self.get_project_by_id(project_id)
            if not project:
                logger.warning(f"프로젝트가 존재하지 않습니다: {project_id}")
                return False
            
            # 워커 매니저를 통해 순위 확인 시작
            from .worker import ranking_worker_manager
            success = ranking_worker_manager.start_ranking_check(project_id)
            
            if success:
                logger.info(f"프로젝트 '{project.current_name}' 순위 확인 시작")
            else:
                logger.info(f"프로젝트 '{project.current_name}'의 순위 확인이 이미 실행 중입니다.")
            
            return success
            
        except Exception as e:
            logger.error(f"순위 확인 시작 실패: {e}")
            return False
    
    def stop_ranking_check(self, project_id: int) -> bool:
        """순위 확인 정지 (비즈니스 로직)"""
        try:
            project = self.get_project_by_id(project_id)
            if not project:
                logger.warning(f"프로젝트가 존재하지 않습니다: {project_id}")
                return False
            
            from .worker import ranking_worker_manager
            success = ranking_worker_manager.stop_ranking_check(project_id)
            
            if success:
                logger.info(f"프로젝트 '{project.current_name}' 순위 확인 정지")
            
            return success
            
        except Exception as e:
            logger.error(f"순위 확인 정지 실패: {e}")
            return False
    
    def is_ranking_in_progress(self, project_id: int) -> bool:
        """순위 확인이 진행 중인지 확인"""
        try:
            from .worker import ranking_worker_manager
            return ranking_worker_manager.is_ranking_in_progress(project_id)
        except Exception as e:
            logger.error(f"순위 확인 상태 조회 실패: {e}")
            return False
    
    def get_ranking_progress(self, project_id: int) -> tuple[int, int]:
        """순위 확인 진행률 조회 (current, total)"""
        try:
            from .worker import ranking_worker_manager
            return ranking_worker_manager.get_current_progress(project_id)
        except Exception as e:
            logger.error(f"순위 확인 진행률 조회 실패: {e}")
            return 0, 0
    
    def get_ranking_current_time(self, project_id: int) -> Optional[str]:
        """현재 순위 확인 시간 조회"""
        try:
            from .worker import ranking_worker_manager
            return ranking_worker_manager.get_current_time(project_id)
        except Exception as e:
            logger.error(f"순위 확인 시간 조회 실패: {e}")
            return None
    
    # ================ 키워드 추가 관련 메서드들 ================
    

    def add_keywords_batch_with_background_update(self, project_id: int, keywords: List[str]) -> Dict[str, Any]:
        """키워드 배치 추가 + 백그라운드 월검색량/카테고리 업데이트"""
        try:
            # 프로젝트 존재 여부 확인
            project = self.get_project_by_id(project_id)
            if not project:
                logger.warning(f"프로젝트가 존재하지 않습니다: {project_id}")
                return {
                    'success': False,
                    'added_keywords': [],
                    'duplicate_keywords': [],
                    'failed_keywords': keywords,
                    'error': 'Project not found'
                }
            
            added_keywords = []
            duplicate_keywords = []
            failed_keywords = []
            
            # 1단계: DB에 키워드만 즉시 추가 (API 분석 없이)
            for keyword in keywords:
                try:
                    # 전역 repository를 통해 키워드만 DB에 추가 (분석 없이)
                    keyword_id = rank_tracking_repository.add_keyword(project_id, keyword)
                    
                    if keyword_id > 0:
                        added_keywords.append(keyword)
                        # 키워드 관리 이력 추가
                        rank_tracking_repository.add_keyword_management_history(
                            project_id, keyword, 'add'
                        )
                    else:
                        duplicate_keywords.append(keyword)
                        
                except Exception as e:
                    if "이미 등록되어 있습니다" in str(e):
                        duplicate_keywords.append(keyword)
                    else:
                        failed_keywords.append(keyword)
                        logger.error(f"키워드 추가 실패: {keyword}, 오류: {e}")
            
            # 2단계: 로그 처리
            from src.desktop.common_log import log_manager
            
            # 성공 로그
            for keyword in added_keywords:
                log_manager.add_log(f"✅ '{keyword}' 키워드 추가 완료", "success")
            
            # 중복 로그  
            for keyword in duplicate_keywords:
                log_manager.add_log(f"⚠️ 중복: '{keyword}' 키워드가 이미 등록되어 있습니다.", "warning")
            
            # 실패 로그
            for keyword in failed_keywords:
                log_manager.add_log(f"❌ '{keyword}' 키워드 추가 실패", "error")
            
            # 3단계: 성공적으로 추가된 키워드가 있으면 백그라운드 업데이트 시작
            if added_keywords:
                log_manager.add_log(f"🎉 {len(added_keywords)}개 키워드 추가 완료!", "success")
                log_manager.add_log(f"🔍 월검색량/카테고리 조회를 시작합니다.", "info")
                self.start_background_keyword_info_update(project_id, added_keywords, project)
                
                if len(duplicate_keywords) > 0:
                    log_manager.add_log(f"⚠️ {len(duplicate_keywords)}개 키워드는 중복으로 건너뜀", "warning")
            
            return {
                'success': len(added_keywords) > 0,
                'added_keywords': added_keywords,
                'duplicate_keywords': duplicate_keywords,
                'failed_keywords': failed_keywords,
                'total_added': len(added_keywords)
            }
            
        except Exception as e:
            logger.error(f"키워드 배치 추가 실패: {e}")
            return {
                'success': False,
                'added_keywords': [],
                'duplicate_keywords': [],
                'failed_keywords': keywords,
                'error': str(e)
            }
    
    def start_background_keyword_info_update(self, project_id: int, keywords: List[str], project) -> bool:
        """백그라운드 키워드 정보 업데이트 시작"""
        try:
            if not keywords or not project_id:
                return False
            
            # 키워드 정보 워커 매니저를 통해 백그라운드 작업 시작
            from .worker import keyword_info_worker_manager
            success = keyword_info_worker_manager.start_keyword_info_update(
                project_id, 
                keywords, 
                project
            )
            
            if success:
                logger.info(f"프로젝트 '{project.current_name}' - {len(keywords)}개 키워드 월검색량/카테고리 조회 시작")
            else:
                logger.warning(f"프로젝트 '{project.current_name}' - 키워드 정보 조회 시작 실패")
                
            return success
            
        except Exception as e:
            logger.error(f"백그라운드 키워드 정보 업데이트 시작 실패: {e}")
            return False

    def get_product_info(self, product_name: str, product_id: str) -> Optional[dict]:
        """상품 정보 조회 (adapter 호출을 service에서 래핑)"""
        try:
            product_info = rank_tracking_adapter.get_product_info(product_name, product_id)
            if not product_info:
                return None
            
            # DTO를 dict로 변환하여 반환
            return {
                'name': product_info.name,
                'price': product_info.price,
                'store_name': product_info.store_name,
                'category': product_info.category,
                'image_url': product_info.image_url
            }
        except Exception as e:
            logger.error(f"상품 정보 조회 실패: {e}")
            return None

    # ================ 워커에서 사용하는 누락된 메서드들 ================
    
    def process_ranking_check_for_project(self, project_id: int) -> Dict[str, Any]:
        """프로젝트의 순위 확인 준비"""
        try:
            # 프로젝트 조회
            project = self.get_project_by_id(project_id)
            if not project:
                return {
                    'success': False,
                    'message': '프로젝트를 찾을 수 없습니다.'
                }
            
            # 키워드 조회
            keywords = self.get_project_keywords(project_id)
            if not keywords:
                return {
                    'success': False,
                    'message': '등록된 키워드가 없습니다.'
                }
            
            logger.info(f"순위 확인 준비 완료: {project.current_name}, {len(keywords)}개 키워드")
            
            return {
                'success': True,
                'message': '순위 확인 준비 완료',
                'data': {
                    'project': project,
                    'keywords': keywords
                }
            }
            
        except Exception as e:
            logger.error(f"순위 확인 준비 실패: {e}")
            return {
                'success': False,
                'message': f'순위 확인 준비 실패: {str(e)}'
            }
    
    def process_single_keyword_ranking(self, keyword_obj, product_id: str) -> tuple:
        """단일 키워드 순위 확인"""
        try:
            # adapters를 통한 순위 확인
            result = self.check_keyword_ranking(keyword_obj.keyword, product_id)
            
            success = result.success and result.rank > 0
            logger.info(f"키워드 '{keyword_obj.keyword}' 순위 확인: {result.rank} (성공: {success})")
            
            return result, success
            
        except Exception as e:
            logger.error(f"키워드 '{keyword_obj.keyword}' 순위 확인 실패: {e}")
            failed_result = self.create_failed_ranking_result(keyword_obj.keyword, str(e))
            return failed_result, False
    
    def create_failed_ranking_result(self, keyword: str, error_message: str) -> RankingResult:
        """실패한 순위 결과 생성"""
        return RankingResult(
            keyword=keyword,
            product_id="",
            rank=0,
            total_results=0,
            success=False,
            error_message=error_message
        )
    
    def save_ranking_results_for_project(self, project_id: int, results: List[RankingResult]) -> bool:
        """프로젝트의 순위 결과 저장"""
        try:
            return self.save_ranking_results(project_id, results)
        except Exception as e:
            logger.error(f"순위 결과 저장 실패: {e}")
            return False
    

# 전역 서비스 인스턴스
rank_tracking_service = RankTrackingService()
