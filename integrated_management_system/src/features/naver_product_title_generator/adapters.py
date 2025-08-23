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


# 위 함수들은 기존 keyword_analysis 서비스를 사용하도록 변경되어 제거됨
# AI 키워드 분석에서는 src.features.keyword_analysis.service.KeywordAnalysisService 사용


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