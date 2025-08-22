"""
순위 추적 어댑터 - vendors 레이어 응답을 features 데이터로 가공
Raw API 응답을 비즈니스 로직에서 사용할 수 있는 형태로 변환
"""
from typing import Optional, Dict, Any, List
import re

from .models import ProductInfo, RankingResult
from src.vendors.naver.developer.shopping_client import naver_shopping_client
from src.vendors.naver.searchad.keyword_client import NaverKeywordToolClient
from src.foundation.logging import get_logger

logger = get_logger("features.rank_tracking.adapters")

RANK_OUT_OF_RANGE = 999  # 200위 밖을 나타내는 상수


def format_date(date_str: str) -> str:
    """날짜 형식 변환 (8/6 14:26)"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%m/%d %H:%M")
    except:
        return date_str


def format_date_with_time(date_str: str) -> str:
    """날짜 시간 형식 변환 (2025-08-07 15:23)"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


def format_rank_display(rank: int) -> str:
    """순위 숫자를 사용자 친화적인 형태로 포맷팅"""
    if rank == 999 or rank > 200:  # RANK_OUT_OF_RANGE = 999
        return "200위밖"
    elif rank >= 1:  # 정상적인 순위 (1~200)
        return f"{rank}위"
    else:
        return "-"  # 0, None이나 기타 경우 (오류 상황 또는 아직 확인 안됨)


def get_rank_color(rank: int, color_type: str = "background") -> str:
    """순위에 따른 색상 반환"""
    if color_type == "background":
        # 배경색 (연한 톤)
        if rank <= 10:
            return "#e8f5e8"  # 연한 초록
        elif rank <= 50:
            return "#fff3cd"  # 연한 노랑
        else:
            return "#f8d7da"  # 연한 빨강
    else:  # foreground/text color
        # 텍스트 색상 (진한 톤)
        if rank == -1 or rank == 0:  # 검색량 없음/API 실패
            return "#6B7280"  # 회색
        elif rank <= 10:
            return "#059669"  # 초록색 (상위 10위)
        elif rank <= 50:
            return "#D97706"  # 주황색 (50위 이내)
        else:
            return "#DC2626"  # 빨간색 (50위 초과)


def format_monthly_volume(volume: int) -> str:
    """월검색량 포맷팅"""
    if volume == -1:
        return "API 호출 실패"
    elif volume == 0:
        return "0"
    else:
        return f"{volume:,}"


def get_category_match_color(project_category: str, keyword_category: str) -> str:
    """카테고리 매칭 결과에 따른 색상 반환"""
    if not project_category or not keyword_category:
        return "#6B7280"  # 회색 (데이터 없음)
    
    # 카테고리 비교를 위한 기본 형태로 변환
    project_base = project_category.split(' > ')[-1] if ' > ' in project_category else project_category
    keyword_base = keyword_category.split(' > ')[-1] if ' > ' in keyword_category else keyword_category
    
    if project_base == keyword_base:
        return "#059669"  # 초록색 (일치)
    else:
        return "#DC2626"  # 빨간색 (불일치)


