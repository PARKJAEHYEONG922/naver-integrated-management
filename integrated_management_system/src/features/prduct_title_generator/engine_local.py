"""
네이버 상품명 생성기 엔진
점수 계산, 랭킹, 필터/정렬, 통계 요약 - 순수 함수
"""
from typing import List, Dict, Tuple, Optional
import re
from collections import Counter

from .models import GeneratedTitle, KeywordInfo, SEO_WEIGHTS, TITLE_LENGTH_SCORES


def calculate_seo_score(
    title: str,
    brand: str,
    keyword: str,
    selected_tokens: List[str]
) -> float:
    """SEO 점수 계산 (순수 함수)"""
    score = 0.0
    
    # 1. 핵심 키워드 포함 (30점)
    if keyword.lower() in title.lower():
        score += SEO_WEIGHTS['keyword_inclusion']
    
    # 2. 선택된 토큰 포함도 (25점)
    if selected_tokens:
        included_tokens = sum(1 for token in selected_tokens if token in title)
        coverage_ratio = included_tokens / len(selected_tokens)
        score += coverage_ratio * SEO_WEIGHTS['token_coverage']
    
    # 3. 제목 길이 최적화 (20점)
    length_score = calculate_length_score(len(title))
    score += length_score
    
    # 4. 브랜드명 포함 (15점)
    if brand and brand in title:
        score += SEO_WEIGHTS['brand_inclusion']
    
    # 5. 읽기 쉬운 구조 (10점)
    readability_score = calculate_readability_score(title)
    score += readability_score
    
    # 6. 부적절한 키워드 감점
    penalty = calculate_penalty_score(title)
    score -= penalty
    
    return max(min(score, 100.0), 0.0)


def calculate_length_score(title_length: int) -> float:
    """제목 길이 기반 점수 계산 (우선순위 고정)"""
    # 우선순위: optimal → good → acceptable
    tiers = [
        TITLE_LENGTH_SCORES['optimal'],
        TITLE_LENGTH_SCORES['good'],
        TITLE_LENGTH_SCORES['acceptable'],
    ]
    
    for min_len, max_len, score_val in tiers:
        if min_len <= title_length <= max_len:
            return score_val
    
    return 0.0


def calculate_readability_score(title: str) -> float:
    """읽기 쉬운 구조 점수 계산"""
    words = title.split()
    word_count = len(words)
    
    if 4 <= word_count <= 8:
        return SEO_WEIGHTS['readability']
    elif 3 <= word_count <= 10:
        return SEO_WEIGHTS['readability'] * 0.5
    return 0.0


def calculate_penalty_score(title: str) -> float:
    """부적절한 키워드 감점 계산 (대소문자 무관, 상한 적용)"""
    penalty_keywords = [
        # 구매 유도성 키워드
        '베스트', '인기', '추천', '후기', '할인', '특가', '세일', '이벤트',
        '무료배송', '빠른배송', '당일배송',
        # 주관적 수식어
        '예쁜', '멋진', '이쁜', '귀여운', '좋은', '최고', '완벽한',
        '아름다운', '매력적인', '사랑스러운',
        # 과장된 광고성 표현
        '프리미엄', '럭셔리', '고급', '최상급', '최고급', '명품',
        '특별한', '독특한', '유일한'
    ]
    
    title_lower = title.lower()
    penalty_count = sum(1 for keyword in penalty_keywords if keyword.lower() in title_lower)
    
    # 키워드당 20점 감점, 최대 40점 상한
    return min(penalty_count * 20.0, 40.0)


def estimate_search_volume(title: str, search_volumes: Dict[str, int]) -> int:
    """제목의 예상 검색량 계산 (이중 집계 방지)"""
    title_lower = title.lower()
    
    # 1) 구문(공백 포함) 키워드 우선 집계
    phrase_hits = {k for k in search_volumes if " " in k and k.lower() in title_lower}
    total_volume = sum(search_volumes[k] for k in phrase_hits)
    
    # 2) 구문에 포함된 단일 토큰들 수집 (중복 방지용)
    used_tokens = set()
    for phrase in phrase_hits:
        used_tokens.update(phrase.lower().split())
    
    # 3) 단일 토큰 집계 (구문에 포함된 토큰은 제외)
    for token, volume in search_volumes.items():
        if " " in token:  # 구문은 이미 처리됨
            continue
        if token.lower() in title_lower and token.lower() not in used_tokens:
            total_volume += volume
    
    return total_volume


