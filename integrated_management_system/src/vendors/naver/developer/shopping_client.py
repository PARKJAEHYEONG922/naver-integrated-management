"""
네이버 쇼핑 API 클라이언트 (베이스 클라이언트 상속)
Raw API 호출만 담당, 가공은 하지 않음
순위추적 기능 포함
"""
from typing import Optional, Dict, Any, List, Tuple
from collections import Counter
import re

from .base_client import NaverSearchClient
from .search_apis import SearchType, get_api_info, validate_sort_option
from ..models import NaverShoppingResponse, NaverAPIError
from src.foundation.exceptions import NaverShoppingAPIError
from src.foundation.logging import get_logger

logger = get_logger("vendors.naver.shopping")


class NaverShoppingClient(NaverSearchClient):
    """네이버 쇼핑 API 클라이언트 (베이스 클라이언트 상속)"""
    
    def __init__(self):
        super().__init__(SearchType.SHOPPING.value, rate_limit=1.0)
        self.api_info = get_api_info(SearchType.SHOPPING)
    
    def search_products(self, 
                       query: str,
                       display: int = 10,
                       start: int = 1,
                       sort: str = "sim",
                       filter_option: Optional[str] = None,
                       exclude: Optional[str] = None) -> NaverShoppingResponse:
        """
        상품 검색
        
        Args:
            query: 검색어
            display: 검색 결과 출력 건수 (1~100)
            start: 검색 시작 위치 (1~1000)
            sort: 정렬 옵션 (sim:정확도순, date:날짜순, asc:가격오름차순, dsc:가격내림차순)
            filter_option: 상품 필터링 옵션
            exclude: 제외할 상품 타입
        
        Returns:
            NaverShoppingResponse: 검색 응답
        """
        # 정렬 옵션 유효성 확인
        if not validate_sort_option(SearchType.SHOPPING, sort):
            logger.warning(f"유효하지 않은 정렬 옵션: {sort}, 기본값으로 대체")
            sort = self.api_info.default_sort
        
        # 추가 파라미터 구성
        additional_params = {}
        if filter_option:
            additional_params['filter'] = filter_option
        if exclude:
            additional_params['exclude'] = exclude
        
        try:
            # 베이스 클라이언트의 통합 검색 메서드 사용
            data = self.search(
                query=query,
                display=display,
                start=start,
                sort=sort,
                **additional_params
            )
            
            # 에러 응답 확인
            if 'errorCode' in data:
                error = NaverAPIError.from_dict(data)
                raise NaverShoppingAPIError(f"API 에러: {error.errorMessage} (코드: {error.errorCode})")
            
            logger.debug(f"네이버 쇼핑 API 성공: {data.get('total', 0)}개 결과")
            return NaverShoppingResponse.from_dict(data)
            
        except Exception as e:
            logger.error(f"네이버 쇼핑 API 호출 실패: {e}")
            if isinstance(e, NaverShoppingAPIError):
                raise
            raise NaverShoppingAPIError(f"API 호출 실패: {e}")
    
    # 하위 호환성을 위한 기존 메서드명 유지
    def get_products(self, *args, **kwargs) -> NaverShoppingResponse:
        """기존 코드 호환성을 위한 별칭"""
        return self.search_products(*args, **kwargs)
    
    # 순위추적 기능
    def find_product_rank(self, keyword: str, product_id: str, max_pages: int = 10) -> Optional[int]:
        """
        키워드 검색에서 특정 상품의 순위를 찾기
        
        Args:
            keyword: 검색 키워드
            product_id: 찾을 상품 ID
            max_pages: 최대 검색 페이지 수 (1페이지당 100개, 총 1000개까지)
        
        Returns:
            순위 (1부터 시작), 찾지 못하면 None
        """
        try:
            for page in range(1, max_pages + 1):
                start = (page - 1) * 100 + 1
                
                # 페이지당 100개씩 검색 (최대)
                response = self.search_products(
                    query=keyword,
                    display=100,
                    start=start,
                    sort="sim"  # 정확도 순
                )
                
                if not response.items:
                    break
                
                # 현재 페이지에서 상품 찾기
                for idx, item in enumerate(response.items):
                    current_rank = start + idx
                    
                    # productId가 link에 포함되어 있는지 확인
                    if self._extract_product_id_from_link(item.link) == product_id:
                        logger.info(f"상품 순위 찾음: {keyword} -> {product_id} = {current_rank}위")
                        return current_rank
                
                # 더 이상 결과가 없으면 중단
                if len(response.items) < 100:
                    break
            
            logger.info(f"상품 순위 못찾음: {keyword} -> {product_id} (200위 밖)")
            return None
            
        except Exception as e:
            logger.error(f"순위 검색 실패: {keyword} -> {product_id}: {e}")
            return None
    
    def get_keyword_category(self, keyword: str, sample_size: int = 40) -> Optional[str]:
        """
        키워드의 대표 카테고리 조회 (상위 결과 분석) - 원본 로직과 동일
        
        Args:
            keyword: 분석할 키워드
            sample_size: 분석할 상품 수
        
        Returns:
            대표 카테고리 (전체 경로) + 퍼센트, 없으면 None
        """
        try:
            # 공백 제거 + 대문자 변환 (원본과 동일)
            clean_keyword = keyword.replace(' ', '').upper()
            
            response = self.search_products(
                query=clean_keyword,
                display=sample_size,
                sort="sim"
            )
            
            if not response.items:
                logger.debug(f"키워드 '{keyword}': 검색 결과 없음")
                return None
            
            # 모든 상품의 카테고리 경로 수집 (원본과 동일한 로직)
            all_categories = []
            for item in response.items:
                # 실제로 존재하는 모든 카테고리 찾기 (category1~category4까지 확인)
                categories = []
                for cat_field in ['category1', 'category2', 'category3', 'category4']:
                    if hasattr(item, cat_field):
                        category_value = getattr(item, cat_field)
                        if category_value and category_value.strip():
                            categories.append(category_value.strip())
                        else:
                            break  # 빈 카테고리가 나오면 중단
                
                if categories:
                    # 전체 카테고리 경로를 ' > '로 연결 (원본과 동일)
                    full_category_path = ' > '.join(categories)
                    all_categories.append(full_category_path)
            
            logger.debug(f"키워드 '{keyword}': {len(all_categories)}개 카테고리 수집")
            
            if not all_categories:
                return None
            
            # 카테고리별 개수 카운트 및 비율 계산 (원본과 동일)
            category_counter = Counter(all_categories)
            most_common = category_counter.most_common(1)  # 상위 1개만
            total = sum(category_counter.values())
            
            if most_common:
                cat, count = most_common[0]
                percentage = int((count / total) * 100)
                
                # 전체 경로에 비율 정보 추가해서 반환
                result = f"{cat}({percentage}%)"
                logger.debug(f"키워드 카테고리 분석 완료: {keyword} -> {result}")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"카테고리 분석 실패: {keyword}: {e}")
            return None
    
    def smart_product_search(self, product_name: str, product_id: str) -> Optional[Dict[str, Any]]:
        """
        스마트 상품 검색 - 상품명과 ID를 이용한 정확한 상품 정보 조회
        
        Args:
            product_name: 상품명
            product_id: 상품 ID
        
        Returns:
            상품 정보 딕셔너리, 못찾으면 None
        """
        try:
            # 1차: 상품명으로 검색
            response = self.search_products(
                query=product_name,
                display=50,
                sort="sim"
            )
            
            if not response.items:
                return None
            
            # 정확한 productId 매칭으로 찾기
            for item in response.items:
                if self._extract_product_id_from_link(item.link) == product_id:
                    # 카테고리 정보를 원본과 동일하게 처리 (전체 경로)
                    categories = []
                    for cat_field in ['category1', 'category2', 'category3', 'category4']:
                        if hasattr(item, cat_field):
                            category_value = getattr(item, cat_field)
                            if category_value and category_value.strip():
                                categories.append(category_value.strip())
                            else:
                                break
                    
                    category_str = ' > '.join(categories) if categories else ''
                    
                    return {
                        'product_id': product_id,
                        'name': item.title.replace('<b>', '').replace('</b>', ''),
                        'price': self._extract_price(item.lprice),
                        'category': category_str,
                        'store_name': item.mallName or '',
                        'description': getattr(item, 'description', ''),
                        'image_url': item.image or '',
                        'url': item.link
                    }
            
            logger.warning(f"정확한 상품 매칭 실패: {product_name} ({product_id})")
            return None
            
        except Exception as e:
            logger.error(f"스마트 상품 검색 실패: {product_name} ({product_id}): {e}")
            return None
    
    def _extract_product_id_from_link(self, link: str) -> Optional[str]:
        """상품 링크에서 productId 추출"""
        if not link:
            return None
        
        patterns = [
            r'https?://shopping\.naver\.com/catalog/(\d+)',
            r'https?://smartstore\.naver\.com/[^/]+/products/(\d+)',
            r'https?://brand\.naver\.com/[^/]+/products/(\d+)',
            r'/catalog/(\d+)',
            r'/products/(\d+)',
            r'productId=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_price(self, price_str: str) -> int:
        """가격 문자열에서 숫자만 추출"""
        if not price_str:
            return 0
        
        # 숫자만 추출
        numbers = re.findall(r'\d+', str(price_str))
        if numbers:
            return int(''.join(numbers))
        return 0
    
    def get_keyword_category(self, keyword: str, sample_size: int = 40) -> Optional[str]:
        """키워드 카테고리 조회 (상위 N개 분석해서 최대 비중 카테고리의 마지막 부분 반환, 원본과 동일)"""
        try:
            # API 호출로 검색 결과 가져오기
            response = self.search(keyword, display=sample_size, sort='sim')
            if not response:
                return None
            
            # response는 dict 형태
            items = response.get('items', [])
            if not items:
                return None
            
            # 모든 상품의 마지막 카테고리만 수집 (원본과 동일)
            from collections import Counter
            all_categories = []
            
            for item in items:
                # 실제로 존재하는 모든 카테고리 찾기 (category1~category4까지 확인)
                categories = []
                for i in range(1, 5):  # category1부터 category4까지 확인
                    category_value = item.get(f'category{i}')
                    if category_value and category_value.strip():
                        categories.append(category_value.strip())
                    else:
                        break  # 빈 카테고리가 나오면 중단
                
                if categories:
                    # 전체 카테고리 경로 사용 (프로젝트 카테고리와 매칭을 위해)
                    full_category_path = ' > '.join(categories)
                    all_categories.append(full_category_path)
            
            if not all_categories:
                return None
            
            # 카테고리별 개수 카운트 및 비율 계산
            category_counter = Counter(all_categories)
            most_common = category_counter.most_common(1)  # 상위 1개만
            total = sum(category_counter.values())
            
            if most_common:
                cat, count = most_common[0]
                percentage = int((count / total) * 100)
                # 전체 경로에 비율 정보 추가해서 반환
                result = f"{cat}({percentage}%)"
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"키워드 카테고리 조회 실패: {keyword}: {e}")
            return None
    
    def find_product_rank(self, keyword: str, product_id: str, max_pages: int = 10) -> Optional[int]:
        """
        키워드 검색에서 특정 상품의 순위를 찾기
        
        Args:
            keyword: 검색 키워드
            product_id: 찾을 상품 ID
            max_pages: 최대 검색 페이지 수 (1페이지당 100개, 총 1000개까지)
        
        Returns:
            순위 (1부터 시작), 찾지 못하면 None
        """
        try:
            for page in range(1, max_pages + 1):
                start = (page - 1) * 100 + 1
                
                # 페이지당 100개씩 검색 (최대)
                response = self.search_products(
                    query=keyword,
                    display=100,
                    start=start,
                    sort="sim"  # 정확도 순
                )
                
                if not response.items:
                    break
                
                # 현재 페이지에서 상품 찾기
                for idx, item in enumerate(response.items):
                    current_rank = start + idx
                    
                    # productId가 link에 포함되어 있는지 확인
                    if self._extract_product_id_from_link(item.link) == product_id:
                        logger.info(f"상품 순위 찾음: {keyword} -> {product_id} = {current_rank}위")
                        return current_rank
                
                # 더 이상 결과가 없으면 중단
                if len(response.items) < 100:
                    break
            
            logger.info(f"상품 순위 못찾음: {keyword} -> {product_id} (200위 밖)")
            return None
            
        except Exception as e:
            logger.error(f"순위 검색 실패: {keyword} -> {product_id}: {e}")
            return None


# 전역 클라이언트 인스턴스
naver_shopping_client = NaverShoppingClient()

# 편의를 위한 별칭
shopping_client = naver_shopping_client