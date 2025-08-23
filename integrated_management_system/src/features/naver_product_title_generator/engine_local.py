"""
네이버 상품명 생성기 로컬 엔진
순수 함수 기반 핵심 알고리즘 (I/O 없음)
"""
from typing import List, Dict, Any, Optional
import re
import math
from collections import Counter

from .models import KeywordBasicData, GeneratedTitle


# AI 프롬프트 시스템 (공용 - 모든 프롬프트에 자동 추가)
SYSTEM_PROMPT = """당신은 네이버 쇼핑 상품명 분석 전문가입니다.  
아래 상품명을 분석해, 사람들이 실제 검색할 가능성이 높은 키워드를 생성하세요.  
결과는 네이버 월간 검색량 API 비교용이며, 모든 카테고리에 공용으로 사용 가능해야 합니다."""

# 기본 프롬프트 내용 (사용자에게 표시용)
DEFAULT_AI_PROMPT = """규칙

1. 브랜드명 제거  
- 모든 브랜드 삭제

2. 규격·단위 제거  
- g, kg, ml, 개, 개입, 박스, 세트, %, p, S, M, L, 소형, 중형, 대형 등 제외.  

3. 불필요 단어 제거  
- 남성, 여성, 인기, 특가, 신상, 할인, 무료배송, 멋진, 이쁜, 세련된과 같은 주관적인 단어 제외.  

4. 형태소 분류  
- ① 브랜드명  
- ② 카테고리명  
- ③ 형태  
- ④ 주원료  
- ⑤ 제품 고유명사(시리즈/모델명)  

키워드 생성 규칙

싱글(single_keywords)  
-사용자가 검색할 것 같은 제품 고유명사, 카테고리명

빅람(bigram_keywords)  
- 위 5요소 중 2개 조합.  
- 순서: 대상 → 속성 → 형태 → 주원료/고유명사 우선.  
- 가능한 한 많이 생성, 의미 명확·검색 가능성 높으면 빈도 무관 포함.  

트리그램(trigram_keywords)  
- 위 5요소 중 3개 조합, 빅람 충분 시에만.  
- 순서 동일, 의미 명확·검색 가능성 높을 때만.  

공통  
- 실제 한국어 검색 어순 적용.  
- 붙임·띄어쓰기는 동일 키워드로 간주, 한 형태만 출력.  
- 조건 미달 시 개수 확보 위해 규칙 완화 가능.  

출력 형식  
- 키워드만 쉼표(,)로 구분.  
- single + bigram + trigram 합산 200개 이상.  
- 중복 제거(붙임·띄어쓰기 동일 키워드도 중복 제거).  
- 설명·기타 문장 금지."""


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


def build_ai_prompt(product_titles: List[str], custom_prompt: Optional[str] = None) -> str:
    """
    AI 분석용 프롬프트 생성
    
    Args:
        product_titles: 분석할 상품명 리스트
        custom_prompt: 사용자 정의 프롬프트 (None이면 기본 프롬프트 사용)
        
    Returns:
        str: 완성된 프롬프트
    """
    # 상품명 목록 텍스트 생성
    titles_text = "\n".join([f"- {title}" for title in product_titles])
    
    if custom_prompt:
        # 공용 시스템 프롬프트 + 사용자 정의 프롬프트 + 상품명 목록
        return f"{SYSTEM_PROMPT}\n\n{custom_prompt}\n\n상품명 목록:\n{titles_text}"
    else:
        # 공용 시스템 프롬프트 + 기본 프롬프트 + 상품명 목록
        return f"{SYSTEM_PROMPT}\n\n{DEFAULT_AI_PROMPT}\n\n상품명 목록:\n{titles_text}"


def parse_ai_keywords_response(ai_response: str) -> List[str]:
    """
    AI 응답에서 키워드 추출
    
    Args:
        ai_response: AI가 반환한 텍스트
        
    Returns:
        List[str]: 추출된 키워드 리스트
    """
    # 쉼표로 구분된 키워드 추출
    keywords = []
    
    # 줄바꿈으로 나누고 각 줄에서 키워드 추출
    lines = ai_response.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
            
        # 쉼표로 구분
        if ',' in line:
            parts = line.split(',')
            for part in parts:
                keyword = part.strip()
                if keyword and len(keyword) >= 2:
                    keywords.append(keyword)
        else:
            # 쉼표가 없으면 전체를 하나의 키워드로
            if len(line) >= 2:
                keywords.append(line)
    
    # 중복 제거 (순서 유지)
    unique_keywords = []
    seen = set()
    
    for keyword in keywords:
        keyword_lower = keyword.lower().strip()
        if keyword_lower not in seen:
            seen.add(keyword_lower)
            unique_keywords.append(keyword.strip())
    
    return unique_keywords


def filter_keywords_by_search_volume(keywords: List[KeywordBasicData], min_volume: int = 100) -> List[KeywordBasicData]:
    """
    검색량 기준으로 키워드 필터링
    
    Args:
        keywords: 키워드 데이터 리스트
        min_volume: 최소 월간 검색량
        
    Returns:
        List[KeywordBasicData]: 필터링된 키워드 리스트
    """
    return [kw for kw in keywords if kw.search_volume >= min_volume]


def calculate_keyword_score(keyword_data: KeywordBasicData) -> float:
    """
    키워드 점수 계산 (검색량 + 경쟁도 고려)
    
    Args:
        keyword_data: 키워드 데이터
        
    Returns:
        float: 키워드 점수 (0-100)
    """
    # 기본 점수는 검색량 기반
    volume_score = min(keyword_data.search_volume / 1000 * 50, 70)  # 최대 70점
    
    # 경쟁도 보너스 (낮을수록 좋음)
    competition_bonus = 0
    if keyword_data.competition == "낮음":
        competition_bonus = 20
    elif keyword_data.competition == "보통":
        competition_bonus = 10
    
    # 키워드 길이 보너스 (2-4글자가 적정)
    length_bonus = 0
    length = len(keyword_data.keyword)
    if 2 <= length <= 4:
        length_bonus = 10
    elif length == 5:
        length_bonus = 5
    
    total_score = volume_score + competition_bonus + length_bonus
    return min(total_score, 100.0)