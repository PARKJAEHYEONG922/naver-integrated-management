"""
네이버 상품명 생성기 워커
장시간 작업/취소/진행률 (QThread/시그널)
"""
from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any

from .service import product_title_service


class AnalysisWorker(QThread):
    """분석 워커 스레드"""
    
    # 시그널 정의
    progress_updated = Signal(int, str)  # (진행률, 상태메시지)
    analysis_completed = Signal(object)  # AnalysisResult 객체
    error_occurred = Signal(str)
    
    def __init__(self, brand: str, keyword: str, spec: str):
        super().__init__()
        self.brand = brand
        self.keyword = keyword
        self.spec = spec
        self.is_cancelled = False
    
    def run(self):
        """워커 실행"""
        try:
            # 진행률 콜백 함수
            def progress_callback(progress: int, message: str):
                if self.is_cancelled:
                    return False
                self.progress_updated.emit(progress, message)
                return True
            
            # 서비스를 통해 분석 실행
            result = product_title_service.analyze_products(
                self.brand,
                self.keyword,
                self.spec,
                progress_callback
            )
            
            if not self.is_cancelled:
                self.analysis_completed.emit(result)
                
        except Exception as e:
            if not self.is_cancelled:
                self.error_occurred.emit(f"분석 중 오류 발생: {str(e)}")
    
    def cancel(self):
        """작업 취소"""
        self.is_cancelled = True


class TitleGenerationWorker(QThread):
    """상품명 생성 워커"""
    
    # 시그널 정의
    titles_generated = Signal(list)  # GeneratedTitle 리스트
    progress_updated = Signal(int, str)
    error_occurred = Signal(str)
    
    def __init__(self, brand: str, keyword: str, spec: str, selected_tokens: List[str], search_volumes: Dict[str, int]):
        super().__init__()
        self.brand = brand
        self.keyword = keyword
        self.spec = spec
        self.selected_tokens = selected_tokens
        self.search_volumes = search_volumes
        self.is_cancelled = False
    
    def run(self):
        """상품명 생성 실행"""
        try:
            self.progress_updated.emit(10, f"🎨 선택된 {len(self.selected_tokens)}개 키워드로 상품명 생성 중...")
            
            # 서비스를 통해 상품명 생성
            generated_titles = product_title_service.generate_titles(
                self.brand,
                self.keyword,
                self.spec,
                self.selected_tokens,
                self.search_volumes
            )
            
            self.progress_updated.emit(60, "⚙️ 점수 계산 및 랭킹 정렬 중...")
            self.progress_updated.emit(100, f"🎉 {len(generated_titles)}개 상품명 생성 완료!")
            
            if not self.is_cancelled:
                self.titles_generated.emit(generated_titles)
                
        except Exception as e:
            if not self.is_cancelled:
                self.error_occurred.emit(f"상품명 생성 중 오류: {str(e)}")
    
    def cancel(self):
        """작업 취소"""
        self.is_cancelled = True