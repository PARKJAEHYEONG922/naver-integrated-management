"""
통합 텍스트 처리 및 검증 유틸리티 (CLAUDE.md 구조)
키워드 파싱/정규화, 카테고리 처리, URL/상품ID/파일 검증 등 모든 모듈에서 사용하는 텍스트 관련 기능
validators.py 기능 통합 완료 - 중복 제거 및 단일 책임 원칙 적용
"""
import re
import os
from typing import List, Set, Tuple, Optional, Dict, Any
from urllib.parse import urlparse
from pathlib import Path
from src.foundation.logging import get_logger

logger = get_logger("toolbox.text_utils")


def parse_keywords(text: str) -> List[str]:
    """텍스트에서 키워드 파싱 (keyword_analysis와의 호환성)"""
    return TextProcessor.parse_keywords_from_text(text)


def filter_unique_keywords_with_skipped(keywords: List[str]) -> Tuple[List[str], List[str]]:
    """중복 키워드 필터링 및 건너뛴 목록 반환"""
    unique_keywords = []
    skipped_keywords = []
    seen = set()
    
    for keyword in keywords:
        clean_keyword = keyword.strip().lower()
        if clean_keyword and clean_keyword not in seen:
            unique_keywords.append(keyword.strip())
            seen.add(clean_keyword)
        elif keyword.strip():
            skipped_keywords.append(keyword.strip())
    
    return unique_keywords, skipped_keywords


class TextProcessor:
    """텍스트 처리기"""
    
    @staticmethod
    def parse_keywords_from_text(text: str) -> List[str]:
        """
        텍스트에서 키워드 목록 파싱 (엔터, 쉼표 구분 지원)
        
        Args:
            text: 입력 텍스트
        
        Returns:
            List[str]: 파싱된 키워드 목록
        """
        if not text.strip():
            return []
        
        keywords = []
        
        # 개행문자와 쉼표로 분리
        text = text.replace(',', '\n').replace('，', '\n')  # 영문/한글 쉼표 모두 지원
        
        for line in text.strip().split('\n'):
            line = line.strip()
            if line:
                # 세미콜론이나 기타 구분자도 처리
                for keyword in line.replace(';', '\n').replace('|', '\n').split('\n'):
                    keyword = keyword.strip()
                    if keyword:
                        keywords.append(keyword)
        
        logger.info(f"텍스트에서 {len(keywords)}개 키워드 파싱 완료")
        return keywords
    
    @staticmethod
    def clean_keyword(keyword: str) -> str:
        """
        키워드 정리 (공백 제거, 대소문자 통일 등)
        
        Args:
            keyword: 원본 키워드
        
        Returns:
            str: 정리된 키워드
        """
        if not keyword:
            return ""
        
        # 앞뒤 공백 제거
        cleaned = keyword.strip()
        
        # 연속된 공백을 하나로 통일
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    @staticmethod
    def normalize_keyword(keyword: str) -> str:
        """
        키워드 정규화 (비교용)
        
        Args:
            keyword: 원본 키워드
        
        Returns:
            str: 정규화된 키워드
        """
        if not keyword:
            return ""
        
        # 공백 제거 + 대문자 변환 (PowerLink 방식과 호환)
        normalized = keyword.strip().replace(' ', '').upper()
        return normalized
    
    @staticmethod
    def filter_unique_keywords(keywords: List[str], existing_keywords: Set[str] = None) -> List[str]:
        """
        중복 제거 및 기존 키워드 필터링
        
        Args:
            keywords: 키워드 목록
            existing_keywords: 기존 키워드 집합
        
        Returns:
            List[str]: 중복 제거된 키워드 목록
        """
        if existing_keywords is None:
            existing_keywords = set()
        
        unique_keywords = []
        seen = set()
        
        for keyword in keywords:
            # 정리 및 정규화
            cleaned = TextProcessor.clean_keyword(keyword)
            normalized = TextProcessor.normalize_keyword(cleaned)
            
            if normalized and normalized not in seen and normalized not in existing_keywords:
                unique_keywords.append(cleaned)  # 원본 형태로 저장
                seen.add(normalized)
        
        logger.debug(f"중복 제거 완료: {len(keywords)} -> {len(unique_keywords)}개")
        return unique_keywords
    
    @staticmethod
    def filter_unique_keywords_with_skipped(keywords: List[str], 
                                          existing_keywords: Set[str] = None) -> Tuple[List[str], List[str]]:
        """
        중복 제거 및 기존 키워드 필터링 (건너뛴 키워드 목록도 반환)
        
        Args:
            keywords: 키워드 목록
            existing_keywords: 기존 키워드 집합
        
        Returns:
            Tuple[List[str], List[str]]: (고유 키워드, 건너뛴 키워드)
        """
        if existing_keywords is None:
            existing_keywords = set()
        
        unique_keywords = []
        skipped_keywords = []
        seen = set()
        
        for keyword in keywords:
            # 정리 및 정규화
            cleaned = TextProcessor.clean_keyword(keyword)
            normalized = TextProcessor.normalize_keyword(cleaned)
            
            if normalized:
                if normalized in existing_keywords:
                    # 이미 검색된 키워드
                    skipped_keywords.append(cleaned)
                elif normalized not in seen:
                    # 새로운 키워드
                    unique_keywords.append(cleaned)
                    seen.add(normalized)
        
        logger.info(f"중복 제거 완료: {len(keywords)} -> {len(unique_keywords)}개 (건너뛴: {len(skipped_keywords)}개)")
        return unique_keywords, skipped_keywords
    
    @staticmethod
    def validate_keyword(keyword: str) -> bool:
        """키워드 유효성 검사"""
        if not keyword or not keyword.strip():
            return False
        
        cleaned = TextProcessor.clean_keyword(keyword)
        
        # 최소/최대 길이 검사
        if len(cleaned) < 1 or len(cleaned) > 100:
            return False
        
        # 특수문자만으로 이루어진 키워드 제외
        if not any(c.isalnum() for c in cleaned):
            return False
        
        return True
    
    @staticmethod
    def extract_keywords_from_mixed_text(text: str) -> List[str]:
        """혼합된 텍스트에서 키워드 추출 (더 유연한 파싱)"""
        if not text.strip():
            return []
        
        # 다양한 구분자로 분리
        separators = ['\n', ',', '，', ';', '|', '\t']
        
        # 모든 구분자를 개행문자로 통일
        for sep in separators:
            text = text.replace(sep, '\n')
        
        keywords = []
        for line in text.split('\n'):
            # 공백으로도 분리 시도 (단어 단위)
            words = line.split()
            for word in words:
                word = word.strip()
                if word and TextProcessor.validate_keyword(word):
                    keywords.append(word)
        
        return keywords
    
    @staticmethod
    def split_keywords_by_batch_size(keywords: List[str], batch_size: int = 100) -> List[List[str]]:
        """키워드를 배치 크기별로 분할"""
        batches = []
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            batches.append(batch)
        return batches


