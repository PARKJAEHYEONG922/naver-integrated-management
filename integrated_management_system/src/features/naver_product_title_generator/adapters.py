"""
네이버 상품명 생성기 어댑터
벤더 API 호출 및 데이터 정규화, 엑셀 저장 담당 (keyword_analysis 스타일)
"""
from typing import List, Dict, Any, Optional, Callable
import re
from collections import Counter

from src.foundation.logging import get_logger
from src.foundation.http_client import api_error_handler, ParallelAPIProcessor, rate_limiter_manager
from .models import KeywordBasicData

logger = get_logger("features.naver_product_title_generator.adapters")


def parse_keywords(text: str) -> List[str]:
    """
    입력 텍스트에서 키워드 추출 (엔터 또는 쉼표로 구분)
    
    Args:
        text: 입력 텍스트
        
    Returns:
        List[str]: 정리된 키워드 리스트
    """
    if not text or not text.strip():
        return []
    
    # 쉼표와 엔터로 구분
    keywords = re.split(r'[,\n]+', text.strip())
    
    # 빈 문자열 제거하고 공백 정리
    cleaned_keywords = []
    for keyword in keywords:
        cleaned = keyword.strip()
        if cleaned:  # 빈 문자열이 아닌 경우만 추가
            cleaned_keywords.append(cleaned)
    
    # 중복 제거 (순서 유지)
    unique_keywords = []
    seen = set()
    for keyword in cleaned_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower not in seen:
            seen.add(keyword_lower)
            unique_keywords.append(keyword)
    
    logger.debug(f"키워드 파싱 완료: {len(unique_keywords)}개 키워드")
    return unique_keywords


@api_error_handler("네이버 검색광고 API")
def get_keyword_search_volume(keyword: str) -> int:
    """
    네이버 검색광고 API로 키워드 월검색량 조회 (Raw 방식)
    
    Args:
        keyword: 조회할 키워드
        
    Returns:
        int: 월검색량 (PC + 모바일 합계), 조회 실패시 0
    """
    try:
        from src.vendors.naver.client_factory import NaverClientFactory
        from .engine_local import normalize_keyword_for_api
        
        # API 호출용 키워드 정규화 (공백/특수문자 제거)
        normalized_keyword = normalize_keyword_for_api(keyword)
        
        logger.debug(f"월검색량 조회 시작: '{keyword}' → '{normalized_keyword}'")
        
        # 검색광고 API 클라이언트
        keyword_client = NaverClientFactory.get_keyword_tool_client()
        searchad_response = keyword_client.get_keyword_ideas([normalized_keyword])
        
        if not searchad_response or 'keywordList' not in searchad_response:
            logger.warning(f"검색광고 API 응답이 비어있음: '{keyword}'")
            return 0
        
        # 정확히 일치하는 키워드 찾기 (정규화된 키워드로 비교)
        for kw_item in searchad_response['keywordList']:
            if kw_item.get('relKeyword', '').upper() == normalized_keyword.upper():
                pc_count = kw_item.get('monthlyPcQcCnt', 0)
                mobile_count = kw_item.get('monthlyMobileQcCnt', 0)
                
                # "< 10" 처리
                if pc_count == '< 10':
                    pc_count = 0
                elif isinstance(pc_count, str):
                    pc_count = int(pc_count) if pc_count.isdigit() else 0
                
                if mobile_count == '< 10':
                    mobile_count = 0
                elif isinstance(mobile_count, str):
                    mobile_count = int(mobile_count) if mobile_count.isdigit() else 0
                
                total_volume = int(pc_count) + int(mobile_count)
                logger.debug(f"월검색량 조회 완료: '{keyword}' -> {total_volume} (PC: {pc_count}, Mobile: {mobile_count})")
                return total_volume
        
        logger.warning(f"키워드 '{keyword}'에 대한 검색량 정보를 찾을 수 없음")
        return 0
        
    except Exception as e:
        logger.error(f"월검색량 조회 실패 '{keyword}': {e}")
        return 0


