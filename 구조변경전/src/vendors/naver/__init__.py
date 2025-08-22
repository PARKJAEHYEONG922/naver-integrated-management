"""
네이버 API 벤더 모듈 (재구성)
Raw API 호출 및 최소 정규화

새로운 구조:
- developer/: 네이버 개발자 센터 API (검색 API들)
- searchad/: 네이버 검색광고 API
- 통합 팩토리로 모든 API 쉽게 접근
"""

# === 기존 호환성 유지 (하위 호환성) ===
# 이전 방식으로도 계속 사용 가능
from .developer.shopping_client import naver_shopping_client
from .searchad.keyword_client import naver_searchad_client

# === 새로운 통합 구조 - 네이버 개발자 API ===
from .developer import (
    SearchType, SortOption, get_api_info, get_available_search_types,
    NaverSearchClient,
    NaverShoppingClient, NaverNewsClient, NaverBlogClient, NaverBookClient
)

# === 새로운 통합 구조 - 네이버 검색광고 API ===
from .searchad import (
    SearchAdAPIType, get_searchad_api_info,
    NaverSearchAdBaseClient, NaverKeywordToolClient,
    NaverSearchAdClient
)

# === 통합 팩토리 ===
from .client_factory import (
    NaverClientFactory,
    get_shopping_client, get_news_client, get_blog_client, get_book_client,
    get_keyword_tool_client, get_searchad_client,
    search_all_apis
)

# === 공통 모델 및 유틸 ===
from .models import (
    NaverShoppingResponse, NaverSearchAdResponse,
    NaverShoppingItem, NaverSearchAdKeywordData,
    NaverAPIError
)
from .normalizers import normalize_shopping_response, normalize_searchad_response

__all__ = [
    # === 기존 호환성 ===
    'naver_shopping_client',
    'naver_searchad_client',
    
    # === 네이버 개발자 API ===
    'SearchType', 'SortOption', 'get_api_info', 'get_available_search_types',
    'NaverSearchClient',
    'NaverShoppingClient', 'NaverNewsClient', 'NaverBlogClient', 'NaverBookClient',
    
    # === 네이버 검색광고 API ===
    'SearchAdAPIType', 'get_searchad_api_info',
    'NaverSearchAdBaseClient', 'NaverKeywordToolClient', 'NaverSearchAdClient',
    
    # === 통합 팩토리 ===
    'NaverClientFactory',
    'get_shopping_client', 'get_news_client', 'get_blog_client', 'get_book_client',
    'get_keyword_tool_client', 'get_searchad_client',
    'search_all_apis',
    
    # === 공통 모델 및 유틸 ===
    'NaverShoppingResponse', 'NaverSearchAdResponse',
    'NaverShoppingItem', 'NaverSearchAdKeywordData', 'NaverAPIError',
    'normalize_shopping_response', 'normalize_searchad_response'
]

# === 사용 예시 (문서화용) ===
"""
새로운 폴더 구조 사용 예시:

# 기존 방식 (하위 호환성 유지)
from src.vendors.naver import naver_shopping_client, naver_searchad_client
shopping = naver_shopping_client.search_products("키워드")
searchad = naver_searchad_client.get_keyword_ideas(["키워드"])

# 새로운 통합 팩토리 방식
from src.vendors.naver import NaverClientFactory
shopping_client = NaverClientFactory.get_shopping_client()
keyword_tool = NaverClientFactory.get_keyword_tool_client()

# 편의 함수 방식 (추천)
from src.vendors.naver import get_shopping_client, get_keyword_tool_client
shopping = get_shopping_client().search_products("키워드")
volume = get_keyword_tool_client().get_search_volume("키워드")

# 직접 임포트 방식
from src.vendors.naver.developer import NaverShoppingClient
from src.vendors.naver.searchad import NaverSearchAdClient
shopping_client = NaverShoppingClient()
searchad_client = NaverSearchAdClient()

# 모든 검색 API 동시 사용
from src.vendors.naver import search_all_apis
results = search_all_apis("키워드", display=20)

향후 확장:
- src.vendors.google.search: 구글 검색 API
- src.vendors.google.ads: 구글 광고 API  
- src.vendors.google.youtube: 유튜브 API
"""