class CategoryProcessor:
    """카테고리 처리기"""
    
    @staticmethod
    def extract_last_category(category_path: str, separator: str = ' > ') -> str:
        """
        카테고리 경로에서 마지막 카테고리 추출
        
        Args:
            category_path: 카테고리 경로 (예: "가전 > 컴퓨터 > 노트북")
            separator: 구분자
        
        Returns:
            str: 마지막 카테고리
        """
        if not category_path:
            return ""
        
        categories = category_path.split(separator)
        return categories[-1].strip() if categories else ""
    
    @staticmethod
    def build_category_path(categories: List[str], separator: str = ' > ') -> str:
        """
        카테고리 목록을 경로로 결합
        
        Args:
            categories: 카테고리 목록
            separator: 구분자
        
        Returns:
            str: 카테고리 경로
        """
        if not categories:
            return ""
        
        # 빈 카테고리 제거
        valid_categories = [cat.strip() for cat in categories if cat.strip()]
        return separator.join(valid_categories)
    
    @staticmethod
    def calculate_category_similarity(category1: str, category2: str) -> float:
        """
        두 카테고리 간 유사도 계산 (간단한 문자열 매칭)
        
        Args:
            category1: 첫 번째 카테고리
            category2: 두 번째 카테고리
        
        Returns:
            float: 유사도 (0.0 ~ 1.0)
        """
        if not category1 or not category2:
            return 0.0
        
        # 대소문자 통일 및 공백 제거
        cat1 = category1.lower().replace(' ', '')
        cat2 = category2.lower().replace(' ', '')
        
        if cat1 == cat2:
            return 1.0
        
        # 포함 관계 확인
        if cat1 in cat2 or cat2 in cat1:
            return 0.7
        
        # 간단한 문자 매칭
        common_chars = set(cat1) & set(cat2)
        total_chars = set(cat1) | set(cat2)
        
        if total_chars:
            return len(common_chars) / len(total_chars)
        
        return 0.0


# ================================
# 편의 함수들 (하위 호환성)
# ================================

def parse_keywords_from_text(text: str) -> List[str]:
    """키워드 파싱 편의 함수"""
    return TextProcessor.parse_keywords_from_text(text)


def clean_keyword(keyword: str) -> str:
    """키워드 정리 편의 함수"""
    return TextProcessor.clean_keyword(keyword)


def normalize_keyword(keyword: str) -> str:
    """키워드 정규화 편의 함수"""
    return TextProcessor.normalize_keyword(keyword)


