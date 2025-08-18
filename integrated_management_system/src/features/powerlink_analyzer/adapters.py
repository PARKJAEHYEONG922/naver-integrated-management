"""
파워링크 분석기 어댑터
vendors의 Raw API 응답을 파워링크 분석 데이터로 변환
"""
import time
import random
from typing import List, Optional, Dict, Any, Tuple
from playwright.sync_api import BrowserContext

from src.vendors.naver.client_factory import get_keyword_tool_client
from src.foundation.logging import get_logger
from .models import KeywordAnalysisResult, BidPosition
from .config import POWERLINK_CONFIG, NAVER_MIN_BID

logger = get_logger("features.powerlink_analyzer.adapters")


class AdaptiveRateLimiter:
    """적응형 Rate Limiter - API 응답에 따라 동적으로 호출 속도 조절"""
    
    def __init__(self, initial_delay=1.0, min_delay=0.5, max_delay=10.0):
        self.current_delay = initial_delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.success_count = 0
        self.error_count = 0
        self.last_call_time = 0
        
    def on_success(self):
        """API 호출 성공 시 호출 - 점진적으로 속도 증가"""
        self.success_count += 1
        self.error_count = 0
        
        # 연속 성공 시 딜레이 감소 (최소값까지)
        if self.success_count >= 3:
            self.current_delay = max(self.min_delay, self.current_delay * 0.9)
            self.success_count = 0
            
    def on_rate_limit(self, retry_after=None):
        """429 Rate Limit 에러 시 호출"""
        self.error_count += 1
        self.success_count = 0
        
        if retry_after:
            # 서버에서 지정한 대기 시간 적용
            self.current_delay = min(float(retry_after), self.max_delay)
        else:
            # 딜레이 2배 증가
            self.current_delay = min(self.current_delay * 2, self.max_delay)
            
        logger.warning(f"Rate Limit 적응: 딜레이 {self.current_delay:.2f}초로 증가")
    
    def on_error(self):
        """일반적인 에러 시 호출"""
        self.error_count += 1
        if self.error_count >= 2:
            # 에러가 반복되면 딜레이 증가
            self.current_delay = min(self.current_delay * 1.5, self.max_delay)
            
    def wait(self):
        """API 호출 전 대기"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        if time_since_last < self.current_delay:
            wait_time = self.current_delay - time_since_last
            logger.debug(f"적응형 Rate Limit: {wait_time:.2f}초 대기")
            time.sleep(wait_time)
            
        self.last_call_time = time.time()


# 전역 적응형 Rate Limiter 인스턴스
adaptive_rate_limiter = AdaptiveRateLimiter()


def exponential_backoff_retry(func, max_retries=3, base_delay=1.0, max_delay=60.0, backoff_factor=2.0):
    """
    지수 백오프를 사용한 적응형 재시도
    
    Args:
        func: 실행할 함수
        max_retries: 최대 재시도 횟수
        base_delay: 기본 지연 시간 (초)
        max_delay: 최대 지연 시간 (초)
        backoff_factor: 백오프 배수
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:  # 마지막 시도
                raise e
            
            # 지수 백오프 계산 (지터 추가)
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)  # 10% 지터
            total_delay = delay + jitter
            
            logger.warning(f"재시도 {attempt + 1}/{max_retries} - {total_delay:.2f}초 후 재시도: {e}")
            time.sleep(total_delay)
    
    return None


