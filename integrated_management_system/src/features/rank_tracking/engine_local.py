"""
순위 추적 핵심 비즈니스 로직 엔진 (CLAUDE.md 구조)
계산 및 알고리즘 로직만 담당 - 향후 .pyd 컴파일 대상
DB 접근 없음, 순수 계산 로직만
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import re

from .models import TrackingProject, TrackingKeyword, RankingResult, ProductInfo, RANK_OUT_OF_RANGE, DEFAULT_SAMPLE_SIZE
from .adapters import RankTrackingAdapter, clean_product_name, smart_product_search
from src.foundation.logging import get_logger

logger = get_logger("features.rank_tracking.engine_local")


class RankTrackingEngine:
    """순위 추적 핵심 엔진 - 순수 계산 로직만"""
    
    def __init__(self):
        self.adapter = RankTrackingAdapter()
    
    def analyze_keyword_for_tracking(self, keyword: str) -> Dict[str, Any]:
        """키워드 분석 (어댑터 레이어 위임)"""
        try:
            return self.adapter.analyze_keyword_for_tracking(keyword)
        except Exception as e:
            logger.error(f"키워드 분석 실패: {keyword}: {e}")
            return {
                'success': False,
                'keyword': keyword,
                'category': '-',
                'monthly_volume': 0,
                'error_message': str(e)
            }
    
    def check_keyword_ranking(self, keyword: str, product_id: str) -> RankingResult:
        """키워드 순위 확인"""
        try:
            # 어댑터를 통해 순위 확인
            ranking_data = self.adapter.check_keyword_ranking(keyword, product_id)
            
            if ranking_data['success']:
                return RankingResult(
                    keyword=keyword,
                    product_id=product_id,
                    rank=ranking_data['rank'],
                    success=True,
                    total_results=ranking_data.get('total_results', 0),
                    checked_at=datetime.now()
                )
            else:
                return RankingResult(
                    keyword=keyword,
                    product_id=product_id,
                    rank=999,  # 순위 없음
                    success=False,
                    error_message=ranking_data.get('error', '순위 확인 실패'),
                    checked_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 순위 확인 실패: {e}")
            return RankingResult(
                keyword=keyword,
                product_id=product_id,
                rank=999,
                success=False,
                error_message=str(e),
                checked_at=datetime.now()
            )
    
    def create_failed_ranking_result(self, keyword: str, error_message: str) -> RankingResult:
        """실패한 순위 결과 생성"""
        return RankingResult(
            keyword=keyword,
            success=False,
            rank=999,
            error_message=error_message
        )
    
    def process_keyword_info_update(self, keyword: str) -> Dict[str, Any]:
        """키워드 정보 업데이트 처리 (순수 분석 로직)"""
        try:
            # 카테고리와 월검색량 조회
            category = self.get_keyword_category_from_vendor(keyword)
            monthly_volume = self.get_keyword_volume_from_vendor(keyword)
            
            return {
                'success': True,
                'category': category,
                'monthly_volume': monthly_volume
            }
            
        except Exception as e:
            logger.error(f"키워드 정보 업데이트 실패: {keyword}: {e}")
            return {
                'success': False,
                'category': '-',
                'monthly_volume': -1,
                'error_message': str(e)
            }
    
    def get_keyword_category_from_vendor(self, keyword: str) -> str:
        """키워드 카테고리 조회"""
        try:
            category = self.adapter.get_keyword_category(keyword)
            return category if category else "-"
        except Exception as e:
            logger.warning(f"카테고리 조회 실패: {keyword}: {e}")
            return "-"
    
    def get_keyword_volume_from_vendor(self, keyword: str) -> int:
        """키워드 월검색량 조회"""
        try:
            volume = self.adapter.get_keyword_monthly_volume(keyword)
            return volume if volume is not None else -1
        except Exception as e:
            logger.warning(f"월검색량 조회 실패: {keyword}: {e}")
            return -1
    
    def refresh_product_info_analysis(self, project: TrackingProject) -> Dict[str, Any]:
        """프로젝트 상품 정보 새로고침 분석"""
        try:
            logger.info(f"프로젝트 정보 새로고침 시작: {project.current_name}")
            
            # 상품 정보 재조회
            product_info_dict = smart_product_search(project.current_name, project.product_id)
            
            if not product_info_dict:
                return {
                    'success': False,
                    'message': f'{project.current_name} 상품 정보를 찾을 수 없습니다.',
                    'changes': []
                }
            
            # 변경사항 분석
            new_info = {
                'current_name': clean_product_name(product_info_dict.get('name', '')),
                'price': product_info_dict.get('price', 0),
                'category': product_info_dict.get('category', ''),
                'store_name': product_info_dict.get('store_name', ''),
            }
            
            # 변경사항 감지
            changes_detected = self._detect_project_changes(project, new_info)
            
            # ProductInfo 객체 생성
            product_info = ProductInfo(
                product_id=product_info_dict.get('product_id', ''),
                name=new_info['current_name'],
                price=new_info['price'],
                category=new_info['category'],
                store_name=new_info['store_name'],
                description=product_info_dict.get('description', ''),
                image_url=product_info_dict.get('image_url', ''),
                url=product_info_dict.get('url', '')
            )
            
            return {
                'success': True,
                'new_info': new_info,
                'changes': changes_detected,
                'product_info': product_info
            }
            
        except Exception as e:
            logger.error(f"프로젝트 정보 새로고침 분석 실패: {e}")
            return {
                'success': False,
                'message': f'상품 정보 새로고침 중 오류가 발생했습니다: {str(e)}',
                'changes': []
            }
    
    def _detect_project_changes(self, project: TrackingProject, new_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """프로젝트 변경사항 감지"""
        changes_detected = []
        
        field_map = {
            'current_name': '상품명',
            'price': '가격', 
            'category': '카테고리',
            'store_name': '스토어명'
        }
        
        for field, display_name in field_map.items():
            old_value = getattr(project, field, '')
            new_value = new_info[field]
            
            # 가격은 정수로 비교
            if field == 'price':
                old_value = int(old_value) if old_value else 0
                new_value = int(new_value) if new_value else 0
            
            # 문자열 필드는 빈 값을 통일
            if isinstance(old_value, str):
                old_value = old_value.strip() if old_value else ''
            if isinstance(new_value, str):
                new_value = new_value.strip() if new_value else ''
            
            # 변경사항 감지
            if str(old_value) != str(new_value):
                # 변경사항 메시지용 정보 저장
                if field == 'price':
                    old_display = f"{int(old_value):,}원" if old_value else "0원"
                    new_display = f"{int(new_value):,}원" if new_value else "0원"
                else:
                    old_display = old_value if old_value else '-'
                    new_display = new_value if new_value else '-'
                
                changes_detected.append({
                    'field': display_name,
                    'field_name': field,
                    'old': old_display,
                    'new': new_display,
                    'old_value': str(old_value),
                    'new_value': str(new_value)
                })
                
                logger.info(f"변경사항 감지 - {display_name}: '{old_value}' → '{new_value}'")
        
        return changes_detected
    
    def process_single_keyword_ranking(self, keyword_obj, product_id: str) -> Tuple[Any, bool]:
        """단일 키워드 순위 확인 처리 (순수 비즈니스 로직)"""
        try:
            # 순위 확인
            result = self.check_keyword_ranking(keyword_obj.keyword, product_id)
            logger.info(f"순위 확인 결과: {keyword_obj.keyword} -> 순위: {result.rank}, 성공: {result.success}")
            return result, True
            
        except Exception as e:
            logger.error(f"키워드 {keyword_obj.keyword} 순위 확인 실패: {e}")
            failed_result = self.create_failed_ranking_result(keyword_obj.keyword, str(e))
            return failed_result, False
    
    def check_project_rankings_analysis(self, project, keywords: List) -> Dict[str, Any]:
        """프로젝트 전체 키워드 순위 확인 분석 (순수 계산)"""
        try:
            # 순위 확인 결과
            results = []
            success_count = 0
            
            for keyword_obj in keywords:
                result = self.check_keyword_ranking(keyword_obj.keyword, project.product_id)
                results.append(result)
                if result.success:
                    success_count += 1
            
            return {
                'success': success_count > 0,
                'message': f"순위 확인 완료: {success_count}/{len(keywords)} 키워드",
                'results': results,
                'success_count': success_count,
                'total_count': len(keywords)
            }
            
        except Exception as e:
            logger.error(f"프로젝트 순위 확인 분석 실패: {e}")
            return {
                'success': False,
                'message': f"순위 확인 중 오류 발생: {e}",
                'results': [],
                'success_count': 0,
                'total_count': len(keywords) if keywords else 0
            }
    
    def analyze_keywords_batch(self, keywords: List[str]) -> Dict[str, Any]:
        """키워드 배치 월검색량 분석 (순수 계산)"""
        try:
            updated_count = 0
            failed_count = 0
            results = []
            
            for keyword in keywords:
                try:
                    analysis = self.analyze_keyword_for_tracking(keyword)
                    
                    if analysis['success']:
                        updated_count += 1
                        results.append({
                            'keyword': keyword,
                            'success': True,
                            'category': analysis['category'],
                            'monthly_volume': analysis['monthly_volume']
                        })
                    else:
                        failed_count += 1
                        results.append({
                            'keyword': keyword,
                            'success': False,
                            'error_message': analysis.get('error_message', '분석 실패')
                        })
                        
                except Exception as e:
                    failed_count += 1
                    results.append({
                        'keyword': keyword,
                        'success': False,
                        'error_message': str(e)
                    })
                    logger.error(f"키워드 '{keyword}' 처리 실패: {e}")
            
            return {
                'success': updated_count > 0,
                'updated_count': updated_count,
                'failed_count': failed_count,
                'total_count': len(keywords),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"키워드 배치 분석 실패: {e}")
            return {
                'success': False,
                'updated_count': 0,
                'failed_count': len(keywords),
                'total_count': len(keywords),
                'results': [],
                'error_message': str(e)
            }


    # batch_update_keywords_volume은 analyze_keywords_batch와 동일하므로 제거됨
    # analyze_keywords_batch를 사용하세요
    
    def analyze_and_add_keyword(self, keyword: str) -> Dict[str, Any]:
        """키워드 분석 및 추가 로직 (순수 계산)"""
        try:
            # 키워드 분석 수행
            analysis = self.analyze_keyword_for_tracking(keyword)
            
            if analysis['success']:
                return {
                    'success': True,
                    'keyword': keyword,
                    'category': analysis['category'],
                    'monthly_volume': analysis['monthly_volume'],
                    'ready_for_db': True
                }
            else:
                return {
                    'success': False,
                    'keyword': keyword,
                    'category': '-',
                    'monthly_volume': 0,
                    'error_message': analysis.get('error_message', '분석 실패'),
                    'ready_for_db': False
                }
                
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 분석/추가 로직 실패: {e}")
            return {
                'success': False,
                'keyword': keyword,
                'category': '-',
                'monthly_volume': 0,
                'error_message': str(e),
                'ready_for_db': False
            }
    
    def generate_keywords_from_product(self, product_name: str) -> List[str]:
        """상품명에서 키워드 생성 (순수 계산 로직)"""
        import re
        
        try:
            # 공백으로 분리
            words = product_name.strip().split()
            
            # 숫자+단위 필터링 (15g, 500ml, 2kg 등)
            unit_pattern = r'^\d+[a-zA-Z가-힣]*$'
            filtered_words = []
            
            for word in words:
                # 숫자+단위 패턴 제거
                if not re.match(unit_pattern, word):
                    # 특수문자 제거하고 한글/영문만 남기기
                    clean_word = re.sub(r'[^\w가-힣]', '', word)
                    if len(clean_word) > 1:  # 1글자는 제외
                        filtered_words.append(clean_word)
            
            # 중복 제거
            unique_words = list(dict.fromkeys(filtered_words))
            
            keywords = []
            
            # 1. 전체 상품명 (첫 번째)
            keywords.append(product_name.strip())
            
            # 2. 단일 키워드들 (순서대로)
            keywords.extend(unique_words[:3])  # 처음 3개만
            
            # 3. 2단어 조합
            if len(unique_words) >= 2:
                # 1+2, 1+3, 2+3 조합
                combinations = [
                    f"{unique_words[0]} {unique_words[1]}",  # 1+2
                ]
                if len(unique_words) >= 3:
                    combinations.extend([
                        f"{unique_words[0]} {unique_words[2]}",  # 1+3
                        f"{unique_words[1]} {unique_words[2]}",  # 2+3
                    ])
                keywords.extend(combinations)
            
            return keywords
            
        except Exception as e:
            logger.error(f"상품명에서 키워드 생성 실패: {product_name}: {e}")
            return [product_name.strip()]  # 최소한 원본 상품명은 반환
    
    def calculate_keyword_batch_results(self, keywords: List[str], existing_keywords: set) -> Dict[str, Any]:
        """키워드 배치 추가 결과 계산 (순수 로직)"""
        try:
            new_keywords = []
            duplicate_keywords = []
            
            # 중복 체크
            for keyword in keywords:
                keyword = keyword.strip()
                if keyword.lower() in existing_keywords:
                    duplicate_keywords.append(keyword)
                else:
                    new_keywords.append(keyword)
            
            return {
                'new_keywords': new_keywords,
                'duplicate_keywords': duplicate_keywords,
                'total_keywords': len(keywords),
                'new_count': len(new_keywords),
                'duplicate_count': len(duplicate_keywords)
            }
            
        except Exception as e:
            logger.error(f"키워드 배치 결과 계산 실패: {e}")
            return {
                'new_keywords': [],
                'duplicate_keywords': [],
                'total_keywords': 0,
                'new_count': 0,
                'duplicate_count': 0,
                'error_message': str(e)
            }
    
    def process_keyword_info_analysis(self, keyword: str) -> Dict[str, Any]:
        """키워드 정보 분석 처리 (순수 분석 로직)"""
        try:
            # 카테고리와 월검색량 조회
            category = self.get_keyword_category_from_vendor(keyword)
            monthly_volume = self.get_keyword_volume_from_vendor(keyword)
            
            return {
                'success': True,
                'category': category,
                'monthly_volume': monthly_volume,
                'keyword': keyword
            }
            
        except Exception as e:
            logger.error(f"키워드 정보 분석 실패: {keyword}: {e}")
            return {
                'success': False,
                'category': '-',
                'monthly_volume': -1,
                'keyword': keyword,
                'error_message': str(e)
            }
    
    def analyze_and_add_keyword_logic(self, keyword: str) -> Dict[str, Any]:
        """키워드 분석 후 추가를 위한 순수 로직"""
        try:
            # 키워드 분석
            analysis = self.analyze_keyword_for_tracking(keyword)
            
            if analysis['success']:
                return {
                    'success': True,
                    'keyword': keyword,
                    'category': analysis.get('category', ''),
                    'monthly_volume': analysis.get('monthly_volume', -1),
                    'ready_for_db': True
                }
            else:
                return {
                    'success': False,
                    'keyword': keyword,
                    'error_message': analysis.get('error_message', '분석 실패'),
                    'ready_for_db': False
                }
                
        except Exception as e:
            logger.error(f"키워드 분석/추가 로직 실패: {e}")
            return {
                'success': False,
                'keyword': keyword,
                'error_message': str(e),
                'ready_for_db': False
            }
    
    def get_product_category_analysis(self, product_id: str) -> Dict[str, Any]:
        """상품 카테고리 조회 분석 (순수 로직)"""
        try:
            # smart_product_search를 통해 상품 정보 조회
            product_info = smart_product_search(f"상품ID_{product_id}", product_id)
            if product_info and 'category' in product_info:
                return {
                    'success': True,
                    'category': product_info['category'],
                    'product_id': product_id
                }
            
            return {
                'success': False,
                'category': '',
                'product_id': product_id,
                'error_message': '상품 정보 조회 실패'
            }
            
        except Exception as e:
            logger.error(f"상품 카테고리 분석 실패: {e}")
            return {
                'success': False,
                'category': '',
                'product_id': product_id,
                'error_message': str(e)
            }
    
    def prepare_table_data_analysis(self, project, keywords, overview) -> Dict[str, Any]:
        """테이블 데이터 준비를 위한 분석 로직 (순수 계산)"""
        try:
            from .adapters import format_date, format_date_with_time
            
            # 날짜 목록 추출 및 정렬
            dates = overview.get("dates", [])
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
            logger.error(f"테이블 데이터 분석 실패: {e}")
            return {"success": False, "message": f"오류 발생: {e}"}
    
    def prepare_table_row_data_analysis(self, keyword_data: dict, all_dates: list, current_rankings: dict, current_time: str) -> list:
        """테이블 행 데이터 준비 분석 (순수 계산)"""
        try:
            from .adapters import format_monthly_volume, format_rank_display
            
            keyword = keyword_data['keyword']
            rankings = keyword_data.get('rankings', {})
            
            # 기본 행 데이터 (체크박스 제외)
            row_data = [keyword]  # 키워드
            
            # 카테고리 추가
            category = keyword_data.get('category', '') or '-'
            row_data.append(category)
            
            # 월검색량
            search_vol = keyword_data.get('search_volume')
            monthly_vol = keyword_data.get('monthly_volume', -1)
            volume = search_vol or monthly_vol
            
            # 월검색량 포맷팅
            if volume == -1:
                volume_text = "-"  # 아직 API 호출 안됨
            else:
                volume_text = format_monthly_volume(volume)
            row_data.append(volume_text)
            
            # 날짜별 순위 추가
            for date in all_dates:
                # 진행 중인 날짜인 경우 임시 저장된 순위 데이터 확인
                if date == current_time:
                    keyword_id = keyword_data.get('id')
                    if keyword_id and keyword_id in current_rankings:
                        rank = current_rankings[keyword_id]
                        rank_display = format_rank_display(rank)
                        row_data.append(rank_display)
                    else:
                        row_data.append("-")
                else:
                    # 저장된 순위 데이터 확인
                    rank_data = rankings.get(date)
                    if rank_data and rank_data.get('rank') is not None:
                        rank_display = format_rank_display(rank_data['rank'])
                        row_data.append(rank_display)
                    else:
                        row_data.append("-")
            
            return row_data
            
        except Exception as e:
            logger.error(f"테이블 행 데이터 분석 실패: {e}")
            return [keyword_data.get('keyword', ''), '-', '-'] + ['-'] * len(all_dates)
    
    def analyze_keywords_for_deletion(self, keyword_ids: List[int], keyword_names: List[str]) -> Dict[str, Any]:
        """키워드 삭제 분석 (순수 로직)"""
        try:
            if not keyword_ids:
                return {
                    'success': False,
                    'message': "삭제할 키워드가 선택되지 않았습니다.",
                    'deletable_count': 0
                }
            
            return {
                'success': True,
                'message': f"{len(keyword_ids)}개 키워드 삭제 준비 완료",
                'deletable_count': len(keyword_ids),
                'keyword_ids': keyword_ids,
                'keyword_names': keyword_names
            }
            
        except Exception as e:
            logger.error(f"키워드 삭제 분석 실패: {e}")
            return {
                'success': False,
                'message': f"키워드 삭제 분석 중 오류: {str(e)}",
                'deletable_count': 0
            }


# 전역 엔진 인스턴스
rank_tracking_engine = RankTrackingEngine()