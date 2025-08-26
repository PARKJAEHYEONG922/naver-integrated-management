"""
네이버 상품명 생성기 모듈
"""
from .models import (
    AnalysisStep, ProductInput, KeywordBasicData, 
    AIAnalysisResult, GeneratedTitle, SessionData
)
from .service import product_title_service
from .ui_main import NaverProductTitleGeneratorWidget

def register(app):
    """네이버 상품명 생성기 모듈을 앱에 등록"""
    widget = NaverProductTitleGeneratorWidget()
    app.add_feature_tab(widget, "네이버 상품명 생성기")

__all__ = [
    'AnalysisStep',
    'ProductInput', 
    'KeywordBasicData',
    'AIAnalysisResult',
    'GeneratedTitle',
    'SessionData',
    'product_title_service',
    'NaverProductTitleGeneratorWidget',
    'register'
]