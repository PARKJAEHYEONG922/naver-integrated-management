"""
네이버 PowerLink 광고비 분석기 메인 UI 
컨트롤 위젯과 결과 위젯을 조합하는 컨테이너 역할
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from .control_widget import PowerLinkControlWidget
from .results_widget import PowerLinkResultsWidget


class PowerLinkAnalyzerWidget(QWidget):
    """PowerLink 광고비 분석기 메인 UI 컨테이너"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        
    def closeEvent(self, event):
        """위젯 종료 시 리소스 정리"""
        # 컨트롤 위젯의 리소스 정리 위임
        if hasattr(self, 'control_widget'):
            self.control_widget.closeEvent(event)
        super().closeEvent(event)
        
    def setup_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 헤더 섹션 (제목 + 사용법)
        self.setup_header(main_layout)
        
        # 컨텐츠 레이아웃 (좌측 패널 + 우측 패널)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # 좌측 패널 (컨트롤 위젯)
        self.control_widget = PowerLinkControlWidget()
        self.control_widget.setFixedWidth(350)
        
        # 우측 패널 (결과 위젯)
        self.results_widget = PowerLinkResultsWidget()
        
        content_layout.addWidget(self.control_widget)
        content_layout.addWidget(self.results_widget, 1)
        
        main_layout.addLayout(content_layout)
        
    def setup_header(self, layout):
        """헤더 섹션 (제목 + 사용법)"""
        header_layout = QHBoxLayout()
        
        # 제목
        title_label = QLabel("💰 파워링크 광고비")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 버튼
        self.help_button = QPushButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        self.help_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_secondary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                margin-left: 10px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        
        header_layout.addWidget(self.help_button)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
    
    def show_help_dialog(self):
        """사용법 다이얼로그 표시"""
        help_text = (
            "📋 키워드 입력:\n"
            "• 분석할 키워드를 입력해주세요 (엔터로 구분)\n"
            "• 같은 업종/카테고리 키워드를 함께 분석하면 정확한 순위 비교 가능\n\n"
            "📊 분석 결과 설명:\n"
            "• 월검색량: 네이버에서 월 평균 검색되는 횟수\n"
            "• 월평균클릭수: 파워링크 1~15위 광고들의 월 평균 클릭수\n"
            "• 클릭률: 파워링크 1~15위 광고들의 월 평균 클릭률 (%)\n"
            "• 1p노출위치: 실제 1페이지에 노출되는 광고 개수 (위까지)\n"
            "• 1등광고비: 1위 노출을 위한 예상 입찰가 (원)\n"
            "• 최소노출가격: 1페이지 노출을 위한 최소 입찰가 (원)\n"
            "• 추천순위: 비용 대비 효율성 기준 상대적 순위\n\n"
            "🏆 추천순위 계산 공식 (하이브리드 방식):\n\n"
            "📊 두 가지 관점으로 효율성 측정:\n"
            "• 현실성 점수 = 월평균클릭수 ÷ 최소노출가격\n"
            "  → 네이버 데이터 기반 실제 예상 성과 (원당 클릭수)\n\n"
            "• 잠재력 점수 = (월검색량 × 클릭률 ÷ 100) ÷ 최소노출가격\n"
            "  → 순수 수요와 반응성 기반 이론적 잠재력\n\n"
            "🎯 최종 점수 = 현실성 70% + 잠재력 30%\n"
            "• 실제 성과 가능성과 전략적 잠재력을 균형있게 반영\n"
            "• 점수가 높을수록 비용 대비 효율이 좋은 키워드\n"
            "• 동점시: 월검색량↑ → 최소노출가격↓ → 키워드명 순\n\n"
            "💡 사용 팁:\n"
            "• PC/모바일 탭을 구분해서 플랫폼별 분석\n"
            "• 추천순위 상위 키워드 우선 검토 (투자 효율 높음)\n"
            "• 월검색량 높고 최소노출가격 낮은 키워드가 유리\n"
            "• 체크박스로 불필요한 키워드 삭제 가능\n"
            "• 클리어 버튼으로 새로운 키워드 그룹 분석\n"
            "• 상세 버튼으로 1~15위별 입찰가 확인 가능"
        )
        
        dialog = ModernConfirmDialog(
            self, "파워링크 광고비 사용법", help_text, 
            confirm_text="확인", cancel_text=None, icon="💡"
        )
        dialog.exec()
    
    def setup_connections(self):
        """시그널 연결"""
        # 컨트롤 위젯의 시그널을 결과 위젯으로 연결
        self.control_widget.analysis_completed.connect(self.on_analysis_completed)
        self.control_widget.analysis_error.connect(self.on_analysis_error)
        self.control_widget.keywords_data_cleared.connect(self.on_keywords_data_cleared)
        
        # 키워드 즉시 추가 시그널 연결
        self.control_widget.keyword_added_immediately.connect(self.results_widget.add_keyword_immediately)
        
        # 모든 순위 계산 완료 시그널 연결
        self.control_widget.all_rankings_updated.connect(self.results_widget.update_all_tables)
        
        # 분석 상태 시그널 연결 (저장 버튼 제어용)
        self.control_widget.analysis_started.connect(self.results_widget.on_analysis_started)
        self.control_widget.analysis_finished.connect(self.results_widget.on_analysis_finished)
    
    def on_analysis_completed(self, results):
        """분석 완료 시 결과 위젯 업데이트"""
        # 결과 위젯에 키워드 데이터 전달하여 테이블 업데이트
        self.results_widget.set_keywords_data(results)
    
    def on_analysis_error(self, error_msg):
        """분석 오류 처리"""
        # 필요 시 추가 처리
        pass
    
    def on_keywords_data_cleared(self):
        """키워드 데이터 클리어 시 결과 위젯 테이블 클리어"""
        # Use the available method or create a direct clear
        if hasattr(self.results_widget, 'clear_all_tables'):
            self.results_widget.clear_all_tables()
        else:
            # Fallback: clear tables directly
            self.results_widget.mobile_table.setRowCount(0)
            self.results_widget.pc_table.setRowCount(0)
            self.results_widget.update_save_button_state()