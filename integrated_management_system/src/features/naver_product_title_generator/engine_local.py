"""
네이버 상품명 생성기 로컬 엔진
순수 함수 기반 핵심 알고리즘 (I/O 없음)
"""
from typing import List, Dict, Any
import re
import math
from collections import Counter

from .models import KeywordBasicData, GeneratedTitle


def extract_keywords_from_product_name(product_name: str) -> List[str]:
    """제품명에서 키워드 추출 (앞으로 사용할 함수)"""
    # 한글, 영어, 숫자만 남기고 정리
    cleaned = re.sub(r'[^\w\s가-힣]', ' ', product_name)
    
    keywords = set()
    words = cleaned.split()
    
    # 1. 개별 단어들
    for word in words:
        if len(word) >= 2:
            keywords.add(word.lower())
    
    # 2. 2글자 조합
    if len(words) > 1:
        for i in range(len(words) - 1):
            combined = f"{words[i]} {words[i+1]}".lower()
            keywords.add(combined)
    
    # 3. 전체 조합
    if len(words) <= 3:  # 3단어 이하일 때만
        keywords.add(product_name.lower())
    
    return list(keywords)


def calculate_seo_score(title: str, keywords: List[str]) -> float:
    """SEO 점수 계산 (앞으로 사용할 함수)"""
    score = 50.0  # 기본 점수
    
    # 키워드 포함도
    for keyword in keywords:
        if keyword.lower() in title.lower():
            score += 10
    
    # 길이 적정성
    length = len(title)
    if 20 <= length <= 40:
        score += 20
    elif length < 20:
        score -= 10
    elif length > 50:
        score -= 15
    
    return min(score, 100.0)


def generate_title_variations(keywords: List[str], original_product: str) -> List[str]:
    """키워드 조합으로 상품명 변형 생성 (앞으로 구현할 함수)"""
    variations = set()
    
    # 기본 패턴들
    patterns = [
        "{product} {keyword}",
        "{keyword} {product}",
        "{product} {keyword} 추천",
        "{keyword} 전문 {product}",
        "인기 {keyword} {product}"
    ]
    
    # 각 키워드와 패턴 조합
    for keyword in keywords[:5]:  # 상위 5개만
        for pattern in patterns:
            title = pattern.format(product=original_product, keyword=keyword)
            if len(title) <= 50:  # 50자 제한
                variations.add(title)
    
    return list(variations)[:10]  # 최대 10개