@api_error_handler("네이버 쇼핑 API")
def get_keyword_category(keyword: str) -> str:
    """
    네이버 개발자 쇼핑 API로 키워드 카테고리 조회 (Raw 방식)
    
    Args:
        keyword: 조회할 키워드
        
    Returns:
        str: 카테고리 경로 (예: "패션의류 > 여성의류 > 원피스"), 조회 실패시 빈 문자열
    """
    try:
        from src.vendors.naver.client_factory import NaverClientFactory
        from .engine_local import normalize_keyword_for_api
        
        # API 호출용 키워드 정규화 (공백/특수문자 제거)
        normalized_keyword = normalize_keyword_for_api(keyword)
        
        logger.debug(f"카테고리 조회 시작: '{keyword}' → '{normalized_keyword}'")
        
        # 쇼핑 API 클라이언트
        shopping_client = NaverClientFactory.get_shopping_client()
        shopping_response = shopping_client.search_products(query=normalized_keyword, display=20, sort="sim")
        
        # 응답 구조 로그 (디버깅용)
        logger.debug(f"쇼핑 API 응답 구조 확인: '{keyword}' -> {type(shopping_response)}")
        
        # NaverShoppingResponse 객체 처리
        if hasattr(shopping_response, 'items'):
            items = shopping_response.items
            if not items:
                logger.warning(f"쇼핑 API 응답에 items가 비어있음: '{keyword}'")
                return ""
        # 딕셔너리 응답 처리 (혹시 raw 응답인 경우)
        elif isinstance(shopping_response, dict) and 'items' in shopping_response:
            items = shopping_response['items']
            if not items:
                logger.warning(f"쇼핑 API 응답에 items가 비어있음: '{keyword}'")
                return ""
        else:
            logger.warning(f"쇼핑 API 응답 형태를 인식할 수 없음: '{keyword}' -> {type(shopping_response)}")
            return ""
        
        logger.debug(f"쇼핑 API 응답: '{keyword}' -> {len(items)}개 상품 발견")
        
        # 모든 상품(1~40위)의 카테고리 수집
        all_categories = []
        
        for idx, item in enumerate(items):
            try:
                category_path = None
                
                # NaverShoppingItem 객체인 경우
                if hasattr(item, 'category1'):
                    categories = []
                    for i in range(1, 10):  # category1~9까지 확인
                        cat_attr = f'category{i}'
                        if hasattr(item, cat_attr):
                            cat_value = getattr(item, cat_attr)
                            if cat_value and cat_value.strip():  # 빈 문자열이 아닌 경우만
                                categories.append(cat_value.strip())
                    
                    if categories:
                        category_path = " > ".join(categories)
                
                # 딕셔너리인 경우
                elif isinstance(item, dict):
                    categories = []
                    for i in range(1, 10):  # category1~9까지 확인
                        cat_key = f'category{i}'
                        if cat_key in item and item[cat_key] and item[cat_key].strip():
                            categories.append(item[cat_key].strip())
                    
                    if categories:
                        category_path = " > ".join(categories)
                    
                    # 디버깅용: 첫 번째 상품의 모든 필드 출력
                    if idx == 0:
                        logger.debug(f"첫 번째 상품 필드들: {list(item.keys())}")
                        category_fields = [k for k in item.keys() if 'category' in k.lower()]
                        logger.debug(f"카테고리 관련 필드들: {category_fields}")
                        for field in category_fields:
                            logger.debug(f"{field}: {item[field]}")
                
                # 카테고리 경로가 있으면 리스트에 추가
                if category_path:
                    all_categories.append(category_path)
                    logger.debug(f"상품{idx+1}: {category_path}")
                
            except Exception as e:
                logger.warning(f"상품 {idx+1}의 카테고리 처리 중 오류: {e}")
                continue
        
        # 카테고리가 수집되지 않은 경우
        if not all_categories:
            logger.warning(f"키워드 '{keyword}'에 대한 카테고리 정보를 찾을 수 없음. items 개수: {len(items)}")
            return ""
        
        # 가장 많이 나타나는 카테고리 찾기
        from collections import Counter
        category_counter = Counter(all_categories)
        most_common_category, count = category_counter.most_common(1)[0]
        
        # 퍼센테이지 계산
        total_products = len(all_categories)
        percentage = int((count / total_products) * 100)
        
        # 결과 포맷: "카테고리 경로 (퍼센테이지%)"
        result = f"{most_common_category} ({percentage}%)"
        
        logger.info(f"카테고리 분석 완료: '{keyword}' -> '{result}' ({count}/{total_products}개 상품)")
        return result
        
    except Exception as e:
        logger.error(f"카테고리 조회 실패 '{keyword}': {e}")
        return "조회 실패"