def generate_title_variations(
    brand: str,
    keyword: str,
    spec: str,
    selected_tokens: List[str]
) -> List[str]:
    """상품명 변형 생성"""
    if not selected_tokens:
        return [f"{brand} {keyword} {spec}"]
    
    # 기본 조합들 (스페이스 버그 수정)
    base_combinations = [
        f"{brand} {' '.join(selected_tokens[:3])} {spec}",
        f"{brand} {selected_tokens[0]} {' '.join(selected_tokens[1:4])} {spec}",
        f"{brand} {' '.join(selected_tokens[:2])} {' '.join(selected_tokens[2:4])} {spec}",  # 공백 수정
    ]
    
    # 객관적 특성 키워드 추가 버전
    objective_modifiers = ["천연", "무첨가", "수제", "건식", "유기농"]
    variations = list(base_combinations)
    
    for i, base_title in enumerate(base_combinations[:3]):
        if i < len(objective_modifiers):
            modified_title = f"{objective_modifiers[i]} {base_title}"
            variations.append(modified_title)
    
    # 길이 제한/정규화/중복 제거 (모든 변형에 적용)
    MAX_LENGTH = 50
    seen = set()
    final_variations = []
    
    for variation in variations:
        # 공백 정규화
        normalized = re.sub(r"\\s+", " ", variation).strip()
        
        # 길이 제한 및 중복 제거
        if len(normalized) <= MAX_LENGTH and normalized not in seen:
            seen.add(normalized)
            final_variations.append(normalized)
    
    return final_variations


def rank_generated_titles(
    titles: List[str],
    brand: str,
    keyword: str,
    selected_tokens: List[str],
    search_volumes: Dict[str, int]
) -> List[GeneratedTitle]:
    """생성된 상품명들을 점수순으로 랭킹"""
    ranked_titles = []
    
    for title in titles:
        seo_score = calculate_seo_score(title, brand, keyword, selected_tokens)
        estimated_volume = estimate_search_volume(title, search_volumes)
        
        # 사용된 키워드들 추출
        keywords_used = extract_keywords_from_title(title, selected_tokens)
        
        generated_title = GeneratedTitle(
            title=title,
            seo_score=seo_score,
            estimated_volume=estimated_volume,
            keywords_used=keywords_used
        )
        
        ranked_titles.append(generated_title)
    
    # SEO 점수순으로 정렬
    ranked_titles.sort(key=lambda x: x.seo_score, reverse=True)
    
    return ranked_titles


def extract_keywords_from_title(title: str, available_tokens: List[str]) -> List[str]:
    """제목에서 사용된 키워드들 추출"""
    used_keywords = []
    title_lower = title.lower()
    
    for token in available_tokens:
        if token.lower() in title_lower:
            used_keywords.append(token)
    
    return used_keywords


def filter_keywords_by_volume(
    keywords: List[str],
    search_volumes: Dict[str, int],
    min_volume: int = 100
) -> List[str]:
    """검색량 기준으로 키워드 필터링"""
    return [
        keyword for keyword in keywords
        if search_volumes.get(keyword, 0) >= min_volume
    ]


def filter_keywords_by_category(
    keywords: List[str],
    keyword_categories: Dict[str, str],
    target_category: str,
    min_match_rate: float = 0.4
) -> List[str]:
    """카테고리 일치성 기준으로 키워드 필터링 (맵 없으면 통과)"""
    # 카테고리 맵이 비어있거나 타겟 카테고리가 없으면 패스-스루
    if not keyword_categories or not target_category:
        return keywords[:]
    
    filtered_keywords = []
    for keyword in keywords:
        keyword_category = keyword_categories.get(keyword, "")
        if is_category_match(keyword_category, target_category, min_match_rate):
            filtered_keywords.append(keyword)
    
    return filtered_keywords


def is_category_match(
    keyword_category: str,
    target_category: str,
    min_match_rate: float = 0.4
) -> bool:
    """카테고리 일치 여부 확인"""
    if not keyword_category or not target_category:
        return False
    
    # 일치율 추출
    match_rate = extract_category_match_rate(keyword_category)
    if match_rate < min_match_rate:
        return False
    
    # 카테고리명 일치 확인
    return is_category_name_match(keyword_category, target_category)


