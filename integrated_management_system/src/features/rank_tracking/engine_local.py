"""
순위 추적 핵심 비즈니스 로직 엔진 (CLAUDE.md 구조)
계산 및 알고리즘 로직만 담당 - 향후 .pyd 컴파일 대상
DB 접근 없음, 순수 계산 로직만
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import re

from .models import TrackingProject, RankingResult, RANK_OUT_OF_RANGE


class RankTrackingEngine:
    """순위 추적 핵심 엔진 - 순수 계산 로직만 (.pyd 컴파일 대상)"""
    
    def __init__(self):
        pass  # 순수 계산만 담당 - 외부 의존성 없음
    
    # analyze_keyword_for_tracking 제거됨 - service 레이어에서 adapter 직접 호출
    
    # check_keyword_ranking 제거됨 - service 레이어에서 adapter 직접 호출
    
    def create_failed_ranking_result(self, keyword: str, error_message: str) -> RankingResult:
        """실패한 순위 결과 생성"""
        return RankingResult(
            keyword=keyword,
            success=False,
            rank=RANK_OUT_OF_RANGE,
            error_message=error_message
        )
    
    # process_keyword_info_update 제거됨 - service 레이어에서 adapter 직접 호출
    
    # get_keyword_category_from_vendor, get_keyword_volume_from_vendor 제거됨 - service 레이어에서 adapter 직접 호출
    
    # refresh_product_info_analysis 제거됨 - service 레이어에서 adapter 호출 후 detect_project_changes 호출
    
    def detect_project_changes(self, project: TrackingProject, new_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """프로젝트 변경사항 감지 (순수 계산 로직)"""
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
        
        return changes_detected
    
    # process_single_keyword_ranking 제거됨 - service 레이어에서 adapter 직접 호출
    
    # check_project_rankings_analysis 제거됨 - service 레이어에서 adapter 직접 호출
    
    # analyze_keywords_batch 제거됨 - service 레이어에서 adapter 직접 호출


    # batch_update_keywords_volume은 analyze_keywords_batch와 동일하므로 제거됨
    # analyze_keywords_batch를 사용하세요
    
    # analyze_and_add_keyword 제거됨 - service 레이어에서 adapter 직접 호출 (analyze_and_add_keyword_logic과 중복)
    
    def generate_keywords_from_product(self, product_name: str) -> List[str]:
        """상품명에서 키워드 생성 (순수 계산 로직)"""
        
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
            
        except Exception:
            return [product_name.strip()]  # 최소한 원본 상품명은 반환
    
    def calculate_keyword_batch_results(self, keywords: List[str], existing_keywords: set) -> Dict[str, Any]:
        """키워드 배치 추가 결과 계산 (순수 로직)"""
        try:
            new_keywords = []
            duplicate_keywords = []
            
            # 키워드 정규화 함수
            def norm(s: str) -> str:
                return re.sub(r'\s+', ' ', s).strip().casefold()
            
            normalized_existing = {norm(k) for k in existing_keywords}
            
            # 중복 체크
            for keyword in keywords:
                keyword = keyword.strip()
                if norm(keyword) in normalized_existing:
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
            
        except Exception:
            return {
                'new_keywords': [],
                'duplicate_keywords': [],
                'total_keywords': 0,
                'new_count': 0,
                'duplicate_count': 0
            }
    
    # process_keyword_info_analysis 제거됨 - service 레이어에서 adapter 직접 호출 (process_keyword_info_update와 중복)
    
    # analyze_and_add_keyword_logic 제거됨 - service 레이어에서 adapter 직접 호출 (analyze_and_add_keyword와 중복)
    
    # get_product_category_analysis 제거됨 - service 레이어에서 adapter 직접 호출
    
    def prepare_table_data_analysis(self, project, keywords, overview) -> Dict[str, Any]:
        """테이블 데이터 준비를 위한 분석 로직 (순수 계산)"""
        try:
            # 포맷터 함수들을 service에서 전달받거나 여기서 직접 구현
            def format_date(date_str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return dt.strftime("%m/%d %H:%M")
                except:
                    return date_str
            
            def format_date_with_time(date_str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return dt.strftime("%Y-%m-%d %H:%M")
                except:
                    return date_str
            
            # 날짜 목록 추출 및 정렬
            dates = overview.get("dates", [])
            # 날짜 파싱 및 정렬
            parsed_dates = []
            unparsed_dates = []
            for date in dates:
                try:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    parsed_dates.append((date, dt))
                except:
                    unparsed_dates.append(date)
            
            # 파싱된 날짜는 시간 내림차순 정렬, 실패한 것은 뒤에 추가
            parsed_dates.sort(key=lambda x: x[1], reverse=True)
            sorted_dates = [date for date, _ in parsed_dates] + unparsed_dates
            all_dates = sorted_dates[:10]  # 최대 10개
            
            # 헤더 구성
            headers = ["", "키워드", "카테고리", "월검색량"]
            for date in all_dates:
                headers.append(format_date(date))
            
            # 마지막 확인 시간 (시간만 반환, UI에서 "마지막 확인:" 텍스트 추가)
            last_check_time = ""
            if dates:
                last_check_time = format_date_with_time(dates[0])
            else:
                last_check_time = "-"
            
            # 프로젝트 카테고리 전체 (색상 매칭용) - 전체 경로 보존
            project_category_base = ""
            if hasattr(project, 'category') and project.category:
                project_category_base = project.category
            
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
            
        except Exception:
            return {"success": False, "message": "테이블 데이터 분석 실패"}
    
    def prepare_table_row_data_analysis(self, keyword_data: dict, all_dates: list, current_rankings: dict, current_time: str) -> list:
        """테이블 행 데이터 준비 분석 (순수 계산)"""
        try:
            # 순수 계산 로직 - 외부 import 없이 직접 구현
            def format_monthly_volume_local(vol):
                if vol is None:
                    return "-"
                if vol < 0:
                    return "-"
                if vol == 0:
                    return "0"
                return f"{vol:,}"
            
            def format_rank_display_local(rank):
                if not isinstance(rank, int):
                    return "-"
                if rank == RANK_OUT_OF_RANGE or rank > 200:
                    return "200위밖"
                elif rank >= 1:
                    return f"{rank}위"
                return "-"
            
            keyword = keyword_data['keyword']
            rankings = keyword_data.get('rankings', {})
            
            # 기본 행 데이터 (체크박스 제외)
            row_data = [keyword]  # 키워드
            
            # 카테고리 추가 (표시용으로는 마지막 부분만)
            category_full = keyword_data.get('category', '') or '-'
            if category_full and category_full != '-':
                # 괄호 앞 부분에서 마지막 세그먼트만 추출
                category_clean = category_full.split('(')[0].strip()
                if ' > ' in category_clean:
                    category_display = category_clean.split(' > ')[-1]
                    # 비율 정보가 있으면 마지막에 추가
                    if '(' in category_full:
                        percentage_part = category_full.split('(')[-1]
                        category_display = f"{category_display}({percentage_part}"
                else:
                    category_display = category_full
            else:
                category_display = '-'
            row_data.append(category_display)
            
            # 월검색량
            search_vol = keyword_data.get('search_volume')
            monthly_vol = keyword_data.get('monthly_volume', -1)
            volume = search_vol if search_vol is not None else monthly_vol
            
            # 월검색량 포맷팅
            volume_text = format_monthly_volume_local(volume)
            row_data.append(volume_text)
            
            # 날짜별 순위 추가
            for date in all_dates:
                # 진행 중인 날짜인 경우 임시 저장된 순위 데이터 확인
                if date == current_time:
                    keyword_id = keyword_data.get('id')
                    if keyword_id and keyword_id in current_rankings:
                        rank = current_rankings[keyword_id]
                        rank_display = format_rank_display_local(rank)
                        row_data.append(rank_display)
                    else:
                        row_data.append("-")
                else:
                    # 저장된 순위 데이터 확인
                    rank_data = rankings.get(date)
                    if rank_data is not None:
                        # rank_data가 숫자인 경우 (기존 방식)
                        if isinstance(rank_data, (int, float)):
                            rank_display = format_rank_display_local(rank_data)
                        # rank_data가 딕셔너리인 경우 (새로운 방식)
                        elif isinstance(rank_data, dict) and rank_data.get('rank') is not None:
                            rank_display = format_rank_display_local(rank_data['rank'])
                        else:
                            rank_display = "-"
                        row_data.append(rank_display)
                    else:
                        row_data.append("-")
            
            return row_data
            
        except Exception:
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
            
        except Exception:
            return {
                'success': False,
                'message': "키워드 삭제 분석 실패",
                'deletable_count': 0
            }


# 전역 엔진 인스턴스
rank_tracking_engine = RankTrackingEngine()