def analyze_keyword_full_info(keyword: str) -> KeywordBasicData:
    """
    키워드의 월검색량과 카테고리를 모두 조회해서 KeywordBasicData 반환
    
    Args:
        keyword: 분석할 키워드
        
    Returns:
        KeywordBasicData: 키워드, 월검색량, 카테고리 정보
    """
    try:
        logger.info(f"키워드 전체 분석 시작: '{keyword}'")
        
        # 1. 월검색량 조회
        search_volume = get_keyword_search_volume(keyword)
        
        # 2. 카테고리 조회  
        category = get_keyword_category(keyword)
        
        # KeywordBasicData 생성
        keyword_data = KeywordBasicData(
            keyword=keyword,
            search_volume=search_volume,
            category=category or "카테고리 없음"
        )
        
        logger.info(f"키워드 전체 분석 완료: '{keyword}' (검색량: {search_volume}, 카테고리: {category or '없음'})")
        return keyword_data
        
    except Exception as e:
        logger.error(f"키워드 전체 분석 실패 '{keyword}': {e}")
        return KeywordBasicData(
            keyword=keyword,
            search_volume=0,
            category="분석 실패"
        )


def get_keywords_search_volume(keywords: List[str], 
                              max_workers: int = 3,
                              stop_check: Optional[Callable[[], bool]] = None,
                              progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[KeywordBasicData]:
    """
    키워드들의 월검색량을 병렬로 조회 (adapters 역할: 벤더 호출 + 정규화)
    
    Args:
        keywords: 분석할 키워드 리스트
        max_workers: 최대 동시 작업 수 (기본 3개)
        stop_check: 중단 확인 함수
        progress_callback: 진행률 콜백
        
    Returns:
        List[KeywordBasicData]: 월검색량만 포함된 정규화된 데이터 리스트
    """
    if not keywords:
        return []
    
    # 단일 키워드인 경우 병렬 처리 없이 직접 호출
    if len(keywords) == 1:
        try:
            search_volume = get_keyword_search_volume(keywords[0])
            return [KeywordBasicData(keyword=keywords[0], search_volume=search_volume, category="")]
        except Exception as e:
            logger.error(f"키워드 월검색량 조회 실패 '{keywords[0]}': {e}")
            return [KeywordBasicData(keyword=keywords[0], search_volume=0, category="")]
    
    # 여러 키워드는 병렬 처리
    try:
        logger.info(f"🔄 병렬 월검색량 조회 시작: {len(keywords)}개 키워드, {max_workers}개 워커")
        
        # 레이트 리미터 설정
        api_limiter = rate_limiter_manager.get_limiter("naver_volume_api", calls_per_second=1.0)
        
        # 병렬 처리기 생성
        processor = ParallelAPIProcessor(max_workers=max_workers, rate_limiter=api_limiter)
        
        # 단일 키워드 처리 함수 정의
        def process_single_keyword(keyword: str) -> KeywordBasicData:
            try:
                search_volume = get_keyword_search_volume(keyword)
                return KeywordBasicData(keyword=keyword, search_volume=search_volume, category="")
            except Exception as e:
                logger.error(f"키워드 월검색량 조회 실패 '{keyword}': {e}")
                return KeywordBasicData(keyword=keyword, search_volume=0, category="")
        
        # 진행률 콜백 래퍼 (키워드명 포함)
        def detailed_progress_callback(current: int, total: int, message: str):
            if progress_callback:
                # 현재 처리 중인 키워드 표시
                if current <= len(keywords):
                    current_keyword = keywords[current-1] if current > 0 else ""
                    detailed_message = f"월검색량 조회 중... ({current}/{total}) '{current_keyword}'"
                    progress_callback(current, total, detailed_message)
                else:
                    progress_callback(current, total, message)
        
        # 배치 처리 실행
        results = processor.process_batch(
            func=process_single_keyword,
            items=keywords,
            stop_check=stop_check,
            progress_callback=detailed_progress_callback
        )
        
        # 결과 정리
        keyword_data_list = []
        failed_count = 0
        
        for keyword, result, error in results:
            if error is None and result is not None:
                keyword_data_list.append(result)
            else:
                failed_count += 1
                keyword_data_list.append(KeywordBasicData(keyword=keyword, search_volume=0, category=""))
        
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count}개 키워드 월검색량 조회 실패")
        
        logger.info(f"✅ 병렬 월검색량 조회 완료: 성공 {len(keyword_data_list)-failed_count}개, 실패 {failed_count}개")
        return keyword_data_list
        
    except Exception as e:
        logger.error(f"병렬 월검색량 조회 실패: {e}")
        return [KeywordBasicData(keyword=kw, search_volume=0, category="") for kw in keywords]


