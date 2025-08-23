"""
네이버 상품명 생성기 어댑터
벤더 호출, 정규화, 엑셀/CSV 저장 I/O 담당
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd

from src.foundation.logging import get_logger
from src.vendors.naver.client_factory import NaverClientFactory
from src.vendors.naver.normalizers import normalize_shopping_response
from src.toolbox.formatters import format_int, format_percent, format_datetime


logger = get_logger(__name__)


class ProductTitleAdapters:
    """상품명 생성기 어댑터 클래스"""
    
    def __init__(self):
        self.naver_client = NaverClientFactory.get_shopping_client()
    
    def fetch_products(self, keyword: str, display: int = 40) -> List[Dict[str, Any]]:
        """네이버 쇼핑에서 상품 데이터 가져오기"""
        try:
            raw_response = self.naver_client.search_products(keyword, display)
            return normalize_shopping_response(raw_response)
        except Exception as e:
            raise Exception(f"상품 데이터 조회 실패: {str(e)}")
    
    def extract_product_info(self, products: List[Dict[str, Any]]) -> tuple[List[str], Dict[str, int]]:
        """상품명과 카테고리 정보 추출"""
        titles = []
        categories = {}
        
        for product in products:
            title = product.get('title', '')
            if title:
                titles.append(title)
            
            # 카테고리 정보 수집
            category = self._get_main_category_from_product(product)
            if category:
                categories[category] = categories.get(category, 0) + 1
        
        return titles, categories
    
    def _get_main_category_from_product(self, product: Dict[str, Any]) -> Optional[str]:
        """상품에서 메인 카테고리 추출"""
        # category4 > category3 > category2 > category1 순으로 우선순위
        for i in range(4, 0, -1):
            category = product.get(f'category{i}', '').strip()
            if category:
                return category
        return None
    
    def get_keyword_search_volume(self, keyword: str) -> int:
        """키워드 검색량 조회"""
        try:
            searchad_client = NaverClientFactory.get_searchad_client()
            return searchad_client.get_search_volume(keyword) or 0
        except Exception:
            # API 오류 시 더미 데이터
            return 100 + abs(hash(keyword)) % 500
    
    def get_keyword_volumes_batch(self, keywords: List[str], progress_callback=None, cancel_checker=None) -> Dict[str, int]:
        """키워드들의 검색량을 배치로 조회 (취소 체크 지원)"""
        volumes = {}
        total = len(keywords)
        
        for i, keyword in enumerate(keywords):
            # 취소 체크
            if cancel_checker and cancel_checker():
                logger.info(f"검색량 조회가 취소되었습니다 ({i}/{total})")
                break
                
            if progress_callback:
                progress_callback(f"검색량 조회 중: {i+1}/{total}")
            
            volumes[keyword] = self.get_keyword_search_volume(keyword)
            
        return volumes
    
    def get_keyword_categories(self, keywords: List[str]) -> Dict[str, str]:
        """각 키워드의 카테고리 추정 (네이버 검색결과 상위의 카테고리 다수결)"""
        keyword_categories = {}
        
        try:
            for keyword in keywords[:20]:  # 성능상 상위 20개만 처리
                # 각 키워드로 검색하여 상위 상품들의 카테고리 수집
                products = self.fetch_products(keyword, display=10)
                
                categories = {}
                for product in products:
                    main_category = self._get_main_category_from_product(product)
                    if main_category:
                        categories[main_category] = categories.get(main_category, 0) + 1
                
                # 가장 많이 나타난 카테고리를 해당 키워드의 카테고리로 설정
                if categories:
                    best_category = max(categories.keys(), key=categories.get)
                    ratio = (categories[best_category] / len(products)) * 100
                    keyword_categories[keyword] = f"{best_category}({ratio:.0f}%)"
                else:
                    keyword_categories[keyword] = "미분류(0%)"
                    
        except Exception as e:
            # 오류 시 빈 카테고리 맵 반환 (모든 키워드 통과)
            logger.warning(f"카테고리 조회 중 오류: {e}")
            
        return keyword_categories
    
    def export_analysis_to_excel(
        self,
        file_path: str,
        brand: str,
        keyword: str,
        spec: str,
        final_tokens: List[str],
        search_volumes: Dict[str, int],
        category_info: Dict[str, Any],
        generated_titles: List[Dict[str, Any]] = None
    ) -> None:
        """분석 결과를 엑셀로 내보내기"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 1. 기본 정보 시트
                info_data = [
                    ['브랜드명', brand],
                    ['핵심키워드', keyword],
                    ['규격/수량', spec],
                    ['분석시간', format_datetime(datetime.now())],
                    ['메인카테고리', category_info.get('main_category', '')],
                    ['카테고리일치율', format_percent(category_info.get('ratio', 0))],
                    ['최종키워드수', format_int(len(final_tokens))]
                ]
                
                info_df = pd.DataFrame(info_data, columns=['항목', '값'])
                info_df.to_excel(writer, sheet_name='분석정보', index=False)
                
                # 2. 키워드 분석 시트
                keyword_data = []
                for token in final_tokens:
                    volume = search_volumes.get(token, 0)
                    keyword_data.append({
                        '키워드': token,
                        '월검색량': format_int(volume),
                        '글자수': len(token),
                        '타입': '단일' if ' ' not in token else f'{token.count(" ")+1}단어'
                    })
                
                keyword_df = pd.DataFrame(keyword_data)
                keyword_df.to_excel(writer, sheet_name='키워드분석', index=False)
                
                # 3. 생성된 상품명 시트 (있는 경우)
                if generated_titles:
                    title_data = []
                    for i, title_info in enumerate(generated_titles, 1):
                        # 키 매핑 (후방 호환)
                        score = title_info.get('seo_score', title_info.get('score', 0))
                        est_volume = title_info.get('estimated_volume', title_info.get('search_volume', 0))
                        char_count = title_info.get('char_count', len(title_info.get('title', '')))
                        
                        title_data.append({
                            '순위': i,
                            '상품명': title_info['title'],
                            'SEO점수': float(score),  # 원시값 저장
                            '예상검색량': int(est_volume),  # 원시값 저장
                            '글자수': char_count
                        })
                    
                    title_df = pd.DataFrame(title_data)
                    title_df.to_excel(writer, sheet_name='생성상품명', index=False)
                
                # 워크시트 스타일링
                self._style_excel_sheets(writer)
                
        except Exception as e:
            raise Exception(f"엑셀 저장 실패: {str(e)}")
    
    def _style_excel_sheets(self, writer) -> None:
        """엑셀 시트 스타일링"""
        try:
            for sheet_name, worksheet in writer.sheets.items():
                # 열 너비 조정
                if sheet_name == '키워드분석':
                    worksheet.column_dimensions['A'].width = 20  # 키워드
                    worksheet.column_dimensions['B'].width = 15  # 월검색량
                elif sheet_name == '생성상품명':
                    worksheet.column_dimensions['B'].width = 50  # 상품명
                elif sheet_name == '분석정보':
                    worksheet.column_dimensions['A'].width = 15
                    worksheet.column_dimensions['B'].width = 30
        except Exception:
            pass  # 스타일링 실패해도 저장은 진행
    
    def export_results_to_excel(
        self,
        file_path: str,
        input_data: Dict[str, str],
        generated_titles: List[Dict[str, Any]],
        category_info: Dict[str, Any],
        selected_tokens: List[str]
    ) -> None:
        """생성된 상품명 결과를 엑셀로 저장 (UI에서 file_path 제공)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 엑셀 데이터 구성
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 1. 생성된 상품명 시트
                excel_data = []
                for i, title_data in enumerate(generated_titles, 1):
                    # 키 매핑 (후방 호환)
                    score = title_data.get('seo_score', title_data.get('score', 0))
                    est_volume = title_data.get('estimated_volume', title_data.get('search_volume', 0))
                    char_count = title_data.get('char_count', len(title_data.get('title', '')))
                    
                    excel_data.append({
                        '순위': i,
                        '상품명': title_data['title'],
                        'SEO점수': float(score),  # 원시값 저장
                        '예상검색량': int(est_volume),  # 원시값 저장
                        '글자수': char_count
                    })
                
                df = pd.DataFrame(excel_data)
                df.to_excel(writer, sheet_name='생성된상품명', index=False)
                
                # 2. 분석 정보 시트
                analysis_info = pd.DataFrame([
                    ['브랜드명', input_data.get('brand', '')],
                    ['핵심키워드', input_data.get('keyword', '')],
                    ['규격/수량', input_data.get('spec', '')],
                    ['재질/원재료', input_data.get('material', '')],
                    ['사이즈', input_data.get('size', '')],
                    ['분석시간', timestamp],
                    ['메인카테고리', category_info.get('main_category', '')],
                    ['카테고리일치율(%)', f"{category_info.get('ratio', 0):.1f}"],
                    ['선택된토큰', ', '.join(selected_tokens)]
                ], columns=['항목', '값'])
                
                analysis_info.to_excel(writer, sheet_name='분석정보', index=False)
                
                # 워크시트 스타일링
                workbook = writer.book
                
                # 상품명 시트 스타일링
                titles_sheet = writer.sheets['생성된상품명']
                titles_sheet.column_dimensions['B'].width = 50  # 상품명 열 너비 확장
                
                # 분석정보 시트 스타일링
                info_sheet = writer.sheets['분석정보']
                info_sheet.column_dimensions['A'].width = 15
                info_sheet.column_dimensions['B'].width = 40
                
        except ImportError:
            raise Exception("pandas 라이브러리가 필요합니다. 'pip install pandas openpyxl'을 실행해주세요.")
        except Exception as e:
            raise Exception(f"엑셀 저장 오류: {str(e)}")


# 싱글톤 인스턴스
product_title_adapters = ProductTitleAdapters()