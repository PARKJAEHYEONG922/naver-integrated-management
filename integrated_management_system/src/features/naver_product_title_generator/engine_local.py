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
결과는 네이버 월간 검색량 API 비교용이며, 모든 카테고리에 공용으로 사용 가능해야 합니다.

🔸 필수 출력 형식 (사용자 규칙과 상관없이 반드시 준수)
- 키워드만 쉼표(,)로 구분하여 한 줄에 출력
- 예시: 스마트폰, 갤럭시, 아이폰, 휴대폰, 모바일  
- 설명이나 기타 문장 절대 금지
- single + bigram + trigram 합산 300개 이상의 키워드 생성"""

# 기본 프롬프트 내용 (사용자에게 표시용)
DEFAULT_AI_PROMPT = """[규칙]

1. 브랜드명 제거  
- 모든 브랜드명 삭제
- 보통 상품명 앞에 단어가 브랜드명일 확률이 90% 이다.

2. 규격·단위 제거  
- g, kg, ml, 개, 개입, 박스, 세트, %, p, S, M, L, 소형, 중형, 대형 등 제외.  

3. 불필요 단어 제거  
- 인기, 특가, 신상, 할인, 무료배송, 멋진, 이쁜, 세련된, 가성비 와 같은 주관적인 단어, 제품을 꾸며주는 단어 제외.  

4. 인증/기관어(HACCP 등) 제거

5. 나머지 상품명 형태소 분류  
- 1.대상: 예) 강아지, 반려견, 애견, 남자, 남성, 여자, 여성 등...
- 2.효능/상황: 예)치석제거, 입냄새제거, 치아관리, 양치, 스케일링, 이갈이, 구강케어 등...  
- 3.형태  
- 4.주원료
- 5.제품 고유명사

6. 키워드 생성 규칙

1) 싱글(single_keywords)  
- 오직 특정상품명을 지칭하는 단어만 넣는다.
- 대상은 넣지 않는다. 예)강아지, 반려견, 애견, 남성, 여성 등... 

2) 빅람(bigram_keywords)  
- 위 5요소 중 2개 조합.  
- 대상+효능/상황, 대상+형태, 대상+제품고유명사, 형태+제품고유명사, 주원료+제품고유명사  
- 대상이 여러명일 경우 대상+제품고유명사 조합을 주력으로 생성
- 가능한 한 많이 생성  

3) 트리그램(trigram_keywords)  
- 위 5요소 중 3개 조합 
- 대상+효능/상황+제품고유명사, 대상+형태+제품고유명사, 대상+주원료+제품고유명사, 의미 명확 검색 가능성 높은 한국어 어순으로 조합도 포함  

7. 공통  
- 실제 한국어 검색 어순으로 어색하지 않는 검색어 적용.  
- 붙임·띄어쓰기는 동일 키워드로 간주, 한 형태만 출력.  
- 조건 미달 시 개수 확보 위해 규칙 완화 가능.  

8. 출력 형식  
- 키워드만 쉼표(,)로 구분.  
- single + bigram + trigram 합산 300개 이상.  
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
                # "+" 기호 제거 (예: "강아지+오래먹는+개껌" -> "강아지오래먹는개껌")
                keyword = keyword.replace('+', '')
                if keyword and len(keyword) >= 2:
                    keywords.append(keyword)
        else:
            # 쉼표가 없으면 전체를 하나의 키워드로
            line = line.replace('+', '')  # "+" 기호 제거
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
    filtered = [kw for kw in keywords if kw.search_volume >= min_volume]
    
    # 검색량 내림차순으로 정렬
    filtered.sort(key=lambda x: x.search_volume, reverse=True)
    
    return filtered


def filter_keywords_by_category(keywords: List[KeywordBasicData], target_category: str) -> List[KeywordBasicData]:
    """
    카테고리 기준으로 키워드 필터링 (1단계에서 선택한 카테고리와 매칭)
    
    Args:
        keywords: 필터링할 키워드 리스트
        target_category: 1단계에서 사용자가 선택한 카테고리
        
    Returns:
        List[KeywordBasicData]: 매칭되는 카테고리의 키워드 리스트
    """
    if not keywords or not target_category:
        return keywords
    
    # % 부분 제거
    target_clean = target_category.split('(')[0].strip() if '(' in target_category else target_category.strip()
    
    # 디버깅용 로그
    from src.foundation.logging import get_logger
    logger = get_logger("features.naver_product_title_generator.engine_local")
    logger.info(f"🎯 필터링 대상 카테고리: '{target_clean}'")
    
    filtered = []
    for kw in keywords:
        if not kw.category:
            logger.debug(f"  ❌ '{kw.keyword}' - 카테고리 없음")
            continue
            
        # 키워드 카테고리도 % 부분 제거
        kw_clean = kw.category.split('(')[0].strip() if '(' in kw.category else kw.category.strip()
        
        # 카테고리 매칭 로직 (원본 문자열로 비교)
        is_match = is_category_match(target_clean, kw_clean)
        logger.info(f"  {'✅' if is_match else '❌'} '{kw.keyword}' - '{kw_clean}' {'매칭!' if is_match else '불일치'}")
        
        if is_match:
            filtered.append(kw)
    
    # 검색량 내림차순으로 정렬
    filtered.sort(key=lambda x: x.search_volume, reverse=True)
    
    logger.info(f"📊 필터링 결과: {len(keywords)}개 중 {len(filtered)}개 매칭")
    
    return filtered


