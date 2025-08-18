"""
PowerLink 분석기 텍스트 처리 함수들
키워드 파싱, 정규화 등 텍스트 관련 작업 처리
"""
from typing import List


def parse_keywords_from_text(text: str) -> List[str]:
    """텍스트에서 키워드 목록 파싱 (엔터, 쉼표 구분 지원)"""
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
    
    return keywords


def process_keywords(keywords: List[str], existing_keywords: set = None) -> List[str]:
    """키워드 전처리 (공백 제거, 대문자 변환, 중복 제거)"""
    if existing_keywords is None:
        existing_keywords = set()
        
    unique_keywords = []
    seen = set()
    
    for keyword in keywords:
        # 전처리: 공백 제거, 대문자 변환
        processed = keyword.strip().replace(' ', '').upper()
        
        if processed and processed not in seen and processed not in existing_keywords:
            unique_keywords.append(processed)
            seen.add(processed)
    
    return unique_keywords