class PowerLinkDataAdapter:
    """파워링크 분석을 위한 데이터 어댑터"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def is_api_configured(self) -> bool:
        """API 설정 확인"""
        try:
            # foundation의 config_manager를 통해 설정 확인
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            return api_config.is_searchad_valid()
        except Exception as e:
            logger.error(f"API 설정 확인 실패: {e}")
            return False
    
    def get_keyword_basic_data(self, keyword: str) -> Optional[Tuple[int, float, float, float, float]]:
        """
        기본 키워드 데이터 조회 (월검색량, 클릭수, 클릭률)
        
        Returns:
            (월검색량, PC클릭수, PC클릭률, 모바일클릭수, 모바일클릭률) 또는 None
        """
        if not self.is_api_configured():
            logger.error("네이버 검색광고 API가 설정되지 않았습니다.")
            return None
        
        def _get_keyword_data():
            # 적응형 Rate Limiting 적용
            adaptive_rate_limiter.wait()
            
            try:
                # vendors의 keyword_client 사용 (필요할 때마다 가져오기)
                keyword_client = get_keyword_tool_client()
                response_data = keyword_client.get_keyword_ideas([keyword], show_detail=True)
                
                # 성공 시 Rate Limiter 업데이트
                adaptive_rate_limiter.on_success()
                
                keyword_list = response_data.get('keywordList', [])
                for item in keyword_list:
                    if item.get('relKeyword') == keyword:
                        # PC & 모바일 검색량 처리
                        pc_search_volume = self._parse_search_volume(item.get('monthlyPcQcCnt'))
                        mobile_search_volume = self._parse_search_volume(item.get('monthlyMobileQcCnt'))
                        
                        # PC & 모바일 월평균 클릭수
                        pc_clicks = float(item.get('monthlyAvePcClkCnt', 0))
                        mobile_clicks = float(item.get('monthlyAveMobileClkCnt', 0))
                        
                        # 클릭률
                        pc_ctr = float(item.get('monthlyAvePcCtr', 0))
                        mobile_ctr = float(item.get('monthlyAveMobileCtr', 0))
                        
                        # PC/Mobile 검색량을 분리해서 반환 (더 정확한 순위 계산을 위해)
                        return (pc_search_volume, mobile_search_volume, pc_clicks, pc_ctr, mobile_clicks, mobile_ctr)
                
                # 키워드를 찾지 못한 경우
                return None
                
            except Exception as e:
                # API 에러 타입에 따른 Rate Limiter 업데이트
                error_msg = str(e).lower()
                if '429' in error_msg or 'rate limit' in error_msg:
                    # Retry-After 헤더 파싱 시도
                    retry_after = None
                    if hasattr(e, 'response') and e.response:
                        retry_after = e.response.headers.get('Retry-After')
                    adaptive_rate_limiter.on_rate_limit(retry_after)
                else:
                    adaptive_rate_limiter.on_error()
                raise
        
        # 적응형 재시도 적용
        try:
            return exponential_backoff_retry(_get_keyword_data, max_retries=3, base_delay=1.0)
        except Exception as e:
            logger.error(f"키워드 데이터 조회 최종 실패: {e}")
            return None
        
        return None
    
    def _parse_search_volume(self, volume_str: str) -> int:
        """검색량 문자열 파싱 ("< 10" 처리)"""
        if not volume_str or volume_str == "< 10":
            return 0
        try:
            return int(volume_str)
        except (ValueError, TypeError):
            return 0
    
    def get_bid_positions_for_both_devices(self, keyword: str) -> Tuple[List[BidPosition], List[BidPosition]]:
        """
        PC/모바일 입찰가를 각각 조회 (실제 API 테스트 확인: 통합 요청 불가, 따로 요청 필수)
        
        API 테스트 결과:
        - PC만 요청: 성공 ✅
        - 모바일만 요청: 성공 ✅  
        - device="ALL": 400 에러 ❌
        - device 없음: 400 에러 ❌
        
        Returns:
            (PC 입찰가 리스트, 모바일 입찰가 리스트)
        """
        if not self.is_api_configured():
            logger.error("네이버 검색광고 API가 설정되지 않았습니다.")
            return [], []
        
        # 병렬 처리를 위해 각각 조회 (순차 처리보다 빠름)
        pc_bids = self._get_bid_positions_for_device(keyword, "PC", POWERLINK_CONFIG["pc_positions"])
        mobile_bids = self._get_bid_positions_for_device(keyword, "MOBILE", POWERLINK_CONFIG["mobile_positions"])
        
        return pc_bids, mobile_bids
    
    def _get_bid_positions_for_device(self, keyword: str, device: str, max_positions: int) -> List[BidPosition]:
        """특정 디바이스의 입찰가 조회 - vendors 레이어를 통해 수행"""
        def _get_bid_data():
            # 적응형 Rate Limiting 적용
            adaptive_rate_limiter.wait()
            
            try:
                from src.vendors.naver.searchad.base_client import NaverKeywordToolClient
                
                # 베이스 클라이언트 인스턴스 생성 및 입찰가 조회
                client = NaverKeywordToolClient()
                positions_list = list(range(1, max_positions + 1))
                response_data = client.get_bid_estimates(keyword, device, positions_list)
                
                # 성공 시 Rate Limiter 업데이트
                adaptive_rate_limiter.on_success()
                
                if not response_data:
                    raise Exception(f"{device} 입찰가 조회 실패: 응답 데이터 없음")
                    
                bid_positions = []
                estimates = response_data.get('estimate', [])
                for estimate in estimates:
                    bid_positions.append(BidPosition(
                        position=estimate['position'],
                        bid_price=estimate['bid']
                    ))
                return bid_positions
                
            except Exception as e:
                # API 에러 타입에 따른 Rate Limiter 업데이트
                error_msg = str(e).lower()
                if '429' in error_msg or 'rate limit' in error_msg:
                    retry_after = None
                    if hasattr(e, 'response') and e.response:
                        retry_after = e.response.headers.get('Retry-After')
                    adaptive_rate_limiter.on_rate_limit(retry_after)
                else:
                    adaptive_rate_limiter.on_error()
                raise
        
        # 적응형 재시도 적용
        try:
            return exponential_backoff_retry(_get_bid_data, max_retries=3, base_delay=1.0)
        except Exception as e:
            logger.error(f"{device} 입찰가 조회 최종 실패: {e}")
            return []
    
    def get_page_exposure_positions(self, keyword: str, device_type: str, browser_context: Optional[BrowserContext] = None) -> Optional[Tuple[int, int]]:
        """
        1페이지 노출 위치 크롤링
        
        Args:
            keyword: 키워드
            device_type: 'pc' 또는 'mobile'
            browser_context: 기존 브라우저 컨텍스트 (필수 - worker에서 전달)
            
        Returns:
            (파워링크 위치 인덱스, 파워링크 광고 개수) 또는 None
        """
        # browser_context가 없으면 기본값 반환
        if not browser_context:
            logger.warning(f"{device_type.upper()} 크롤링 - 브라우저 컨텍스트가 없어 기본값 사용")
            return (8, 8) if device_type == 'pc' else (4, 4)
        
        max_retries = POWERLINK_CONFIG["max_retries"]
        
        for attempt in range(max_retries + 1):
            try:
                result = self._perform_search_with_context(keyword, device_type, browser_context)
                
                if result is not None:
                    return result
                
                # 실패한 경우 재시도
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2  # 2초, 4초 대기
                    logger.warning(f"{device_type.upper()} 크롤링 실패 - {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"{device_type.upper()} 크롤링 최대 재시도 횟수 초과 - 기본값 사용")
                    return (8, 8) if device_type == 'pc' else (4, 4)
                    
            except Exception as e:
                logger.error(f"{device_type.upper()} 크롤링 재시도 중 오류: {str(e)}")
                if attempt == max_retries:
                    return (8, 8) if device_type == 'pc' else (4, 4)
                continue
        
        # 모든 시도 실패 시 기본값
        return (8, 8) if device_type == 'pc' else (4, 4)
    
    def _perform_search_with_context(self, keyword: str, device_type: str, browser_context: BrowserContext) -> Optional[Tuple[int, int]]:
        """기존 브라우저 컨텍스트를 사용한 검색 크롤링"""
        page = None
        try:
            # 기존 브라우저 컨텍스트에서 새 페이지 생성
            page = browser_context.new_page()
            
            if device_type == 'pc':
                search_url = f"https://search.naver.com/search.naver?query={keyword}"
            else:  # mobile
                search_url = f"https://m.search.naver.com/search.naver?query={keyword}"
                
            page.goto(search_url, wait_until='networkidle')
            page.wait_for_timeout(3000)  # 3초 대기
            
            return self._extract_powerlink_info(page, keyword, device_type)
            
        except Exception as e:
            logger.error(f"{device_type.upper()} 크롤링 오류 (브라우저 재사용): {str(e)}")
            return None
        finally:
            if page:
                try:
                    page.close()
                except:
                    pass
    
    
    def _extract_powerlink_info(self, page, keyword: str, device_type: str) -> Optional[Tuple[int, int]]:
        """페이지에서 파워링크 정보 추출"""
        try:
            # 파워링크 위치 찾기
            title_wrap_divs = page.query_selector_all(".title_wrap")
            position_index = 0
            
            for idx, div in enumerate(title_wrap_divs, start=1):
                try:
                    h2_tag = div.query_selector("h2")
                    if h2_tag:
                        h2_text = h2_tag.inner_text()
                        if device_type == 'pc':
                            if "파워링크" in h2_text:
                                position_index = idx
                                break
                        else:  # mobile
                            if keyword in h2_text:
                                position_index = idx
                                break
                except:
                    continue
            
            # 파워링크 광고 개수 찾기
            if device_type == 'pc':
                power_link_elements = page.query_selector_all(".title_url_area")
            else:  # mobile
                power_link_elements = page.query_selector_all(".url_area")
            
            power_link_count = len(power_link_elements)
            
            return position_index, power_link_count
            
        except Exception as e:
            logger.error(f"파워링크 정보 추출 오류: {str(e)}")
            return None
    
    def calculate_min_exposure_bid(self, bid_positions: List[BidPosition], position: int) -> int:
        """
        현실적인 최소노출가격 계산 (70원 API 오류 감지)
        """
        if not bid_positions or position <= 0:
            return 0
        if position > len(bid_positions):
            return bid_positions[-1].bid_price
        
        # 1페이지 노출 위치까지만 고려
        relevant_positions = bid_positions[:position]
        if not relevant_positions:
            return 0
        
        # 마지막 노출 위치 가격
        last_position_price = relevant_positions[-1].bid_price
        
        # 마지막 위치가 70원이고, 위에 정상 가격이 있는 경우 API 오류 감지
        if last_position_price == NAVER_MIN_BID and len(relevant_positions) > 1:
            # 위 순위들 중 70원이 아닌 가격들 확인
            non_min_prices = [pos.bid_price for pos in relevant_positions[:-1] 
                             if pos.bid_price > NAVER_MIN_BID]
            
            if non_min_prices:
                # 바로 위 순위 가격 확인
                second_last_price = relevant_positions[-2].bid_price
                
                # 바로 위 순위와 10배 이상 차이나면 API 오류로 판단
                if second_last_price / NAVER_MIN_BID > 10:
                    return second_last_price
                
                # 연속된 70원이 많으면 (절반 이상) 진짜 저경쟁 키워드
                min_bid_count = sum(1 for pos in relevant_positions 
                                  if pos.bid_price == NAVER_MIN_BID)
                
                if min_bid_count >= len(relevant_positions) // 2:
                    return NAVER_MIN_BID  # 진짜 저경쟁 키워드
                else:
                    return second_last_price  # API 오류 추정
        
        # 정상 경우는 해당 위치 가격 그대로 반환
        return last_position_price


