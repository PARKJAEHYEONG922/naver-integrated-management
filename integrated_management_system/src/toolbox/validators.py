"""
데이터 검증 (URL, API키 등)
입력 데이터 유효성 검사 기능
"""
import re
import requests
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse

from src.foundation.logging import get_logger


logger = get_logger("toolbox.validators")


class URLValidator:
    """URL 검증기"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        URL 유효성 검사
        
        Args:
            url: 검사할 URL
        
        Returns:
            bool: 유효 여부
        """
        if not url:
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def is_naver_shopping_url(url: str) -> bool:
        """
        네이버 쇼핑 URL 검증
        
        Args:
            url: 검사할 URL
        
        Returns:
            bool: 네이버 쇼핑 URL 여부
        """
        if not URLValidator.is_valid_url(url):
            return False
        
        naver_domains = [
            'shopping.naver.com',
            'smartstore.naver.com',
            'brand.naver.com'
        ]
        
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in naver_domains)
    
    @staticmethod
    def extract_product_id(url: str) -> Optional[str]:
        """
        네이버 쇼핑 URL에서 상품 ID 추출
        
        Args:
            url: 네이버 쇼핑 URL
        
        Returns:
            Optional[str]: 상품 ID
        """
        if not URLValidator.is_naver_shopping_url(url):
            return None
        
        # 상품 ID 패턴 매칭
        patterns = [
            r'/products/(\d+)',
            r'nvMid=(\d+)',
            r'productId=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None


class APIKeyValidator:
    """API 키 검증기"""
    
    @staticmethod
    def is_valid_format(api_key: str, key_type: str = "general") -> bool:
        """
        API 키 형식 검증
        
        Args:
            api_key: API 키
            key_type: 키 타입 (general, naver, openai, claude)
        
        Returns:
            bool: 형식 유효 여부
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # 공백 제거 후 검사
        api_key = api_key.strip()
        
        if key_type == "naver":
            # 네이버 API 키: 영문자와 숫자 조합, 최소 10자
            return bool(re.match(r'^[a-zA-Z0-9]{10,}$', api_key))
        elif key_type == "openai":
            # OpenAI API 키: sk-로 시작
            return api_key.startswith('sk-') and len(api_key) > 20
        elif key_type == "claude":
            # Claude API 키: sk-ant-로 시작
            return api_key.startswith('sk-ant-') and len(api_key) > 30
        else:
            # 일반적인 API 키: 최소 8자, 영문자와 숫자
            return len(api_key) >= 8 and bool(re.match(r'^[a-zA-Z0-9\-_]+$', api_key))
    
    @staticmethod
    def test_naver_shopping_api(client_id: str, client_secret: str) -> Tuple[bool, str]:
        """
        네이버 쇼핑 API 테스트
        
        Args:
            client_id: 클라이언트 ID
            client_secret: 클라이언트 시크릿
        
        Returns:
            Tuple[bool, str]: (성공 여부, 메시지)
        """
        if not client_id or not client_secret:
            return False, "클라이언트 ID와 시크릿이 필요합니다"
        
        try:
            headers = {
                'X-Naver-Client-Id': client_id,
                'X-Naver-Client-Secret': client_secret
            }
            
            # 간단한 테스트 요청
            response = requests.get(
                'https://openapi.naver.com/v1/search/shop.json',
                headers=headers,
                params={'query': '테스트', 'display': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "API 키가 유효합니다"
            elif response.status_code == 401:
                return False, "인증 실패: API 키를 확인해주세요"
            elif response.status_code == 403:
                return False, "권한 없음: API 사용 권한을 확인해주세요"
            else:
                return False, f"API 오류: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "API 호출 시간초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, f"예상치 못한 오류: {str(e)}"


class DataValidator:
    """데이터 검증기"""
    
    @staticmethod
    def is_valid_keyword(keyword: str) -> bool:
        """
        키워드 유효성 검사
        
        Args:
            keyword: 검사할 키워드
        
        Returns:
            bool: 유효 여부
        """
        if not keyword or not isinstance(keyword, str):
            return False
        
        keyword = keyword.strip()
        
        # 빈 문자열 확인
        if not keyword:
            return False
        
        # 길이 확인 (1~50자)
        if len(keyword) > 50:
            return False
        
        # 금지된 문자 확인
        forbidden_chars = ['<', '>', '"', "'", '&']
        if any(char in keyword for char in forbidden_chars):
            return False
        
        return True
    
    @staticmethod
    def validate_keywords(keywords: List[str]) -> Tuple[List[str], List[str]]:
        """
        키워드 목록 검증
        
        Args:
            keywords: 키워드 목록
        
        Returns:
            Tuple[List[str], List[str]]: (유효한 키워드, 무효한 키워드)
        """
        valid_keywords = []
        invalid_keywords = []
        
        for keyword in keywords:
            if DataValidator.is_valid_keyword(keyword):
                valid_keywords.append(keyword.strip())
            else:
                invalid_keywords.append(keyword)
        
        return valid_keywords, invalid_keywords
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        이메일 주소 유효성 검사
        
        Args:
            email: 이메일 주소
        
        Returns:
            bool: 유효 여부
        """
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """
        전화번호 유효성 검사 (한국 형식)
        
        Args:
            phone: 전화번호
        
        Returns:
            bool: 유효 여부
        """
        if not phone:
            return False
        
        # 숫자만 추출
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # 한국 전화번호 패턴
        patterns = [
            r'^010\d{8}$',  # 휴대폰
            r'^02\d{7,8}$',  # 서울 지역번호
            r'^0[3-6]\d{7,8}$',  # 기타 지역번호
            r'^070\d{8}$'  # 인터넷 전화
        ]
        
        return any(re.match(pattern, digits_only) for pattern in patterns)


class ConfigValidator:
    """설정 검증기"""
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        API 설정 검증
        
        Args:
            config: API 설정 딕셔너리
        
        Returns:
            Dict[str, List[str]]: 검증 결과 (오류 메시지 리스트)
        """
        errors = {
            'naver_shopping': [],
            'naver_searchad': [],
            'openai': [],
            'claude': []
        }
        
        # 네이버 쇼핑 API
        if not APIKeyValidator.is_valid_format(config.get('shopping_client_id', ''), 'naver'):
            errors['naver_shopping'].append('클라이언트 ID 형식이 올바르지 않습니다')
        
        if not APIKeyValidator.is_valid_format(config.get('shopping_client_secret', ''), 'naver'):
            errors['naver_shopping'].append('클라이언트 시크릿 형식이 올바르지 않습니다')
        
        # 네이버 검색광고 API
        required_searchad_fields = ['searchad_access_license', 'searchad_secret_key', 'searchad_customer_id']
        for field in required_searchad_fields:
            if not config.get(field):
                errors['naver_searchad'].append(f'{field}가 필요합니다')
        
        # OpenAI API
        openai_key = config.get('openai_api_key', '')
        if openai_key and not APIKeyValidator.is_valid_format(openai_key, 'openai'):
            errors['openai'].append('OpenAI API 키 형식이 올바르지 않습니다')
        
        # Claude API
        claude_key = config.get('claude_api_key', '')
        if claude_key and not APIKeyValidator.is_valid_format(claude_key, 'claude'):
            errors['claude'].append('Claude API 키 형식이 올바르지 않습니다')
        
        return errors


# 편의 함수들
def validate_url(url: str) -> bool:
    """URL 검증 편의 함수"""
    return URLValidator.is_valid_url(url)


def validate_naver_url(url: str) -> bool:
    """네이버 쇼핑 URL 검증 편의 함수"""
    return URLValidator.is_naver_shopping_url(url)


def validate_keyword(keyword: str) -> bool:
    """키워드 검증 편의 함수"""
    return DataValidator.is_valid_keyword(keyword)


def validate_keywords_list(keywords: List[str]) -> Tuple[List[str], List[str]]:
    """키워드 리스트 검증 편의 함수"""
    return DataValidator.validate_keywords(keywords)