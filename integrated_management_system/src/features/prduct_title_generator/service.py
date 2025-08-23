"""
네이버 상품명 생성기 서비스
오케스트레이션: 입력 검증 → adapters → engine_local → DB/엑셀 트리거
"""
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.foundation.logging import get_logger
from src.toolbox.text_utils import validate_keyword
from .adapters import ProductTitleAdapters
from .models import (
    ProductTitleRepository, AnalysisResult, AnalysisStatus,
    GeneratedTitle, DEFAULT_SEARCH_VOLUME_THRESHOLD, TOP_N_TITLES
)
from .engine_local import (
    rank_generated_titles, generate_title_variations,
    filter_keywords_by_volume, filter_keywords_by_category,
    extract_candidate_keywords, calculate_category_statistics
)

logger = get_logger(__name__)


class ProductTitleService:
    """네이버 상품명 생성기 서비스"""
    
    def __init__(self):
        self.adapters = ProductTitleAdapters()
        self.repository = ProductTitleRepository()
    
    def validate_inputs(self, brand: str, keyword: str, spec: str) -> None:
        """입력값 검증 (핵심제품명만 필수)"""
        # 핵심제품명만 필수
        if not keyword.strip():
            raise ValueError("핵심제품명을 입력해주세요")
        
        # 여러 키워드 검증
        keywords = [k.strip() for k in keyword.split(',') if k.strip()]
        if not keywords:
            raise ValueError("올바른 핵심제품명을 입력해주세요")
        
        for kw in keywords:
            if not validate_keyword(kw):
                raise ValueError(f"올바르지 않은 키워드가 있습니다: {kw}")
        
        logger.info(f"입력값 검증 완료: brand={brand or '미설정'}, keywords={keywords}, spec={spec or '미설정'}")
    
    def analyze_products(
        self,
        brand: str,
        keyword: str,
        spec: str,
        progress_callback=None
    ) -> AnalysisResult:
        """상품 분석 실행"""
        try:
            # 취소 체크 헬퍼 함수
            def _emit_progress(progress: int, message: str) -> None:
                if progress_callback and progress_callback(progress, message) is False:
                    raise RuntimeError("분석이 취소되었습니다")
            
            # 1. 입력값 검증
            self.validate_inputs(brand, keyword, spec)
            
            _emit_progress(10, "📊 네이버 쇼핑에서 상품 데이터 수집 중...")
            
            # 2. 여러 키워드로 상품 데이터 수집
            keywords = [k.strip() for k in keyword.split(',') if k.strip()]
            all_titles = []
            all_categories = {}
            
            for i, kw in enumerate(keywords):
                _emit_progress(10 + (i * 15) // len(keywords), f"📊 '{kw}' 상품 검색 중...")
                products = self.adapters.fetch_products(kw)
                titles, categories = self.adapters.extract_product_info(products)
                all_titles.extend(titles)
                
                # 카테고리 합계 계산
                for cat, count in categories.items():
                    all_categories[cat] = all_categories.get(cat, 0) + count
            
            if not all_titles:
                raise Exception("검색 결과가 없습니다")
            
            _emit_progress(30, f"✅ {len(all_titles)}개 상품 분석 완료 (키워드 {len(keywords)}개)")
            
            # 3. engine_local을 통해 카테고리 통계 계산
            main_category, category_ratio = calculate_category_statistics(all_categories, len(all_titles))
            
            _emit_progress(50, "🤖 AI 키워드 추출 중...")
            
            # 4. engine_local을 통해 키워드 후보 추출
            ai_keywords = extract_candidate_keywords(
                titles=all_titles,
                brand=brand or "",  # 브랜드가 없을 수 있음
                spec=spec or "",    # 스펙이 없을 수 있음
                main_category=main_category
            )
            
            _emit_progress(70, "🔍 검색량 조회 중...")
            
            # 5. adapters를 통해 검색량 조회 (취소 체크 포함)
            search_volumes = self.adapters.get_keyword_volumes_batch(
                ai_keywords,
                progress_callback=lambda msg: _emit_progress(75, msg),
                cancel_checker=lambda: progress_callback and progress_callback(0, "") is False if progress_callback else False
            )
            
            # 6. engine_local을 통해 필터링 (검색량)
            filtered_by_volume = filter_keywords_by_volume(
                ai_keywords, 
                search_volumes, 
                DEFAULT_SEARCH_VOLUME_THRESHOLD
            )
            
            _emit_progress(90, "📂 카테고리 일치성 검사 중...")
            
            # 7. 카테고리 일치 필터 실제 적용
            keyword_categories = self.adapters.get_keyword_categories(filtered_by_volume)
            filtered_keywords = filter_keywords_by_category(
                keywords=filtered_by_volume,
                keyword_categories=keyword_categories,
                target_category=main_category,
                min_match_rate=0.4
            )
            
            # 8. 최종 결과 구성
            analysis_result = AnalysisResult(
                brand=brand,
                keyword=keyword,
                spec=spec,
                main_category=main_category,
                category_ratio=category_ratio,
                final_tokens=filtered_keywords,
                search_volumes={k: search_volumes[k] for k in filtered_keywords},
                status=AnalysisStatus.COMPLETED,
                created_at=datetime.now().isoformat()
            )
            
            # 9. DB 저장
            analysis_id = self.repository.save_analysis_result(analysis_result)
            
            _emit_progress(100, "✅ 분석 완료!")
            
            logger.info(f"분석 완료: {analysis_id}, 키워드 {len(filtered_keywords)}개")
            return analysis_result
            
        except Exception as e:
            logger.error(f"분석 실패: {str(e)}")
            
            # 실패 상태로 최소 레코드 저장 (선택적)
            try:
                failed_result = AnalysisResult(
                    brand=brand,
                    keyword=keyword,
                    spec=spec,
                    main_category="",
                    category_ratio=0.0,
                    final_tokens=[],
                    search_volumes={},
                    status=AnalysisStatus.FAILED,
                    created_at=datetime.now().isoformat()
                )
                self.repository.save_analysis_result(failed_result)
                logger.info("실패 상태 레코드 저장 완료")
            except Exception as save_error:
                logger.warning(f"실패 상태 저장 중 오류: {save_error}")
            
            raise
    
    def generate_titles(
        self,
        brand: str,
        keyword: str,
        spec: str,
        selected_tokens: List[str],
        search_volumes: Dict[str, int],
        analysis_id: Optional[int] = None
    ) -> List[GeneratedTitle]:
        """상품명 생성"""
        try:
            logger.info(f"상품명 생성 시작: {len(selected_tokens)}개 키워드")
            
            # 1. engine_local을 통해 제목 변형 생성
            title_variations = generate_title_variations(
                brand, keyword, spec, selected_tokens
            )
            
            # 2. engine_local을 통해 점수 계산 및 랭킹
            ranked_titles = rank_generated_titles(
                title_variations,
                brand,
                keyword,
                selected_tokens,
                search_volumes
            )
            
            # 상위 N개만 반환
            final_titles = ranked_titles[:TOP_N_TITLES]
            
            # DB 저장 (analysis_id가 제공된 경우)
            if analysis_id is not None:
                self.repository.save_generated_titles(analysis_id, final_titles)
                logger.info(f"생성된 상품명 DB 저장 완료: analysis_id={analysis_id}")
            
            logger.info(f"상품명 생성 완료: {len(final_titles)}개")
            return final_titles
            
        except Exception as e:
            logger.error(f"상품명 생성 실패: {str(e)}")
            raise
    
    def export_results(
        self,
        file_path: str,
        analysis_result: AnalysisResult,
        generated_titles: List[GeneratedTitle] = None
    ) -> None:
        """결과를 엑셀로 내보내기"""
        try:
            # GeneratedTitle 직렬화 (property 포함)
            title_data = None
            if generated_titles:
                title_data = [
                    {
                        "title": title.title,
                        "seo_score": title.seo_score,
                        "estimated_volume": title.estimated_volume,
                        "char_count": title.char_count,  # property 보존
                        "keywords_used": ",".join(title.keywords_used or [])
                    } for title in generated_titles
                ]
            
            self.adapters.export_analysis_to_excel(
                file_path,
                analysis_result.brand,
                analysis_result.keyword,
                analysis_result.spec,
                analysis_result.final_tokens,
                analysis_result.search_volumes,
                {
                    'main_category': analysis_result.main_category,
                    'ratio': analysis_result.category_ratio
                },
                title_data
            )
            
            logger.info(f"엑셀 내보내기 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"엑셀 내보내기 실패: {str(e)}")
            raise
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 분석 이력 조회"""
        return self.repository.get_recent_analyses(limit)
    
    def get_analysis_detail(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """분석 상세 정보 조회"""
        return self.repository.get_analysis_detail(analysis_id)
    


# 서비스 인스턴스
product_title_service = ProductTitleService()