def is_category_match(target_category: str, keyword_category: str) -> bool:
    """
    두 카테고리가 매칭되는지 확인
    
    Args:
        target_category: 1단계 선택 카테고리
        keyword_category: 키워드의 카테고리
        
    Returns:
        bool: 매칭 여부
    """
    if not target_category or not keyword_category:
        return False
    
    # 소문자로 변환하여 대소문자 구분 없이 비교
    target_lower = target_category.lower()
    keyword_lower = keyword_category.lower()
    
    # 정확히 같은 경우
    if target_lower == keyword_lower:
        return True
    
    # 카테고리 경로 분리 (> 기준)
    target_parts = [part.strip() for part in target_lower.split('>') if part.strip()]
    keyword_parts = [part.strip() for part in keyword_lower.split('>') if part.strip()]
    
    if not target_parts or not keyword_parts:
        return False
    
    # 두 카테고리의 최소 길이까지 비교 (전체 깊이 비교)
    min_depth = min(len(target_parts), len(keyword_parts))
    
    for i in range(min_depth):
        # 각 단계에서 일치하지 않으면 False
        if target_parts[i] != keyword_parts[i]:
            return False
    
    # 모든 단계가 일치하면 True
    return True


def normalize_keyword_for_comparison(keyword: str) -> str:
    """
    키워드 정규화 - 중복 체크용 (소문자 변환)
    
    Args:
        keyword: 원본 키워드
        
    Returns:
        str: 중복 체크용 정규화된 키워드 (공백 제거, 소문자 변환)
    """
    if not keyword:
        return ""
    
    # 1. 앞뒤 공백 제거
    cleaned = keyword.strip()
    
    # 2. 내부 공백 제거 (네이버 API는 띄어쓰기 없는 형태로만 인식)
    normalized = cleaned.replace(" ", "")
    
    # 3. 소문자로 변환 (중복 체크용)
    normalized = normalized.lower()
    
    return normalized


def normalize_keyword_for_api(keyword: str) -> str:
    """
    키워드 정규화 - 네이버 API 호출용 (대문자 변환)
    
    Args:
        keyword: 원본 키워드
        
    Returns:
        str: API 호출용 정규화된 키워드 (공백 제거, 대문자 변환)
    """
    if not keyword:
        return ""
    
    # 1. 앞뒤 공백 제거
    cleaned = keyword.strip()
    
    # 2. 내부 공백 제거 (네이버 API는 띄어쓰기 없는 형태로만 인식)
    normalized = cleaned.replace(" ", "")
    
    # 3. 대문자로 변환 (네이버 API 요구사항)
    normalized = normalized.upper()
    
    return normalized


def deduplicate_keywords(keywords: List[str]) -> List[str]:
    """
    키워드 리스트에서 중복 제거
    "강아지간식"과 "강아지 간식"을 같은 키워드로 처리
    
    Args:
        keywords: 원본 키워드 리스트
        
    Returns:
        List[str]: 중복 제거된 키워드 리스트 (원본 형태 유지)
    """
    if not keywords:
        return []
    
    seen_normalized = set()  # 정규화된 키워드 저장용
    unique_keywords = []     # 원본 형태의 키워드 저장용
    keyword_mapping = {}     # 정규화된 키워드 -> 원본 키워드 매핑
    
    for keyword in keywords:
        if not keyword or not keyword.strip():
            continue
            
        normalized = normalize_keyword_for_comparison(keyword)
        
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            # 원본 키워드 형태를 보존 (첫 번째로 나온 형태 사용)
            unique_keywords.append(keyword.strip())
            keyword_mapping[normalized] = keyword.strip()
    
    return unique_keywords


def calculate_keyword_score(keyword_data: KeywordBasicData) -> float:
    """
    키워드 점수 계산 (검색량 기반)
    
    Args:
        keyword_data: 키워드 데이터
        
    Returns:
        float: 키워드 점수 (0-100)
    """
    # 기본 점수는 검색량 기반
    volume_score = min(keyword_data.search_volume / 1000 * 50, 70)  # 최대 70점
    
    # 키워드 길이 보너스 (2-4글자가 적정)
    length_bonus = 0
    length = len(keyword_data.keyword)
    if 2 <= length <= 4:
        length_bonus = 20
    elif length == 5:
        length_bonus = 10
    elif length == 6:
        length_bonus = 5
    
    total_score = volume_score + length_bonus
    return min(total_score, 100.0)