def get_keywords_category(keyword_data_list: List[KeywordBasicData], 
                         max_workers: int = 3,
                         stop_check: Optional[Callable[[], bool]] = None,
                         progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[KeywordBasicData]:
    """
    키워드들의 카테고리를 병렬로 조회하여 업데이트 (adapters 역할: 벤더 호출 + 정규화)
    
    Args:
        keyword_data_list: 카테고리를 조회할 키워드 데이터 리스트
        max_workers: 최대 동시 작업 수 (기본 3개)
        stop_check: 중단 확인 함수
        progress_callback: 진행률 콜백
        
    Returns:
        List[KeywordBasicData]: 카테고리가 업데이트된 정규화된 데이터 리스트
    """
    if not keyword_data_list:
        return []
    
    # 단일 키워드인 경우 병렬 처리 없이 직접 호출
    if len(keyword_data_list) == 1:
        kd = keyword_data_list[0]
        try:
            category = get_keyword_category(kd.keyword)
            return [KeywordBasicData(keyword=kd.keyword, search_volume=kd.search_volume, category=category or "카테고리 없음")]
        except Exception as e:
            logger.error(f"키워드 카테고리 조회 실패 '{kd.keyword}': {e}")
            return [KeywordBasicData(keyword=kd.keyword, search_volume=kd.search_volume, category="조회 실패")]
    
    # 여러 키워드는 병렬 처리
    try:
        logger.info(f"🔄 병렬 카테고리 조회 시작: {len(keyword_data_list)}개 키워드, {max_workers}개 워커")
        
        # 레이트 리미터 설정 (카테고리 조회도 동일한 속도)
        api_limiter = rate_limiter_manager.get_limiter("naver_category_api", calls_per_second=1.0)
        
        # 병렬 처리기 생성
        processor = ParallelAPIProcessor(max_workers=max_workers, rate_limiter=api_limiter)
        
        # 키워드만 추출
        keywords = [kd.keyword for kd in keyword_data_list]
        
        # 단일 카테고리 처리 함수 정의
        def process_single_category(keyword: str) -> str:
            try:
                category = get_keyword_category(keyword)
                return category or "카테고리 없음"
            except Exception as e:
                logger.error(f"키워드 카테고리 조회 실패 '{keyword}': {e}")
                return "조회 실패"
        
        # 진행률 콜백 래퍼 (키워드명 포함)
        def detailed_progress_callback(current: int, total: int, message: str):
            if progress_callback:
                # 현재 처리 중인 키워드 표시
                if current <= len(keywords):
                    current_keyword = keywords[current-1] if current > 0 else ""
                    detailed_message = f"카테고리 조회 중... ({current}/{total}) '{current_keyword}'"
                    progress_callback(current, total, detailed_message)
                else:
                    progress_callback(current, total, message)
        
        # 배치 처리 실행
        results = processor.process_batch(
            func=process_single_category,
            items=keywords,
            stop_check=stop_check,
            progress_callback=detailed_progress_callback
        )
        
        # 결과 병합 (원래 KeywordBasicData에 카테고리 정보 업데이트)
        updated_keyword_data = []
        failed_count = 0
        
        for i, (keyword, category_result, error) in enumerate(results):
            original_data = keyword_data_list[i]
            
            if error is None and category_result is not None:
                updated_data = KeywordBasicData(
                    keyword=original_data.keyword,
                    search_volume=original_data.search_volume,
                    category=category_result
                )
            else:
                failed_count += 1
                updated_data = KeywordBasicData(
                    keyword=original_data.keyword,
                    search_volume=original_data.search_volume,
                    category="카테고리 조회 실패"
                )
            
            updated_keyword_data.append(updated_data)
        
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count}개 키워드 카테고리 조회 실패")
        
        logger.info(f"✅ 병렬 카테고리 조회 완료: 성공 {len(updated_keyword_data)-failed_count}개, 실패 {failed_count}개")
        return updated_keyword_data
        
    except Exception as e:
        logger.error(f"병렬 카테고리 조회 실패: {e}")
        # 실패 시 원래 데이터를 그대로 반환 (카테고리만 실패 표시)
        return [KeywordBasicData(
            keyword=kd.keyword,
            search_volume=kd.search_volume,
            category="카테고리 조회 실패"
        ) for kd in keyword_data_list]


