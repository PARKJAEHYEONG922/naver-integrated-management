"""
네이버 응답을 표준 형식으로 변환
필드명/타입 통일(최소 정규화만)
"""
from typing import List, Dict, Any, Optional
from .models import NaverShoppingResponse, NaverSearchAdResponse, NaverShoppingItem, NaverSearchAdKeywordData


class NaverShoppingNormalizer:
    """네이버 쇼핑 API 응답 정규화"""
    
    @staticmethod
    def normalize_product_item(item: NaverShoppingItem) -> Dict[str, Any]:
        """상품 아이템 정규화"""
        return {
            'product_id': item.productId,
            'title': item.title.replace('<b>', '').replace('</b>', ''),  # HTML 태그 제거
            'link': item.link,
            'image_url': item.image,
            'price_min': int(item.lprice) if item.lprice.isdigit() else 0,
            'price_max': int(item.hprice) if item.hprice.isdigit() else 0,
            'mall_name': item.mallName,
            'brand': item.brand,
            'maker': item.maker,
            'product_type': item.productType,
            'categories': [
                getattr(item, f'category{i}', '') 
                for i in range(1, 10) 
                if getattr(item, f'category{i}', '')
            ]
        }
    
    @staticmethod
    def normalize_search_response(response: NaverShoppingResponse) -> Dict[str, Any]:
        """검색 응답 정규화"""
        return {
            'total_count': response.total,
            'start_index': response.start,
            'display_count': response.display,
            'last_build_date': response.lastBuildDate,
            'products': [
                NaverShoppingNormalizer.normalize_product_item(item) 
                for item in response.items
            ]
        }


class NaverSearchAdNormalizer:
    """네이버 검색광고 API 응답 정규화"""
    
    @staticmethod
    def normalize_keyword_data(keyword: NaverSearchAdKeywordData) -> Dict[str, Any]:
        """키워드 데이터 정규화 (원본 통합관리프로그램 방식)"""
        # "< 10" 값을 0으로 처리 (원본처럼)
        pc_searches = 0 if keyword.monthlyPcQcCnt == '< 10' else int(keyword.monthlyPcQcCnt or 0)
        mobile_searches = 0 if keyword.monthlyMobileQcCnt == '< 10' else int(keyword.monthlyMobileQcCnt or 0)
        
        return {
            'keyword': keyword.relKeyword,
            'monthly_pc_searches': pc_searches,
            'monthly_mobile_searches': mobile_searches,
            'monthly_total_searches': pc_searches + mobile_searches,
            'pc_click_count': keyword.monthlyAvePcClkCnt,
            'mobile_click_count': keyword.monthlyAveMobileClkCnt,
            'pc_ctr': keyword.monthlyAvePcCtr,
            'mobile_ctr': keyword.monthlyAveMobileCtr,
            'competition_index': keyword.compIdx,
            'avg_depth': keyword.plAvgDepth
        }
    
    @staticmethod
    def normalize_keyword_response(response: NaverSearchAdResponse) -> Dict[str, Any]:
        """키워드 응답 정규화"""
        return {
            'keyword_count': len(response.keywordList),
            'keywords': [
                NaverSearchAdNormalizer.normalize_keyword_data(keyword)
                for keyword in response.keywordList
            ]
        }


# 편의 함수들
def normalize_shopping_response(response: NaverShoppingResponse) -> Dict[str, Any]:
    """네이버 쇼핑 응답 정규화 편의 함수"""
    return NaverShoppingNormalizer.normalize_search_response(response)


def normalize_searchad_response(response: NaverSearchAdResponse) -> Dict[str, Any]:
    """네이버 검색광고 응답 정규화 편의 함수"""
    return NaverSearchAdNormalizer.normalize_keyword_response(response)


def normalize_search_response(raw_data: Dict[str, Any], api_type: str = "general") -> 'NaverAPIResponse':
    """통합 검색 응답 정규화 함수"""
    from .models import NaverAPIResponse
    return NaverAPIResponse.from_dict(raw_data)