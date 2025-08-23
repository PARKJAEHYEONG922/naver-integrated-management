"""
네이버 상품명 생성기 어댑터
벤더 API 호출 및 데이터 정규화, 엑셀 저장 담당 (keyword_analysis 스타일)
"""
from typing import List, Dict, Any, Optional
import re
from collections import Counter

from src.foundation.logging import get_logger
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


def fetch_searchad_raw(keyword: str) -> Optional[Dict[str, Any]]:
    """검색광고 API Raw 데이터 수집 (keyword_analysis와 동일)"""
    try:
        from src.vendors.naver.client_factory import get_keyword_client
        client = get_keyword_client()
        if client:
            # vendors/naver/searchad/keyword_client.py 표준
            return client.get_keyword_ideas([keyword])
        return None
    except Exception as e:
        logger.warning(f"검색광고 데이터 수집 실패 - {keyword}: {e}")
        return None


def fetch_shopping_normalized(keyword: str) -> Optional[Dict[str, Any]]:
    """쇼핑 API 정규화 데이터 수집 (keyword_analysis와 동일)"""
    try:
        from src.vendors.naver.client_factory import get_shopping_client
        client = get_shopping_client()
        if client:
            # vendors/naver/developer/shopping_client.py 표준
            raw = client.search_products(query=keyword, display=40, sort="sim")
            from src.vendors.naver.normalizers import normalize_shopping_response
            return normalize_shopping_response(raw)
        return None
    except Exception as e:
        logger.warning(f"쇼핑 데이터 수집 실패 - {keyword}: {e}")
        return None


def extract_search_volume(searchad_data: Dict[str, Any], keyword: str) -> Optional[int]:
    """
    검색광고 데이터에서 검색량 추출 (keyword_analysis와 동일 로직)
    """
    try:
        # 정규화된 응답 처리
        keywords = searchad_data.get('keywords', [])
        if keywords:
            # 정확히 일치하는 키워드 찾기
            for kw_data in keywords:
                if kw_data.get('keyword', '').strip().upper() == keyword.strip().upper():
                    return kw_data.get('monthly_total_searches', 0)
            
            # 일치하는 키워드가 없으면 첫 번째 키워드의 검색량 사용
            if keywords:
                return keywords[0].get('monthly_total_searches', 0)
        
        # Raw 응답 처리 (keywordList 필드)
        keyword_list = searchad_data.get('keywordList', [])
        if keyword_list:
            for item in keyword_list:
                if item.get('relKeyword', '').strip().upper() == keyword.strip().upper():
                    pc_count = item.get('monthlyPcQcCnt', '0')
                    mobile_count = item.get('monthlyMobileQcCnt', '0')
                    
                    # "< 10" 값 처리
                    pc_volume = 0 if pc_count == '< 10' else int(pc_count)
                    mobile_volume = 0 if mobile_count == '< 10' else int(mobile_count)
                    
                    return pc_volume + mobile_volume
        
        return None
        
    except Exception as e:
        logger.warning(f"검색량 추출 실패 - {keyword}: {e}")
        return None


def extract_category_with_percentage(shopping_data: Dict[str, Any]) -> str:
    """
    쇼핑 데이터에서 상위 카테고리와 비율 추출 (상위 40개 상품 분석)
    """
    try:
        products = shopping_data.get('products', [])
        if not products:
            return ""
            
        # 모든 카테고리 경로 수집
        all_category_paths = []
        for product in products:
            categories = product.get('categories', [])
            if categories:
                # 전체 카테고리 경로 생성 (예: "디지털/가전 > 휴대폰 > 스마트폰")
                category_path = ' > '.join(categories)
                all_category_paths.append(category_path)
        
        if not all_category_paths:
            return ""
        
        # 가장 많이 나타나는 카테고리 찾기
        category_counter = Counter(all_category_paths)
        most_common = category_counter.most_common(1)  # 1위만
        
        if most_common:
            category_path, count = most_common[0]
            total = len(all_category_paths)
            percentage = int((count / total) * 100)
            
            result = f"{category_path} ({percentage}%)"
            logger.debug(f"카테고리 분석 결과: {result}")
            return result
        
        return ""
        
    except Exception as e:
        logger.warning(f"카테고리 추출 실패: {e}")
        return ""


def analyze_keyword(keyword: str) -> KeywordBasicData:
    """
    단일 키워드 분석 (월검색량 + 카테고리)
    """
    try:
        logger.debug(f"키워드 분석 시작: {keyword}")
        
        # 1. 검색광고 API로 월검색량 조회
        searchad_data = fetch_searchad_raw(keyword)
        search_volume = 0
        if searchad_data:
            search_volume = extract_search_volume(searchad_data, keyword) or 0
        
        # 2. 쇼핑 API로 카테고리 조회
        shopping_data = fetch_shopping_normalized(keyword)
        category = ""
        if shopping_data:
            category = extract_category_with_percentage(shopping_data)
        
        result = KeywordBasicData(
            keyword=keyword,
            search_volume=search_volume,
            category=category or "카테고리 없음",
            competition=""  # 빈 값으로 설정
        )
        
        logger.debug(f"키워드 분석 완료: {keyword} - 검색량: {search_volume}, 카테고리: {category}")
        return result
        
    except Exception as e:
        logger.error(f"키워드 분석 실패 - {keyword}: {e}")
        return KeywordBasicData(
            keyword=keyword,
            search_volume=0,
            category="분석 실패",
            competition="알 수 없음"
        )


def analyze_keywords_batch(keywords: List[str]) -> List[KeywordBasicData]:
    """
    키워드 일괄 분석
    
    Args:
        keywords: 분석할 키워드 리스트
        
    Returns:
        List[KeywordBasicData]: 분석 결과 리스트
    """
    results = []
    
    for keyword in keywords:
        result = analyze_keyword(keyword)
        results.append(result)
    
    logger.info(f"키워드 일괄 분석 완료: {len(results)}개")
    return results


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
        
        from src.vendors.naver.client_factory import get_shopping_client
        client = get_shopping_client()
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