class RankTrackingAdapter:
    """순위 추적 어댑터"""
    
    def __init__(self):
        self.shopping_client = naver_shopping_client
        self.keyword_client = NaverKeywordToolClient()
    
    def extract_product_id_from_url(self, url: str) -> str:
        """네이버 쇼핑 URL에서 상품 ID 추출"""
        if not url or not isinstance(url, str):
            raise ValueError("URL이 비어있거나 올바르지 않습니다")
        
        patterns = [
            r'https?://shopping\.naver\.com/catalog/(\d+)',
            r'https?://smartstore\.naver\.com/[^/]+/products/(\d+)',
            r'https?://brand\.naver\.com/[^/]+/products/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(
            f"지원되지 않는 네이버 쇼핑 URL 형식입니다: {url}\n"
            "올바른 형식: https://shopping.naver.com/catalog/XXXXX 또는 "
            "https://smartstore.naver.com/store/products/XXXXX"
        )
    
    def get_product_info(self, product_name: str, product_id: str) -> Optional[ProductInfo]:
        """상품 정보 조회 (vendors -> ProductInfo DTO 변환)"""
        try:
            raw_data = self.shopping_client.smart_product_search(product_name, product_id)
            if not raw_data:
                return None
            
            return ProductInfo(
                product_id=raw_data.get('product_id', ''),
                name=self._clean_product_name(raw_data.get('name', '')),
                price=raw_data.get('price', 0),
                category=raw_data.get('category', ''),  # 전체 카테고리 경로 유지
                store_name=raw_data.get('store_name', ''),
                description=raw_data.get('description', ''),
                image_url=raw_data.get('image_url', ''),
                url=raw_data.get('url', '')
            )
            
        except Exception as e:
            logger.error(f"상품 정보 조회 실패: {product_name} ({product_id}): {e}")
            return None
    
    def check_product_rank(self, keyword: str, product_id: str) -> RankingResult:
        """키워드에서 상품 순위 확인"""
        result = RankingResult(
            keyword=keyword,
            product_id=product_id,
            success=False
        )
        
        try:
            rank = self.shopping_client.find_product_rank(keyword, product_id, max_pages=10)
            
            result.success = True
            result.rank = rank if rank is not None else RANK_OUT_OF_RANGE
            
            # 총 결과 수는 대략적으로 계산 (실제로는 더 복잡한 로직 필요)
            if rank is not None:
                result.total_results = max(rank, 100)  # 최소 100개는 있다고 가정
            else:
                result.total_results = 1000  # 최대 검색 가능 수
            
            logger.info(f"순위 확인 성공: {keyword} -> {product_id} = {rank or '200+'}위")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"순위 확인 실패: {keyword} -> {product_id}: {e}")
        
        return result
    
    def get_keyword_monthly_volume(self, keyword: str) -> Optional[int]:
        """키워드 월 검색량 조회 (검색광고 API 활용)"""
        try:
            volume = self.keyword_client.get_single_search_volume(keyword)
            logger.debug(f"월검색량 조회: {keyword} -> {volume}")
            return volume
        except Exception as e:
            logger.warning(f"월검색량 조회 실패: {keyword}: {e}")
            return None
    
    def get_keyword_category(self, keyword: str) -> Optional[str]:
        """키워드 대표 카테고리 조회 (쇼핑 API 활용)"""
        try:
            category = self.shopping_client.get_keyword_category(keyword, sample_size=40)
            logger.debug(f"카테고리 조회: {keyword} -> {category}")
            return category
        except Exception as e:
            logger.warning(f"카테고리 조회 실패: {keyword}: {e}")
            return None
    
    def analyze_keyword_for_tracking(self, keyword: str) -> Dict[str, Any]:
        """추적용 키워드 종합 분석 (월검색량 + 카테고리)"""
        result = {
            'keyword': keyword,
            'monthly_volume': 0,
            'category': '',
            'success': False,
            'error_message': None
        }
        
        try:
            # 월검색량 조회
            monthly_volume = self.get_keyword_monthly_volume(keyword)
            if monthly_volume is not None:
                result['monthly_volume'] = monthly_volume
            
            # 카테고리 조회
            category = self.get_keyword_category(keyword)
            if category:
                result['category'] = category
            
            result['success'] = True
            logger.info(f"키워드 분석 완료: {keyword} (볼륨: {monthly_volume}, 카테고리: {category})")
            
        except Exception as e:
            result['error_message'] = str(e)
            logger.error(f"키워드 분석 실패: {keyword}: {e}")
        
        return result
    
    
    def check_multiple_keywords_rank(self, keywords: List[str], product_id: str) -> List[RankingResult]:
        """여러 키워드의 순위를 한번에 검색"""
        results = []
        for keyword in keywords:
            try:
                result = self.check_product_rank(keyword, product_id)
                results.append(result)
            except Exception as e:
                logger.error(f"키워드 순위 검색 실패: {keyword}: {e}")
                # 실패한 경우도 결과에 포함
                failed_result = RankingResult(
                    keyword=keyword,
                    product_id=product_id,
                    success=False,
                    error_message=str(e)
                )
                results.append(failed_result)
        
        return results
    
    def analyze_keywords_for_tracking(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """여러 키워드의 검색량과 카테고리를 한번에 분석"""
        results = []
        for keyword in keywords:
            try:
                result = self.analyze_keyword_for_tracking(keyword)
                results.append(result)
            except Exception as e:
                logger.error(f"키워드 분석 실패: {keyword}: {e}")
                # 실패한 경우도 결과에 포함
                failed_result = {
                    'keyword': keyword,
                    'monthly_volume': 0,
                    'category': '',
                    'success': False,
                    'error_message': str(e)
                }
                results.append(failed_result)
        
        return results
    
    def _clean_product_name(self, name: str) -> str:
        """상품명 정리 (HTML 태그 제거 등)"""
        if not name:
            return ""
        
        import re
        # HTML 태그 제거
        clean_name = re.sub(r'<[^>]+>', '', name)
        # 특수문자 정리
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        return clean_name
    
    def check_keyword_ranking(self, keyword: str, product_id: str) -> dict:
        """키워드 순위 확인 (Raw API 방식)"""
        try:
            import requests
            from src.foundation.config import config_manager
            
            # API 설정 로드
            api_config = config_manager.load_api_config()
            
            if not api_config.shopping_client_id or not api_config.shopping_client_secret:
                return {
                    'success': False,
                    'rank': 999,
                    'error': '네이버 쇼핑 API 설정이 필요합니다'
                }
            
            headers = {
                'X-Naver-Client-Id': api_config.shopping_client_id,
                'X-Naver-Client-Secret': api_config.shopping_client_secret
            }
            
            # 키워드 정리 (원본과 동일하게 공백 제거 + 대문자 변환)
            clean_keyword = keyword.replace(' ', '').upper()
            
            # 200위까지 검색 (100개씩 2페이지)
            for page in range(2):
                start = page * 100 + 1
                display = 100
                
                params = {
                    'query': clean_keyword,
                    'display': display,
                    'start': start,
                    'sort': 'sim'  # 정확도순
                }
                
                # API 재시도 로직 (3번 시도)
                max_retries = 3
                retry_count = 0
                data = None
                
                while retry_count < max_retries:
                    try:
                        response = requests.get(
                            'https://openapi.naver.com/v1/search/shop.json',
                            params=params,
                            headers=headers,
                            timeout=10
                        )
                        
                        if response.status_code == 429:  # Too Many Requests
                            import time
                            wait_time = 2 ** retry_count  # 지수 백오프: 2, 4, 8초
                            logger.warning(f"키워드 '{keyword}' API 요청 한도 초과, {wait_time}초 대기 후 재시도 ({retry_count + 1}/{max_retries})")
                            time.sleep(wait_time)
                            retry_count += 1
                            continue
                        
                        response.raise_for_status()
                        data = response.json()
                        break  # 성공시 루프 탈출
                        
                    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 1 * retry_count  # 1, 2, 3초 대기
                            logger.warning(f"키워드 '{keyword}' API 호출 실패, {wait_time}초 대기 후 재시도 ({retry_count}/{max_retries}): {e}")
                            import time
                            time.sleep(wait_time)
                        else:
                            logger.error(f"키워드 '{keyword}' API 호출 {max_retries}번 시도 모두 실패: {e}")
                            return {
                                'success': False,
                                'rank': 999,
                                'error': f'API 호출 실패 ({max_retries}번 시도): {str(e)}'
                            }
                
                if data is None:
                    continue  # 다음 페이지로
                
                items = data.get('items', [])
                if not items:
                    continue
                
                # 상품 ID로 순위 찾기
                for index, item in enumerate(items):
                    try:
                        link = item.get('link', '')
                        if link and product_id in link:
                            rank = start + index
                            if rank <= 200:
                                logger.info(f"키워드 '{keyword}' 순위 발견: {rank}위")
                                return {
                                    'success': True,
                                    'rank': rank,
                                    'total_results': data.get('total', 0),
                                }
                            else:
                                # 200위 초과
                                return {
                                    'success': True,
                                    'rank': 999,
                                    'total_results': data.get('total', 0),
                                }
                    except Exception as e:
                        continue
                
                # API 호출 간 딜레이
                import time
                time.sleep(0.5)
            
            # 200위 이내에서 찾지 못함
            logger.info(f"키워드 '{keyword}' 200위 밖")
            return {
                'success': True,
                'rank': 999,
                'total_results': 0,
            }
            
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 순위 확인 실패: {e}")
            return {
                'success': False,
                'rank': 999,
                'error': str(e)
            }


# 전역 어댑터 인스턴스
rank_tracking_adapter = RankTrackingAdapter()