def filter_unique_keywords(keywords: List[str], existing_keywords: Set[str] = None) -> List[str]:
    """중복 제거 편의 함수"""
    return TextProcessor.filter_unique_keywords(keywords, existing_keywords)


def filter_unique_keywords_with_skipped(keywords: List[str], 
                                      existing_keywords: Set[str] = None) -> Tuple[List[str], List[str]]:
    """중복 제거 및 기존 키워드 필터링 (건너뛴 키워드 목록도 반환)"""
    return TextProcessor.filter_unique_keywords_with_skipped(keywords, existing_keywords)


def validate_keyword(keyword: str) -> bool:
    """키워드 유효성 검사 편의 함수"""
    return TextProcessor.validate_keyword(keyword)


def clean_keywords(keywords: List[str]) -> List[str]:
    """키워드 목록 정리 편의 함수"""
    return [TextProcessor.clean_keyword(kw) for kw in keywords if kw.strip()]


def filter_valid_keywords(keywords: List[str]) -> List[str]:
    """유효한 키워드만 필터링"""
    return [keyword for keyword in keywords if validate_keyword(keyword)]


def get_last_category(category_path: str) -> str:
    """마지막 카테고리 추출 편의 함수"""
    return CategoryProcessor.extract_last_category(category_path)


def split_keywords_by_batch_size(keywords: List[str], batch_size: int = 100) -> List[List[str]]:
    """키워드를 배치 크기별로 분할"""
    return TextProcessor.split_keywords_by_batch_size(keywords, batch_size)


# ================================
# 하위 호환성 함수들 (필요시에만 유지)
# ================================

def process_keywords(keywords: List[str], existing_keywords: set = None) -> List[str]:
    """PowerLink 호환용 키워드 처리 함수"""
    if existing_keywords is None:
        existing_keywords = set()
    
    return filter_unique_keywords(keywords, existing_keywords)


def filter_duplicates(keywords: List[str], existing: Set[str] = None) -> List[str]:
    """중복 제거 편의 함수 (하위 호환성)"""
    return filter_unique_keywords(keywords, existing)


def format_keyword_for_display(keyword: str) -> str:
    """화면 표시용 키워드 포맷팅"""
    if not keyword:
        return ""
    
    return keyword.strip()


# === 간단한 검증 함수들 (실제 사용되는 것들만) ===

def validate_url(url: str) -> bool:
    """URL 유효성 검사"""
    if not url:
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def validate_naver_url(url: str) -> bool:
    """네이버 쇼핑 URL 검증"""
    if not validate_url(url):
        return False
    
    naver_domains = [
        'shopping.naver.com',
        'smartstore.naver.com', 
        'brand.naver.com'
    ]
    
    parsed = urlparse(url)
    return any(domain in parsed.netloc for domain in naver_domains)


def extract_product_id(url: str) -> Optional[str]:
    """네이버 쇼핑 URL에서 상품 ID 추출"""
    if not validate_naver_url(url):
        return None
    
    patterns = [
        r'https?://shopping\.naver\.com/catalog/(\d+)',
        r'https?://smartstore\.naver\.com/[^/]+/products/(\d+)',
        r'https?://brand\.naver\.com/[^/]+/products/(\d+)',
        r'/products/(\d+)',
        r'nvMid=(\d+)',
        r'productId=(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def validate_product_id(product_id: str) -> bool:
    """상품 ID 유효성 검사"""
    if not product_id or not isinstance(product_id, str):
        return False
    return bool(re.match(r'^\d{5,}$', product_id.strip()))


def validate_excel_file(filename: str) -> Tuple[bool, str]:
    """엑셀 파일명 검증"""
    if not filename or not isinstance(filename, str):
        return False, "파일명이 없습니다"
    
    # 기본 안전성 검사
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    if any(char in filename for char in forbidden_chars):
        return False, "유효하지 않은 파일명입니다"
    
    # 엑셀 확장자 확인
    valid_extensions = ['.xlsx', '.xls']
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        return False, "엑셀 파일 확장자(.xlsx, .xls)가 필요합니다"
    
    return True, "유효한 엑셀 파일명입니다"


# === 키워드 파싱/검증 편의 함수들 ===
def parse_keywords(text: str) -> List[str]:
    """키워드 텍스트 파싱 편의 함수"""
    return TextProcessor.parse_keywords_from_text(text)


def clean_keyword(keyword: str) -> str:
    """키워드 정리 편의 함수"""
    return TextProcessor.clean_keyword(keyword)


def normalize_keyword(keyword: str) -> str:
    """키워드 정규화 편의 함수"""
    return TextProcessor.normalize_keyword(keyword)