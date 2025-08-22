"""
네이버 API 응답 데이터 구조 정의
Raw API 응답을 그대로 표현하는 DTO 클래스들
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class NaverShoppingItem:
    """네이버 쇼핑 API 상품 아이템"""
    title: str
    link: str
    image: str
    lprice: str
    hprice: str
    mallName: str
    productId: str
    productType: str
    brand: str
    maker: str
    category1: str
    category2: str
    category3: str
    category4: str = ""
    category5: str = ""
    category6: str = ""
    category7: str = ""
    category8: str = ""
    category9: str = ""


@dataclass
class NaverShoppingResponse:
    """네이버 쇼핑 API 응답"""
    lastBuildDate: str
    total: int
    start: int
    display: int
    items: List[NaverShoppingItem]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NaverShoppingResponse':
        """딕셔너리에서 응답 객체 생성"""
        items = [NaverShoppingItem(**item) for item in data.get('items', [])]
        return cls(
            lastBuildDate=data.get('lastBuildDate', ''),
            total=data.get('total', 0),
            start=data.get('start', 1),
            display=data.get('display', 10),
            items=items
        )


@dataclass
class NaverSearchAdKeywordData:
    """네이버 검색광고 API 키워드 데이터"""
    relKeyword: str
    monthlyPcQcCnt: int
    monthlyMobileQcCnt: int
    monthlyAvePcClkCnt: float
    monthlyAveMobileClkCnt: float
    monthlyAvePcCtr: float
    monthlyAveMobileCtr: float
    plAvgDepth: int
    compIdx: str


@dataclass
class NaverSearchAdResponse:
    """네이버 검색광고 API 응답"""
    keywordList: List[NaverSearchAdKeywordData]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NaverSearchAdResponse':
        """딕셔너리에서 응답 객체 생성"""
        keyword_list = []
        for item in data.get('keywordList', []):
            keyword_list.append(NaverSearchAdKeywordData(**item))
        
        return cls(keywordList=keyword_list)


@dataclass
class NaverAPIResponse:
    """통합 네이버 API 응답"""
    lastBuildDate: str
    total: int
    start: int
    display: int
    items: List[Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NaverAPIResponse':
        """딕셔너리에서 응답 객체 생성"""
        return cls(
            lastBuildDate=data.get('lastBuildDate', ''),
            total=data.get('total', 0),
            start=data.get('start', 1),
            display=data.get('display', 10),
            items=data.get('items', [])
        )


@dataclass
class NaverAPIError:
    """네이버 API 에러 응답"""
    errorCode: str
    errorMessage: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NaverAPIError':
        """딕셔너리에서 에러 객체 생성"""
        return cls(
            errorCode=data.get('errorCode', ''),
            errorMessage=data.get('errorMessage', '')
        )