def analyze_keywords_parallel(keywords: List[str], 
                            max_workers: int = 3,
                            stop_check: Optional[Callable[[], bool]] = None,
                            progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[KeywordBasicData]:
    """
    키워드들을 병렬로 분석 (월검색량 + 카테고리)
    
    Args:
        keywords: 분석할 키워드 리스트
        max_workers: 최대 동시 작업 수 (기본 3개)
        stop_check: 중단 확인 함수
        progress_callback: 진행률 콜백
        
    Returns:
        List[KeywordBasicData]: 분석된 키워드 데이터 리스트
    """
    try:
        logger.info(f"🔄 병렬 키워드 분석 시작: {len(keywords)}개 키워드, {max_workers}개 워커")
        
        # 레이트 리미터 설정 (초당 1회 호출로 안전하게)
        api_limiter = rate_limiter_manager.get_limiter("naver_parallel_api", calls_per_second=1.0)
        
        # 병렬 처리기 생성
        processor = ParallelAPIProcessor(max_workers=max_workers, rate_limiter=api_limiter)
        
        # 진행률 콜백 래퍼 (키워드명 포함)
        def detailed_progress_callback(current: int, total: int, message: str):
            if progress_callback:
                # 현재 처리 중인 키워드 표시
                if current <= len(keywords):
                    current_keyword = keywords[current-1] if current > 0 else ""
                    detailed_message = f"키워드 분석 중... ({current}/{total}) '{current_keyword}'"
                    progress_callback(current, total, detailed_message)
                else:
                    progress_callback(current, total, message)
        
        # 배치 처리 실행
        results = processor.process_batch(
            func=analyze_keyword_full_info,
            items=keywords,
            stop_check=stop_check,
            progress_callback=detailed_progress_callback
        )
        
        # 결과 정리
        keyword_data_list = []
        failed_count = 0
        
        for keyword, result, error in results:
            if error is None and result is not None:
                keyword_data_list.append(result)
            else:
                # 실패한 키워드는 기본 데이터로 추가
                failed_count += 1
                logger.warning(f"키워드 '{keyword}' 분석 실패: {error}")
                keyword_data_list.append(KeywordBasicData(
                    keyword=keyword,
                    search_volume=0,
                    category="분석 실패"
                ))
        
        success_count = len(keyword_data_list) - failed_count
        logger.info(f"✅ 병렬 키워드 분석 완료: {success_count}/{len(keywords)} 성공")
        
        return keyword_data_list
        
    except Exception as e:
        logger.error(f"병렬 키워드 분석 실패: {e}")
        # 전체 실패 시 모든 키워드를 실패 데이터로 반환
        return [KeywordBasicData(
            keyword=keyword,
            search_volume=0,
            category="분석 실패"
        ) for keyword in keywords]


def analyze_keywords_batch(keywords: List[str], 
                         batch_size: int = 10,
                         max_workers: int = 3,
                         stop_check: Optional[Callable[[], bool]] = None,
                         progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[KeywordBasicData]:
    """
    키워드들을 배치별로 병렬 처리 (대용량 처리용)
    
    Args:
        keywords: 분석할 키워드 리스트
        batch_size: 배치 크기 (기본 10개)
        max_workers: 배치당 최대 동시 작업 수 (기본 3개)
        stop_check: 중단 확인 함수
        progress_callback: 진행률 콜백
        
    Returns:
        List[KeywordBasicData]: 분석된 키워드 데이터 리스트
    """
    try:
        total_keywords = len(keywords)
        logger.info(f"🔄 배치별 병렬 분석 시작: {total_keywords}개 키워드, 배치 크기 {batch_size}, 워커 {max_workers}개")
        
        all_results = []
        processed_count = 0
        
        # 키워드를 배치별로 나누어 처리
        for i in range(0, total_keywords, batch_size):
            if stop_check and stop_check():
                break
            
            batch_keywords = keywords[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_keywords + batch_size - 1) // batch_size
            
            logger.info(f"📦 배치 {batch_num}/{total_batches} 처리 중: {len(batch_keywords)}개 키워드")
            
            # 배치별 진행률 콜백 래핑
            def batch_progress_callback(current: int, total: int, message: str):
                global_current = processed_count + current
                if progress_callback:
                    progress_callback(global_current, total_keywords, f"배치 {batch_num}/{total_batches}: {message}")
            
            # 배치 처리
            batch_results = analyze_keywords_parallel(
                keywords=batch_keywords,
                max_workers=max_workers,
                stop_check=stop_check,
                progress_callback=batch_progress_callback
            )
            
            all_results.extend(batch_results)
            processed_count += len(batch_keywords)
        
        logger.info(f"✅ 배치별 병렬 분석 완료: {len(all_results)}개 키워드 처리됨")
        return all_results
        
    except Exception as e:
        logger.error(f"배치별 병렬 분석 실패: {e}")
        return [KeywordBasicData(
            keyword=keyword,
            search_volume=0,
            category="분석 실패"
        ) for keyword in keywords]


def extract_product_id_from_link(link: str) -> str:
    """상품 링크에서 productId 추출 (rank_tracking과 동일)"""
    if not link:
        return ""
    
    patterns = [
        r'https?://shopping\.naver\.com/catalog/(\d+)',
        r'https?://smartstore\.naver\.com/[^/]+/products/(\d+)',
        r'/catalog/(\d+)',
        r'/products/(\d+)',
        r'productId=(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    
    return ""


def extract_price(price_str: str) -> int:
    """가격 문자열에서 숫자만 추출"""
    if not price_str:
        return 0
    numbers = re.findall(r'\d+', str(price_str))
    if numbers:
        return int(''.join(numbers))
    return 0


def collect_product_names_for_keyword(keyword: str, max_count: int = 40) -> List[Dict[str, Any]]:
    """
    키워드로 상품명 수집 (1~40위)
    
    Args:
        keyword: 검색 키워드
        max_count: 최대 수집 개수
        
    Returns:
        List[Dict]: 상품명 정보 리스트
    """
    try:
        logger.debug(f"상품명 수집 시작: {keyword} (최대 {max_count}개)")
        
        from src.vendors.naver.client_factory import NaverClientFactory
        client = NaverClientFactory.get_shopping_client()
        if not client:
            logger.warning(f"쇼핑 클라이언트 없음: {keyword}")
            return []
        
        # 네이버 쇼핑 API로 검색
        response = client.search_products(
            query=keyword,
            display=min(max_count, 100),  # 최대 100개
            start=1,
            sort="sim"  # 정확도 순
        )
        
        if not response or not hasattr(response, 'items') or not response.items:
            logger.warning(f"검색 결과 없음: {keyword}")
            return []
        
        # 상품명 정보 추출
        product_names = []
        for idx, item in enumerate(response.items):
            if idx >= max_count:
                break
                
            # HTML 태그 제거
            clean_title = item.title.replace('<b>', '').replace('</b>', '') if hasattr(item, 'title') and item.title else ''
            if not clean_title:
                continue
                
            # 카테고리 경로 구성
            categories = []
            for cat_field in ['category1', 'category2', 'category3', 'category4']:
                if hasattr(item, cat_field):
                    category_value = getattr(item, cat_field)
                    if category_value and category_value.strip():
                        categories.append(category_value.strip())
                    else:
                        break
            
            category_path = ' > '.join(categories) if categories else ''
            
            product_names.append({
                'rank': idx + 1,
                'title': clean_title.strip(),
                'keyword': keyword,
                'price': extract_price(getattr(item, 'lprice', '')),
                'mall_name': getattr(item, 'mallName', ''),
                'category': category_path,
                'product_id': extract_product_id_from_link(getattr(item, 'link', '')),
                'image_url': getattr(item, 'image', ''),
                'link': getattr(item, 'link', '')
            })
        
        logger.debug(f"상품명 수집 완료: {keyword} - {len(product_names)}개")
        return product_names
        
    except Exception as e:
        logger.error(f"상품명 수집 실패: {keyword}: {e}")
        return []


def collect_product_names_for_keywords(keywords: List[str], max_count_per_keyword: int = 40) -> List[Dict[str, Any]]:
    """
    여러 키워드로 상품명 수집 및 중복 제거
    
    Args:
        keywords: 검색 키워드 리스트
        max_count_per_keyword: 키워드당 최대 수집 개수
        
    Returns:
        List[Dict]: 중복 제거된 상품명 정보 리스트
    """
    try:
        logger.info(f"상품명 일괄 수집 시작: {len(keywords)}개 키워드")
        
        all_products = []
        
        # 각 키워드별로 상품명 수집
        for keyword in keywords:
            products = collect_product_names_for_keyword(keyword, max_count_per_keyword)
            all_products.extend(products)
        
        logger.info(f"전체 수집 완료: {len(all_products)}개 (중복 제거 전)")
        
        # 중복 제거 (상품 제목 기준)
        unique_products = []
        seen_titles = set()
        
        for product in all_products:
            title = product['title'].strip().lower()
            if title not in seen_titles:
                seen_titles.add(title)
                unique_products.append(product)
        
        # 순위 재정렬 (키워드별 평균 순위 기준)
        title_ranks = {}
        title_keywords = {}
        
        for product in all_products:
            title = product['title'].strip().lower()
            rank = product['rank']
            keyword = product['keyword']
            
            if title not in title_ranks:
                title_ranks[title] = []
                title_keywords[title] = set()
            
            title_ranks[title].append(rank)
            title_keywords[title].add(keyword)
        
        # 평균 순위로 정렬
        for product in unique_products:
            title = product['title'].strip().lower()
            product['avg_rank'] = sum(title_ranks[title]) / len(title_ranks[title])
            product['keywords_found_in'] = list(title_keywords[title])
            product['keyword_count'] = len(title_keywords[title])
        
        # 평균 순위 순으로 정렬
        unique_products.sort(key=lambda x: x['avg_rank'])
        
        # 최종 순위 부여
        for idx, product in enumerate(unique_products):
            product['final_rank'] = idx + 1
        
        logger.info(f"중복 제거 완료: {len(unique_products)}개 (제거된 중복: {len(all_products) - len(unique_products)}개)")
        return unique_products
        
    except Exception as e:
        logger.error(f"상품명 일괄 수집 실패: {e}")
        return []


def get_keywords_category(keyword_data_list: List[KeywordBasicData],
                         max_workers: int = 2,
                         stop_check: Optional[Callable[[], bool]] = None,
                         progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[KeywordBasicData]:
    """
    키워드들의 카테고리를 병렬로 조회 (adapters 역할: 벤더 호출 + 정규화)
    
    Args:
        keyword_data_list: 월검색량이 포함된 KeywordBasicData 리스트
        max_workers: 최대 동시 작업 수 (기본 2개)
        stop_check: 중단 확인 함수
        progress_callback: 진행률 콜백
        
    Returns:
        List[KeywordBasicData]: 월검색량 + 카테고리가 포함된 정규화된 데이터 리스트
    """
    if not keyword_data_list:
        return []
    
    # 단일 키워드인 경우 병렬 처리 없이 직접 호출
    if len(keyword_data_list) == 1:
        try:
            keyword_data = keyword_data_list[0]
            category = get_keyword_category(keyword_data.keyword)
            return [KeywordBasicData(
                keyword=keyword_data.keyword,
                search_volume=keyword_data.search_volume,
                category=category
            )]
        except Exception as e:
            logger.error(f"키워드 카테고리 조회 실패 '{keyword_data_list[0].keyword}': {e}")
            return [KeywordBasicData(
                keyword=keyword_data_list[0].keyword,
                search_volume=keyword_data_list[0].search_volume,
                category="분석 실패"
            )]
    
    # 여러 키워드는 병렬 처리
    try:
        logger.info(f"🔄 병렬 카테고리 조회 시작: {len(keyword_data_list)}개 키워드, {max_workers}개 워커")
        
        # 레이트 리미터 설정 (카테고리 조회도 동일한 속도)
        api_limiter = rate_limiter_manager.get_limiter("naver_category_api", calls_per_second=1.0)
        
        # 병렬 처리기 생성
        processor = ParallelAPIProcessor(max_workers=max_workers, rate_limiter=api_limiter)
        
        # 단일 키워드 처리 함수 정의
        def process_single_keyword_category(keyword_data: KeywordBasicData) -> KeywordBasicData:
            try:
                category = get_keyword_category(keyword_data.keyword)
                return KeywordBasicData(
                    keyword=keyword_data.keyword,
                    search_volume=keyword_data.search_volume,
                    category=category
                )
            except Exception as e:
                logger.error(f"키워드 카테고리 조회 실패 '{keyword_data.keyword}': {e}")
                return KeywordBasicData(
                    keyword=keyword_data.keyword,
                    search_volume=keyword_data.search_volume,
                    category="분석 실패"
                )
        
        # 진행률 콜백 래퍼 (키워드명 포함)
        def wrapped_progress_callback(current: int, total: int, current_item: KeywordBasicData):
            if progress_callback:
                message = f"카테고리 조회 중 '{current_item.keyword}' ({current}/{total})"
                progress_callback(current, total, message)
        
        # 병렬 처리 실행
        batch_results = processor.process_batch(
            func=process_single_keyword_category,
            items=keyword_data_list,
            stop_check=stop_check,
            progress_callback=lambda current, total, msg: wrapped_progress_callback(current, total, keyword_data_list[current-1] if current > 0 and current <= len(keyword_data_list) else None)
        )
        
        # 결과 정리
        results = []
        for keyword_data, result, error in batch_results:
            if error is None and result is not None:
                results.append(result)
            else:
                # 실패한 경우 원본 데이터에 실패 표시
                results.append(KeywordBasicData(
                    keyword=keyword_data.keyword,
                    search_volume=keyword_data.search_volume,
                    category="카테고리 조회 실패"
                ))
        
        logger.info(f"✅ 병렬 카테고리 조회 완료: {len(results)}개 키워드")
        return results
        
    except Exception as e:
        logger.error(f"병렬 카테고리 조회 실패: {e}")
        # 실패시 원본 데이터에 빈 카테고리 추가해서 반환
        return [KeywordBasicData(
            keyword=kd.keyword,
            search_volume=kd.search_volume,
            category="조회 실패"
        ) for kd in keyword_data_list]