def extract_category_match_rate(category_info: str) -> float:
    """카테고리 정보에서 일치율 추출"""
    if '(' in category_info and '%' in category_info:
        try:
            percentage_str = category_info.split('(')[1].split('%')[0]
            return float(percentage_str) / 100.0
        except (IndexError, ValueError):
            return 0.0
    return 0.0


def is_category_name_match(keyword_category: str, target_category: str) -> bool:
    """카테고리명 일치 여부 확인"""
    if '(' in keyword_category:
        category_path = keyword_category.split('(')[0].strip()
    else:
        category_path = keyword_category.strip()
    
    target_lower = target_category.lower()
    category_lower = category_path.lower()
    
    # 완전 일치 또는 포함 관계 확인
    return (
        target_lower == category_lower or
        target_lower in category_lower or
        category_lower in target_lower or
        # 카테고리 경로의 마지막 부분과 비교
        (category_lower.split(' > ')[-1] == target_lower if ' > ' in category_lower else False)
    )


def analyze_keyword_distribution(keywords: List[str]) -> Dict[str, int]:
    """키워드 분포 분석"""
    distribution = {
        'single_words': 0,
        'two_words': 0,
        'three_words': 0,
        'four_plus_words': 0
    }
    
    for keyword in keywords:
        word_count = keyword.count(' ') + 1
        
        if word_count == 1:
            distribution['single_words'] += 1
        elif word_count == 2:
            distribution['two_words'] += 1
        elif word_count == 3:
            distribution['three_words'] += 1
        else:
            distribution['four_plus_words'] += 1
    
    return distribution


def calculate_keyword_statistics(
    keywords: List[str],
    search_volumes: Dict[str, int]
) -> Dict[str, float]:
    """키워드 통계 계산"""
    if not keywords:
        return {
            'total_count': 0,
            'avg_volume': 0.0,
            'max_volume': 0,
            'min_volume': 0,
            'total_volume': 0
        }
    
    volumes = [search_volumes.get(keyword, 0) for keyword in keywords]
    
    return {
        'total_count': len(keywords),
        'avg_volume': sum(volumes) / len(volumes),
        'max_volume': max(volumes),
        'min_volume': min(volumes),
        'total_volume': sum(volumes)
    }


def calculate_category_statistics(categories: Dict[str, int], total_count: int) -> tuple[str, float]:
    """카테고리 통계 계산 - 메인 카테고리와 비율 반환"""
    if not categories or total_count == 0:
        return "", 0.0
    
    # 가장 많이 나타난 카테고리 찾기
    main_category = max(categories.keys(), key=categories.get)
    
    # 해당 카테고리의 비율 계산
    category_ratio = (categories.get(main_category, 0) / total_count) * 100
    
    return main_category, category_ratio


def extract_candidate_keywords(
    titles: List[str],
    brand: str,
    spec: str,
    main_category: str
) -> List[str]:
    """AI를 통한 키워드 후보 추출 (service에서 이관)"""
    all_keywords = set()
    
    # 1. 제목에서 키워드 추출
    for title in titles:
        # HTML 태그 정리
        clean_title = clean_html_text(title)
        
        # 브랜드명과 스펙 제거 후 토큰화
        words = clean_title.replace(brand, '').replace(spec, '').split()
        words = [w.strip('.,!?()[]') for w in words if len(w) > 1]
        all_keywords.update(words)
    
    # 2. 빈도 기반 필터링
    keyword_counts = {}
    for title in titles:
        clean_title = clean_html_text(title)
        for keyword in all_keywords:
            if keyword in clean_title:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
    
    # 3. 후보 키워드 선별 (2회 이상 등장, 길이 제한)
    candidate_keywords = [
        k for k, count in keyword_counts.items() 
        if count >= 2 and 1 < len(k) <= 10
    ]
    
    # 4. 빈도순 정렬 후 상위 50개 반환
    sorted_keywords = sorted(
        candidate_keywords, 
        key=lambda k: keyword_counts[k], 
        reverse=True
    )
    
    return sorted_keywords[:50]


def clean_html_text(text: str) -> str:
    """HTML 태그 및 엔티티 정리"""
    # HTML 태그 제거
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # HTML 엔티티 디코딩
    html_entities = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'"
    }
    
    for entity, char in html_entities.items():
        clean_text = clean_text.replace(entity, char)
    
    return clean_text.strip()