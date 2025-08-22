"""
벤더 정규화 → 기능형 데이터로 변환
네이버 API 응답을 키워드 분석 전용 데이터로 가공
"""
from typing import List, Dict, Any, Optional
from collections import Counter

from src.vendors.naver.normalizers import normalize_shopping_response, normalize_searchad_response
# get_last_category는 현재 사용되지 않음
from src.foundation.logging import get_logger
from .models import KeywordData

logger = get_logger("features.keyword_analysis.adapters")


class KeywordAnalysisAdapter:
    """키워드 분석 데이터 어댑터"""
    
    @staticmethod
    def extract_search_volume(searchad_data: Dict[str, Any], keyword: str) -> Optional[int]:
        """
        검색광고 데이터에서 검색량 추출 (raw/정규화 응답 모두 처리)
        
        Args:
            searchad_data: 검색광고 API 응답 (raw 또는 정규화됨)
            keyword: 대상 키워드
        
        Returns:
            Optional[int]: 월간 검색량
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
                # 첫 번째 키워드의 검색량 추출
                first_keyword = keyword_list[0]
                
                # "< 10" 값을 0으로 처리
                pc_count = first_keyword.get('monthlyPcQcCnt', '0')
                mobile_count = first_keyword.get('monthlyMobileQcCnt', '0')
                
                monthly_pc = 0 if pc_count == '< 10' else int(pc_count or 0)
                monthly_mobile = 0 if mobile_count == '< 10' else int(mobile_count or 0)
                
                return monthly_pc + monthly_mobile
            
            return None
            
        except Exception as e:
            logger.warning(f"검색량 추출 실패 - {keyword}: {e}")
            return None
    
    @staticmethod
    def extract_category_for_keyword_analysis(shopping_data: Dict[str, Any]) -> str:
        """
        쇼핑 데이터에서 키워드 분석용 카테고리 추출
        상위 40개 상품의 카테고리를 분석하여 전체 경로로 반환
        
        Args:
            shopping_data: 정규화된 쇼핑 API 응답
        
        Returns:
            str: 대표 카테고리 전체 경로 (예: "패션의류 > 여성의류 > 원피스")
        """
        try:
            products = shopping_data.get('products', [])
            if not products:
                return ""
            
            # 모든 상품의 카테고리 경로 수집
            all_category_paths = []
            for product in products:
                categories = product.get('categories', [])
                if categories:
                    # 카테고리를 '/'로 연결하여 전체 경로 생성 (기존 통합관리프로그램과 동일)
                    category_path = '/'.join(categories)
                    all_category_paths.append(category_path)
            
            if not all_category_paths:
                return ""
            
            # 상위 2개 카테고리 경로 찾기 (기존 통합관리프로그램과 동일)
            category_counter = Counter(all_category_paths)
            most_common = category_counter.most_common(2)  # 상위 2개
            
            if most_common:
                total = len(all_category_paths)
                result_lines = []
                
                for category_path, count in most_common:
                    percentage = int((count / total) * 100)
                    result_lines.append(f"{category_path}({percentage}%)")
                
                result = "\n".join(result_lines)
                logger.debug(f"카테고리 분석 결과: {len(most_common)}개 카테고리")
                return result
            
            return ""
            
        except Exception as e:
            logger.warning(f"카테고리 추출 실패: {e}")
            return ""
    
    @staticmethod
    def extract_total_products(shopping_data: Dict[str, Any]) -> Optional[int]:
        """
        쇼핑 데이터에서 총 상품 수 추출
        
        Args:
            shopping_data: 정규화된 쇼핑 API 응답
        
        Returns:
            Optional[int]: 총 상품 수
        """
        try:
            return shopping_data.get('total_count', 0)
        except Exception as e:
            logger.warning(f"상품 수 추출 실패: {e}")
            return None
    
    @staticmethod
    def calculate_competition_strength(search_volume: Optional[int], 
                                     total_products: Optional[int]) -> Optional[float]:
        """
        경쟁 강도 계산 (검색량/상품수)
        
        Args:
            search_volume: 월간 검색량
            total_products: 총 상품 수
        
        Returns:
            Optional[float]: 경쟁 강도
        """
        try:
            if not search_volume or not total_products or total_products == 0:
                return float('inf')  # 무한대로 표시
            
            return total_products / search_volume
            
        except Exception as e:
            logger.warning(f"경쟁 강도 계산 실패: {e}")
            return None
    
    @staticmethod
    def build_keyword_data(keyword: str,
                          searchad_data: Optional[Dict[str, Any]] = None,
                          shopping_data: Optional[Dict[str, Any]] = None) -> KeywordData:
        """
        키워드 분석 데이터 구성
        
        Args:
            keyword: 키워드
            searchad_data: 정규화된 검색광고 API 응답
            shopping_data: 정규화된 쇼핑 API 응답
        
        Returns:
            KeywordData: 키워드 분석 데이터
        """
        try:
            # 검색량 추출
            search_volume = None
            if searchad_data:
                search_volume = KeywordAnalysisAdapter.extract_search_volume(searchad_data, keyword)
            
            # 카테고리 및 상품 수 추출
            category = ""
            total_products = None
            if shopping_data:
                category = KeywordAnalysisAdapter.extract_category_for_keyword_analysis(shopping_data)
                total_products = KeywordAnalysisAdapter.extract_total_products(shopping_data)
            
            # 경쟁 강도 계산
            competition_strength = KeywordAnalysisAdapter.calculate_competition_strength(
                search_volume, total_products
            )
            
            keyword_data = KeywordData(
                keyword=keyword,
                category=category,
                search_volume=search_volume,
                total_products=total_products,
                competition_strength=competition_strength
            )
            
            logger.debug(f"키워드 데이터 구성 완료: {keyword}")
            return keyword_data
            
        except Exception as e:
            logger.error(f"키워드 데이터 구성 실패 - {keyword}: {e}")
            # 오류 발생 시 기본 데이터 반환
            return KeywordData(keyword=keyword)


class BatchAnalysisAdapter:
    """배치 분석 데이터 어댑터"""
    
    @staticmethod
    def process_keyword_batch(keywords: List[str],
                            searchad_responses: Dict[str, Dict[str, Any]],
                            shopping_responses: Dict[str, Dict[str, Any]]) -> List[KeywordData]:
        """
        키워드 배치 처리
        
        Args:
            keywords: 키워드 목록
            searchad_responses: 키워드별 검색광고 API 응답
            shopping_responses: 키워드별 쇼핑 API 응답
        
        Returns:
            List[KeywordData]: 키워드 분석 결과 목록
        """
        results = []
        
        for keyword in keywords:
            try:
                searchad_data = searchad_responses.get(keyword)
                shopping_data = shopping_responses.get(keyword)
                
                keyword_data = KeywordAnalysisAdapter.build_keyword_data(
                    keyword, searchad_data, shopping_data
                )
                
                results.append(keyword_data)
                
            except Exception as e:
                logger.error(f"키워드 배치 처리 실패 - {keyword}: {e}")
                # 오류 발생 시 기본 데이터 추가
                results.append(KeywordData(keyword=keyword))
        
        logger.info(f"배치 처리 완료: {len(results)}개 키워드")
        return results


# 편의 함수들
def adapt_keyword_data(keyword: str,
                      searchad_data: Optional[Dict[str, Any]] = None,
                      shopping_data: Optional[Dict[str, Any]] = None) -> KeywordData:
    """키워드 데이터 어댑터 편의 함수"""
    return KeywordAnalysisAdapter.build_keyword_data(keyword, searchad_data, shopping_data)


def adapt_keyword_batch(keywords: List[str],
                       searchad_responses: Dict[str, Dict[str, Any]],
                       shopping_responses: Dict[str, Dict[str, Any]]) -> List[KeywordData]:
    """키워드 배치 어댑터 편의 함수"""
    return BatchAnalysisAdapter.process_keyword_batch(keywords, searchad_responses, shopping_responses)